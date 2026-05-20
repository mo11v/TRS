"""
TRS MTT PDF Parser
Supports both:
  - pdftotext -layout (Linux/Mac): single-line per joint
  - pypdf (Windows fallback): multi-line per joint
"""
import re, json, subprocess, io, logging
from datetime import datetime

logger = logging.getLogger(__name__)

# pdftotext -layout: "    1                     11573      1.561 ..."
JOINT_RE_LAYOUT = re.compile(
    r'^\s{2,12}(\d{1,3}(?:_R\d+)?)\s{4,}(\d{4,6})\s+([\d.]+)\s+(-|[\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)'
)
# pypdf: "1 2026-03-19" then next line "02:38:14 11573 1.561 - 2946 ..."
JOINT_RE_PYPDF  = re.compile(r'^(\d{1,3}(?:_R\d+)?)\s+(\d{4}-\d{2}-\d{2})$')
DATA_RE_PYPDF   = re.compile(r'^(\d{2}:\d{2}:\d{2})\s+(\d{4,6})\s+([\d.]+)\s+(-|[\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)')
DATE_RE = re.compile(r'(\d{4}-\d{2}-\d{2})')
TIME_RE = re.compile(r'(\d{2}:\d{2}:\d{2})')


def _get_int(pattern, text):
    m = re.search(pattern, text)
    return int(m.group(1)) if m else None


def extract_text_pdftotext(content: bytes) -> str | None:
    """Try pdftotext -layout (best quality, needs poppler installed)"""
    try:
        r = subprocess.run(
            ['pdftotext', '-layout', '-', '-'],
            input=content, capture_output=True, timeout=60
        )
        if r.returncode == 0 and r.stdout:
            return r.stdout.decode('utf-8', errors='replace')
    except Exception:
        pass
    return None


def extract_text_pypdf(content: bytes) -> str | None:
    """Fallback: pypdf (works on Windows without poppler)"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        pages = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
        return '\n'.join(pages) if pages else None
    except Exception as e:
        logger.error(f"pypdf failed: {e}")
        return None


def detect_mtt(text: str) -> bool:
    return any(k in text for k in [
        'MTT Report', 'MTT 3.', 'Tong Name/Model',
        'Final\nTorque', 'Shoulder\nTurns', 'Delta\nTorque'
    ])


def parse_header(lines: list, full_text: str) -> dict:
    h = {
        'job_name': '', 'pipe_type': '', 'lot_names': [],
        'tong_model': '', 'tong_arm': None, 'ppt': None,
        'start_datetime': '', 'end_datetime': '',
        'load_cell_serial': '',
        'max_torque': None, 'opt_torque': None, 'min_torque': None,
        'high_shoulder': None, 'low_shoulder': None,
    }
    search_text = '\n'.join(lines[:1500]) if lines else full_text[:8000]
    # Specs may be on joint pages (not just header) — search entire text
    spec_text = full_text

    m = re.search(r'Job#?([\w\-\s#/]+?)(?:\n|Admin)', search_text)
    if m:
        h['job_name'] = m.group(1).strip()

    lots = re.findall(r'Lot #\d+:\s*(.+?)(?:\n|$)', search_text)
    h['lot_names'] = [l.strip() for l in lots]
    if lots:
        h['pipe_type'] = lots[0].strip()

    # Support both formats:
    # Format A (per-page table): "Maximum Torque\n11390"
    # Format B (inline):         "Maximum Torque 3190 Reference Torque 0..."
    h['max_torque']    = _get_int(r'Maximum Torque[\s:]+([0-9]+)', spec_text)
    h['opt_torque']    = _get_int(r'Optimum Torque[\s:]+([0-9]+)', spec_text)
    h['min_torque']    = _get_int(r'Minimum Torque[\s:]+([0-9]+)', spec_text)
    h['high_shoulder'] = _get_int(r'High Shoulder Torque[\s:]+([0-9]+)', spec_text)
    h['low_shoulder']  = _get_int(r'Low Shoulder Torque[\s:]+([0-9]+)', spec_text)

    for i, line in enumerate(lines[:150]):
        l = line.strip()
        def nxt():
            return [lines[j].strip() for j in range(i+1, min(i+6, len(lines))) if lines[j].strip()]
        if 'Tong Name/Model' in l:
            v = nxt(); h['tong_model'] = v[0] if v else ''
        elif 'Tong Arm' in l:
            v = nxt()
            try: h['tong_arm'] = float(v[0]) if v else None
            except: pass
        elif 'Pulses Per Turn' in l:
            v = nxt()
            try: h['ppt'] = int(v[0]) if v else None
            except: pass

    return h


def parse_joints_layout(lines: list) -> list:
    """Parse from pdftotext -layout output (wide spaced columns)"""
    joints = []
    lot_name = 'Lot 1'
    for i, line in enumerate(lines):
        lot_m = re.match(r'\s*(Lot #\d+:\s*.+)', line)
        if lot_m:
            lot_name = lot_m.group(1).strip()
            continue
        m = JOINT_RE_LAYOUT.match(line)
        if not m:
            continue
        date_str = time_str = ''
        for back in range(1, 6):
            if i - back < 0: break
            dm = DATE_RE.search(lines[i - back])
            if dm: date_str = dm.group(1); break
        for fwd in range(1, 4):
            if i + fwd >= len(lines): break
            tm = TIME_RE.search(lines[i + fwd])
            if tm: time_str = tm.group(1); break
        j_status = 'OK'
        for bk in range(1, 25):
            if i - bk < 0: break
            bl = lines[i - bk].strip()
            if 'ACCEPTED' in bl: j_status = 'ACCEPTED'; break
            if 'REJECTED' in bl: j_status = 'REJECTED'; break
        g = m.groups()
        jlabel = g[0].strip()
        dt_str = f"{date_str} {time_str}".strip()
        try: dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S').isoformat()
        except: dt = dt_str
        joints.append(_make_joint(jlabel, dt, lot_name, j_status, g[1], g[2], g[4], g[5], g[6], g[7], g[8]))
    return joints


def parse_joints_pypdf(lines: list) -> list:
    """
    Parse from pypdf output.
    Pattern per joint (2 lines):
      Line A: "1 2026-03-19"         (joint_num + date)
      Line B: "02:38:14 11573 1.561 - 2946 1.499 3.6 8627 0.062 -"
    """
    joints = []
    lot_name = 'Lot 1'
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        lot_m = re.match(r'(Lot #\d+:\s*.+)', line)
        if lot_m:
            lot_name = lot_m.group(1).strip()
            i += 1
            continue
        jm = JOINT_RE_PYPDF.match(line)
        if jm:
            jlabel = jm.group(1)
            date_str = jm.group(2)
            # Find the data line (may be on next non-empty line)
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                dm = DATA_RE_PYPDF.match(lines[j].strip())
                if dm:
                    g = dm.groups()
                    time_str = g[0]
                    dt_str = f"{date_str} {time_str}"
                    try: dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S').isoformat()
                    except: dt = dt_str
                    # Check for ACCEPTED / REJECTED in nearby lines
                    j_status = 'OK'
                    for bk in range(1, 10):
                        if i - bk < 0: break
                        bl = lines[i - bk].strip()
                        if 'ACCEPTED' in bl: j_status = 'ACCEPTED'; break
                        if 'REJECTED' in bl: j_status = 'REJECTED'; break
                    joints.append(_make_joint(
                        jlabel, dt, lot_name, j_status,
                        g[1], g[2], g[4], g[5], g[6], g[7], g[8]
                    ))
                    i = j + 1
                    continue
        i += 1
    return joints


def _make_joint(jlabel, dt, lot, status, ft, ft_turns, st, st_turns, rpm, delta_t, delta_turns):
    def f(v):
        try: return float(v)
        except: return None
    return {
        'joint_label':     jlabel,
        'joint_num':       int(re.sub(r'_R\d+', '', jlabel)),
        'is_rerun':        '_R' in jlabel,
        'run_number':      int(re.search(r'_R(\d+)', jlabel).group(1)) if '_R' in jlabel else 1,
        'datetime':        dt,
        'lot':             lot,
        'status':          status,
        'final_torque':    f(ft),
        'final_turns':     f(ft_turns),
        'shoulder_torque': f(st),
        'shoulder_turns':  f(st_turns),
        'shoulder_rpm':    f(rpm),
        'delta_torque':    f(delta_t),
        'delta_turns':     f(delta_turns),
    }


def compute_stats(joints: list) -> dict:
    if not joints: return {}
    def st(data):
        d = [x for x in data if x is not None]
        if not d: return {}
        n = len(d); mean = sum(d) / n
        std = (sum((x - mean) ** 2 for x in d) / max(n - 1, 1)) ** .5
        return {'min': round(min(d), 2), 'max': round(max(d), 2),
                'mean': round(mean, 2), 'std': round(std, 2), 'count': n}
    ft_vals = [j['final_torque'] for j in joints if j['final_torque']]
    ft_st   = st(ft_vals)
    mean, std = ft_st.get('mean', 0), ft_st.get('std', 1) or 1
    reruns  = [j['joint_label'] for j in joints if j['is_rerun']]
    out_h   = [j['joint_label'] for j in joints if j['final_torque'] and j['final_torque'] > mean + 2 * std]
    out_l   = [j['joint_label'] for j in joints if j['final_torque'] and j['final_torque'] < mean - 2 * std]
    low_rpm = [j['joint_label'] for j in joints if j.get('shoulder_rpm') and j['shoulder_rpm'] < 2.5]
    times = []
    for idx in range(1, len(joints)):
        try:
            t1 = datetime.fromisoformat(joints[idx - 1]['datetime'])
            t2 = datetime.fromisoformat(joints[idx]['datetime'])
            diff = (t2 - t1).total_seconds() / 60
            if 0 < diff < 120:
                times.append({'joint': joints[idx]['joint_label'], 'minutes': round(diff, 1)})
        except: pass
    return {
        'total_joints': len(joints), 'rerun_count': len(reruns),
        'rerun_rate': round(len(reruns) / len(joints) * 100, 1),
        'ok_count': len(joints) - len(reruns),
        'outliers_high': out_h, 'outliers_low': out_l,
        'outlier_count': len(out_h) + len(out_l),
        'reruns': reruns, 'final_torque': ft_st,
        'shoulder_torque': st([j['shoulder_torque'] for j in joints]),
        'final_turns': st([j['final_turns'] for j in joints]),
        'delta_torque': st([j['delta_torque'] for j in joints]),
        'shoulder_rpm': st([j['shoulder_rpm'] for j in joints]),
        'low_rpm_joints': low_rpm, 'time_per_joint': times,
        'fast_joints': [t for t in times if t['minutes'] < 3],
        'slow_joints': [t for t in times if t['minutes'] > 20],
    }


def parse_mtt_pdf(content: bytes) -> dict | None:
    """
    Main entry — tries pdftotext first, then pypdf fallback.
    Returns {'is_mtt': bool, 'header': dict, 'joints': list, 'stats': dict}
    """
    text = None
    method = None

    # Try pdftotext -layout first (best)
    t = extract_text_pdftotext(content)
    if t and detect_mtt(t):
        text = t; method = 'pdftotext'
        logger.info("MTT: using pdftotext -layout")
    else:
        # Fallback: pypdf
        t2 = extract_text_pypdf(content)
        if t2 and detect_mtt(t2):
            text = t2; method = 'pypdf'
            logger.info("MTT: using pypdf fallback")
        elif t2:
            text = t2; method = 'pypdf'

    if not text:
        return None

    if not detect_mtt(text):
        return {'is_mtt': False}

    lines  = text.split('\n')
    header = parse_header(lines, text)

    # Choose parser based on method
    if method == 'pdftotext':
        joints = parse_joints_layout(lines)
    else:
        joints = parse_joints_pypdf(lines)
        # If pypdf parse gives 0, try layout anyway (sometimes works)
        if not joints:
            joints = parse_joints_layout(lines)

    if not joints:
        logger.warning("MTT: no joints parsed")
        return {'is_mtt': True, 'header': header, 'joints': [], 'stats': {}}

    stats = compute_stats(joints)
    logger.info(f"MTT [{method}]: {len(joints)} joints, {stats.get('rerun_count', 0)} reruns")
    return {'is_mtt': True, 'header': header, 'joints': joints, 'stats': stats, 'method': method}


def joints_to_historian(joints: list, job_id: int, device_id=None, file_id=None) -> list:
    return [{
        'job_id': job_id, 'device_id': device_id, 'file_id': file_id,
        'ts': j['datetime'], 'torque': j['final_torque'], 'turns': j['final_turns'],
        'rpm': j['shoulder_rpm'], 'speed': None, 'depth': None,
        'pressure': None, 'temperature': None, 'weight': None,
        'source': 'mtt_pdf',
        'extra_json': json.dumps({
            'joint_label': j['joint_label'], 'joint_num': j['joint_num'],
            'is_rerun': j['is_rerun'], 'shoulder_torque': j['shoulder_torque'],
            'shoulder_turns': j['shoulder_turns'], 'delta_torque': j['delta_torque'],
            'delta_turns': j['delta_turns'], 'lot': j.get('lot', ''),
            'status': j.get('status', 'OK'),
        }, ensure_ascii=False),
    } for j in joints]
