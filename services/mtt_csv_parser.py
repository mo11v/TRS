import io
import re
import csv
from datetime import datetime

from services.mtt_parser import compute_stats


def _to_float(v):
    try:
        if v is None or v == '':
            return None
        return float(v)
    except Exception:
        return None


def _joint_meta(makeup: str):
    label = str(makeup or '').strip()
    m = re.search(r'(\d+)', label)
    joint_num = int(m.group(1)) if m else 0
    r = re.search(r'_R(\d+)', label, re.I)
    if r:
        run_number = int(r.group(1)) + 1
        is_rerun = True
    else:
        run_number = 1
        is_rerun = False
    return label, joint_num, run_number, is_rerun


def parse_mtt_csv(content: bytes) -> dict:
    text = None
    for enc in ('utf-8-sig','utf-8','cp1252','latin1'):
        try:
            text = content.decode(enc)
            break
        except Exception:
            continue
    if text is None:
        raise ValueError('تعذر قراءة ملف CSV')

    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        return {'is_mtt': False}

    required = {'Time','Makeup','MaxTorque','MaxTurns','ShoulderTorque','ShoulderTurns','ShoulderRPM','DeltaTorque','DeltaTurns'}
    cols = set(rows[0].keys())
    if not required.issubset(cols):
        return {'is_mtt': False}

    first = rows[0]
    header = {
        'job_name': '',
        'pipe_type': '',
        'lot_names': [],
        'tong_model': '',
        'tong_arm': None,
        'ppt': None,
        'start_datetime': rows[0].get('Time',''),
        'end_datetime': rows[-1].get('Time',''),
        'load_cell_serial': '',
        'max_torque': _to_float(first.get('MaximumTorque')),
        'opt_torque': _to_float(first.get('OptimumTorque')),
        'min_torque': _to_float(first.get('MinimumTorque')),
        'high_shoulder': _to_float(first.get('High ShoulderTorque')),
        'low_shoulder': _to_float(first.get('Low ShoulderTorque')),
    }

    joints = []
    for row in rows:
        label, joint_num, run_number, is_rerun = _joint_meta(row.get('Makeup'))
        raw_time = str(row.get('Time') or '').strip()
        dt = raw_time.replace('  ', ' ')
        try:
            dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S').isoformat()
        except Exception:
            pass

        ft = _to_float(row.get('MaxTorque'))
        st = _to_float(row.get('ShoulderTorque'))
        rpm = _to_float(row.get('ShoulderRPM'))
        delta_turns = _to_float(row.get('DeltaTurns'))
        comment = ''
        status = 'OK'
        if header['min_torque'] is not None and ft is not None and ft < header['min_torque']:
            comment = 'Reject - Low Torque'; status = 'REJECTED'
        elif header['max_torque'] is not None and ft is not None and ft > header['max_torque']:
            comment = 'Reject - High Torque'; status = 'REJECTED'
        elif header['high_shoulder'] is not None and st is not None and st > header['high_shoulder']:
            comment = 'Reject - High Shoulder'; status = 'REJECTED'
        elif header['low_shoulder'] is not None and st is not None and st < header['low_shoulder']:
            comment = 'Reject - Low Shoulder'; status = 'REJECTED'
        elif delta_turns is not None and delta_turns > 0.100:
            comment = 'Reject - High Delta Turns'; status = 'REJECTED'

        joints.append({
            'joint_label': label,
            'joint_num': joint_num,
            'is_rerun': is_rerun,
            'run_number': run_number,
            'datetime': dt,
            'lot': '',
            'status': status,
            'final_torque': ft,
            'final_turns': _to_float(row.get('MaxTurns')),
            'shoulder_torque': st,
            'shoulder_turns': _to_float(row.get('ShoulderTurns')),
            'shoulder_rpm': rpm,
            'delta_torque': _to_float(row.get('DeltaTorque')),
            'delta_turns': delta_turns,
            'comment': comment,
        })

    stats = compute_stats(joints)
    return {'is_mtt': True, 'header': header, 'joints': joints, 'stats': stats, 'method': 'csv'}
