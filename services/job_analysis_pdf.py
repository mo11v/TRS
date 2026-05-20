"""
TRS Job Analysis PDF Report Generator — v64
- Arabic shaping via built-in Unicode presentation forms (no pip needed)
- FreeSerif font with 141 Arabic glyphs
- Real graphs via pymupdf page rendering
- Job Quality Rating section with progress bars
- Three download modes: critical / flagged / full
"""

import io, json, os
from datetime import datetime

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image as RLImage

# ── Arabic Shaper (stdlib only — no arabic_reshaper needed) ────────────────
_ARABIC_NON_JOINING = set(
    '\u0627\u0623\u0625\u0622\u0621\u062F\u0630\u0631\u0632\u0648\u0629\u0649\u0671'
)
_ARABIC_FORMS = {
    '\u0628':('\uFE8F','\uFE90','\uFE91','\uFE92'),'\u062A':('\uFE95','\uFE96','\uFE97','\uFE98'),
    '\u062B':('\uFE99','\uFE9A','\uFE9B','\uFE9C'),'\u062C':('\uFE9D','\uFE9E','\uFE9F','\uFEA0'),
    '\u062D':('\uFEA1','\uFEA2','\uFEA3','\uFEA4'),'\u062E':('\uFEA5','\uFEA6','\uFEA7','\uFEA8'),
    '\u0633':('\uFEB3','\uFEB4','\uFEB5','\uFEB6'),'\u0634':('\uFEB7','\uFEB8','\uFEB9','\uFEBA'),
    '\u0635':('\uFEBB','\uFEBC','\uFEBD','\uFEBE'),'\u0636':('\uFEBF','\uFEC0','\uFEC1','\uFEC2'),
    '\u0637':('\uFEC3','\uFEC4','\uFEC5','\uFEC6'),'\u0638':('\uFEC7','\uFEC8','\uFEC9','\uFECA'),
    '\u0639':('\uFECB','\uFECC','\uFECD','\uFECE'),'\u063A':('\uFECF','\uFED0','\uFED1','\uFED2'),
    '\u0641':('\uFED3','\uFED4','\uFED5','\uFED6'),'\u0642':('\uFED7','\uFED8','\uFED9','\uFEDA'),
    '\u0643':('\uFEDB','\uFEDC','\uFEDD','\uFEDE'),'\u0644':('\uFEDF','\uFEE0','\uFEE1','\uFEE2'),
    '\u0645':('\uFEE3','\uFEE4','\uFEE5','\uFEE6'),'\u0646':('\uFEE7','\uFEE8','\uFEE9','\uFEEA'),
    '\u0647':('\uFEEB','\uFEEC','\uFEED','\uFEEE'),'\u064A':('\uFEF1','\uFEF2','\uFEF3','\uFEF4'),
    '\u0627':('\uFE8D','\uFE8E',None,None),'\u0623':('\uFE83','\uFE84',None,None),
    '\u0625':('\uFE87','\uFE88',None,None),'\u0622':('\uFE81','\uFE82',None,None),
    '\u0621':('\uFE80',None,None,None),
    '\u062F':('\uFEA9','\uFEAA',None,None),'\u0630':('\uFEAB','\uFEAC',None,None),
    '\u0631':('\uFEAD','\uFEAE',None,None),'\u0632':('\uFEAF','\uFEB0',None,None),
    '\u0648':('\uFEED','\uFEEE',None,None),'\u0629':('\uFE93','\uFE94',None,None),
    '\u0649':('\uFEEF','\uFEF0',None,None),
}

def _ar(text: str) -> str:
    """
    Return Arabic text as-is — FreeSerif font renders Arabic Unicode natively.
    No manual shaping needed; the font handles it correctly.
    """
    return text




# ── Arabic Font Setup ─────────────────────────────────────────────────────
_FONT      = 'Helvetica'
_FONT_BOLD = 'Helvetica-Bold'

def _init_font():
    global _FONT, _FONT_BOLD
    # FreeSerif has 141/144 Arabic presentation form glyphs — best available
    candidates = [
        ('/usr/share/fonts/truetype/freefont/FreeSerif.ttf',     'FreeSerif',
         '/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf', 'FreeSerifBold'),
        ('/usr/share/fonts/truetype/freefont/FreeSans.ttf',      'FreeSans',
         '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',  'FreeSansBold'),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',      'DejaVuSans',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 'DejaVuSans-Bold'),
    ]
    for reg_path, reg_name, bold_path, bold_name in candidates:
        if os.path.exists(reg_path):
            try:
                pdfmetrics.registerFont(TTFont(reg_name, reg_path))
                _FONT = reg_name
                if os.path.exists(bold_path):
                    pdfmetrics.registerFont(TTFont(bold_name, bold_path))
                    _FONT_BOLD = bold_name
                else:
                    _FONT_BOLD = reg_name
                return
            except Exception:
                continue

_init_font()

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
import logging
logger = logging.getLogger(__name__)

# ── Colors ────────────────────────────────────────────────────────────────
BLUE       = colors.HexColor('#1f6feb')
BLUE_LIGHT = colors.HexColor('#58a6ff')
GREEN      = colors.HexColor('#10b981')
GREEN_DIM  = colors.HexColor('#e6f9f0')
RED        = colors.HexColor('#ef4444')
RED_DIM    = colors.HexColor('#fef2f2')
ORANGE     = colors.HexColor('#d29922')
ORANGE_DIM = colors.HexColor('#fffbeb')
GREY       = colors.HexColor('#6b7280')
GREY_LIGHT = colors.HexColor('#f3f4f6')
WHITE      = colors.white
TEXT_DARK  = colors.HexColor('#111827')
TEXT_MID   = colors.HexColor('#374151')
TEXT_LIGHT = colors.HexColor('#6b7280')


# ── Styles ─────────────────────────────────────────────────────────────────
def make_styles():
    return {
        'title':    ParagraphStyle('title',    fontName=_FONT_BOLD, fontSize=20, leading=24,
                                   textColor=BLUE, spaceAfter=4),
        'subtitle': ParagraphStyle('subtitle', fontName=_FONT,      fontSize=11, leading=14,
                                   textColor=TEXT_LIGHT, spaceAfter=2),
        'h1':       ParagraphStyle('h1',       fontName=_FONT_BOLD, fontSize=13, leading=16,
                                   textColor=BLUE, spaceBefore=10, spaceAfter=4),
        'h2':       ParagraphStyle('h2',       fontName=_FONT_BOLD, fontSize=10, leading=13,
                                   textColor=TEXT_DARK, spaceBefore=6, spaceAfter=3),
        'body':     ParagraphStyle('body',     fontName=_FONT,      fontSize=9,  leading=13,
                                   textColor=TEXT_MID),
        'body_sm':  ParagraphStyle('body_sm',  fontName=_FONT,      fontSize=8,  leading=11,
                                   textColor=TEXT_LIGHT),
        'label':    ParagraphStyle('label',    fontName=_FONT_BOLD, fontSize=8,  leading=10,
                                   textColor=TEXT_LIGHT),
        'ok':       ParagraphStyle('ok',       fontName=_FONT_BOLD, fontSize=9,  leading=12,
                                   textColor=GREEN),
        'warn':     ParagraphStyle('warn',     fontName=_FONT_BOLD, fontSize=9,  leading=12,
                                   textColor=ORANGE),
        'crit':     ParagraphStyle('crit',     fontName=_FONT_BOLD, fontSize=9,  leading=12,
                                   textColor=RED),
        # Arabic right-aligned
        'ar':       ParagraphStyle('ar',       fontName=_FONT,      fontSize=9,  leading=14,
                                   textColor=TEXT_MID, alignment=TA_RIGHT),
        'ar_bold':  ParagraphStyle('ar_bold',  fontName=_FONT_BOLD, fontSize=9,  leading=14,
                                   textColor=TEXT_DARK, alignment=TA_RIGHT),
    }


# ── Analysis Logic ─────────────────────────────────────────────────────────
def analyze_joint(j, specs, ft_mean, ft_std):
    ft   = j.get('final_torque') or 0
    st   = j.get('shoulder_torque') or 0
    st_t = j.get('shoulder_turns') or 0
    ft_t = j.get('final_turns') or 0
    rpm  = j.get('shoulder_rpm') or 0
    dt_t = j.get('delta_turns') or 0
    findings = []

    # 1. Final Torque
    if specs.get('max_torque') and ft > specs['max_torque']:
        findings.append(('REJECT','Over-Torque',
            f"FT {ft:.0f} > Max {specs['max_torque']:,}",
            "Over-torque — risk of pin/box yielding, potential failure downhole."))
    elif specs.get('min_torque') and ft < specs['min_torque']:
        findings.append(('REJECT','Under-Torque',
            f"FT {ft:.0f} < Min {specs['min_torque']:,}",
            "Under-torque — connection incomplete, risk of back-off or leak."))
    else:
        opt = specs.get('opt_torque') or ft
        pct = abs((ft - opt) / max(opt,1) * 100)
        findings.append(('OK','Final Torque',
            f"FT {ft:.0f} ft-lb ({pct:.1f}% from Opt)",
            "Final Torque within specification — connection made up correctly."))

    # 2. Shoulder
    if specs.get('high_shoulder') and st > specs['high_shoulder']:
        findings.append(('FLAG','High Shoulder',
            f"ST {st:.0f} > High {specs['high_shoulder']:,}",
            "Shoulder torque exceeded High limit — possible premature shoulder or thread debris."))
    elif specs.get('low_shoulder') and st < specs['low_shoulder']:
        findings.append(('REJECT','Under-Shoulder',
            f"ST {st:.0f} < Low {specs['low_shoulder']:,}",
            "Shoulder not achieved — seal integrity not guaranteed, risk of leak."))
    else:
        findings.append(('OK','Shoulder', f"ST {st:.0f} ft-lb OK", ""))

    # 3. Delta Turns
    if dt_t < 0.010:
        findings.append(('FLAG','Delta Turns Low',
            f"Delta Turns {dt_t:.3f} < 0.010",
            "Delta Turns too low (<0.010) — impact loading pattern, uneven thread stress."))
    elif dt_t > 0.100:
        findings.append(('FLAG','Delta Turns High',
            f"Delta Turns {dt_t:.3f} > 0.100",
            "Delta Turns too high (>0.100) — possible plastic deformation."))
    else:
        findings.append(('OK','Delta Turns', f"Delta {dt_t:.3f} OK", ""))

    # 4. RPM
    if rpm > 0 and rpm < 2.0:
        findings.append(('REJECT','Critical RPM',
            f"RPM {rpm:.1f} < 2.0 — Galling Risk",
            "Critical low RPM — galling almost certain, permanent thread damage."))
    elif rpm > 0 and rpm < 2.5:
        findings.append(('FLAG','Low RPM',
            f"RPM {rpm:.1f} — Below Recommended",
            f"Low shoulder RPM ({rpm:.1f}) — Tenaris Blue recommends 2.5–6.0 RPM."))
    elif rpm > 6.0:
        findings.append(('FLAG','High RPM',
            f"RPM {rpm:.1f} — Above Recommended",
            f"High shoulder RPM ({rpm:.1f} > 6.0) — risk of heat and galling."))
    else:
        findings.append(('OK','Shoulder RPM', f"RPM {rpm:.1f} OK", ""))

    # 5. Late shoulder
    if ft_t > 0 and st_t > 0 and st_t / ft_t > 0.97:
        findings.append(('FLAG','Late Shoulder',
            f"Shoulder at {st_t/ft_t*100:.0f}% of Total Turns",
            "Shoulder occurred too late — possible cross-threading or damaged thread."))

    # 6. Statistical outlier
    if ft_mean and ft_std:
        z = (ft - ft_mean) / ft_std
        if abs(z) > 3:
            findings.append(('FLAG','Statistical Outlier',
                f"Z-score {z:+.1f}σ — Outlier",
                f"Statistical outlier — FT deviates from job average ({ft_mean:.0f} ± {ft_std:.0f} ft-lb."))
        elif abs(z) > 2:
            findings.append(('FLAG','Outlier 2σ', f"Z-score {z:+.1f}σ",
                "Torque outside normal range for this job (Z > 2σ)."))
    return findings


def detect_prior_damage(joint_num, all_joints, specs):
    runs = sorted([j for j in all_joints if j.get('joint_num')==joint_num],
                  key=lambda x: x.get('run_number',1))
    if len(runs) < 2:
        return None
    prior = runs[:-1]; final = runs[-1]; flags=[]; risk='LOW'
    for run in prior:
        rn=run.get('run_number',1); rpm=run.get('shoulder_rpm') or 99
        dt=run.get('delta_turns') or 0; ft=run.get('final_torque') or 0
        if 0 < rpm < 2.0:
            flags.append(('CRITICAL',rn,f"Run {rn}: RPM = {rpm:.1f} (Critical Low)",
                f"Run {rn}: RPM={rpm:.1f} at shoulder — galling damage permanent."))
            risk='CRITICAL'
        if dt > 0.100:
            flags.append(('CRITICAL',rn,f"Run {rn}: Delta Turns = {dt:.3f}",
                f"Run {rn}: Delta Turns={dt:.3f} — permanent metal deformation in prior run."))
            if risk!='CRITICAL': risk='HIGH'
        if 2.0<=rpm<2.5:
            flags.append(('HIGH',rn,f"Run {rn}: RPM = {rpm:.1f} (Below 2.5)",
                "Low RPM in prior run — inadequate lubrication."))
            if risk=='LOW': risk='HIGH'
        if specs.get('max_torque') and ft>specs['max_torque']:
            flags.append(('HIGH',rn,f"Run {rn}: FT = {ft:.0f} > Max {specs['max_torque']:,}",
                "Over-torque in prior run — connection exceeded maximum limit."))
            if risk=='LOW': risk='HIGH'
    if not flags: return None
    actions={
        'CRITICAL':('REJECT — Pull & Inspect Thread',
                    "Pull pipe and inspect thread — final run accepted but prior damage is permanent."),
        'HIGH':    ('Hold — Review with Engineer',
                    "Review with engineer before continuing operations."),
    }
    action_label, action_detail = actions.get(risk,('Monitor',''))
    return {'runs':runs,'final':final,'flags':flags,'risk':risk,
            'action':action_label,'action_detail':action_detail,'total_runs':len(runs)}


def get_verdict(findings):
    sevs=[f[0] for f in findings]
    if 'REJECT' in sevs: return 'REJECT', RED, RED_DIM
    flags=[f for f in findings if f[0]=='FLAG']
    crit=[f for f in flags if any(k in f[1] for k in ('RPM','Delta','Shoulder'))]
    if crit: return 'CHECK', ORANGE, ORANGE_DIM
    if flags: return 'MONITOR', colors.HexColor('#f97316'), colors.HexColor('#fff4ed')
    return 'OK', GREEN, GREEN_DIM


# ── Job Quality Rating ──────────────────────────────────────────────────────
def compute_job_rating(joints, summary, specs):
    if not joints:
        return {'score':0,'grade':'N/A','color':'#888888','breakdown':{},'summary_text':'No data','details':{}}
    total=len(joints); ft_mean=summary.get('ft_mean') or 0
    reruns=sum(1 for j in joints if j.get('is_rerun')); rerun_rate=reruns/total*100
    opt=specs.get('opt_torque') or ft_mean
    mn=specs.get('min_torque') or ft_mean*0.9
    mx=specs.get('max_torque') or ft_mean*1.1
    in_window=sum(1 for j in joints if j.get('final_torque') and mn<=j['final_torque']<=mx)
    near_opt =sum(1 for j in joints if j.get('final_torque') and abs(j['final_torque']-opt)/max(opt,1)<0.05)
    torque_score=min(25,(in_window/total*20)+(near_opt/total*5))
    if   rerun_rate==0:   rerun_score=25
    elif rerun_rate<5:    rerun_score=22
    elif rerun_rate<10:   rerun_score=18
    elif rerun_rate<15:   rerun_score=13
    elif rerun_rate<20:   rerun_score=8
    elif rerun_rate<30:   rerun_score=4
    else:                 rerun_score=0
    rpms=[j.get('shoulder_rpm') or 0 for j in joints if j.get('shoulder_rpm')]
    crit_rpm=sum(1 for r in rpms if r<2.0); low_rpm=sum(1 for r in rpms if 2.0<=r<2.5)
    rpm_score=max(0,20-(crit_rpm/total*20)-(low_rpm/total*8)) if rpms else 10
    dts=[j.get('delta_turns') or 0 for j in joints if j.get('delta_turns')]
    bad_dt=sum(1 for d in dts if d<0.010 or d>0.100)
    dt_score=max(0,15-(bad_dt/total*15)) if dts else 8
    outliers=summary.get('outlier_count') or 0
    outlier_score=max(0,15-(outliers/total*100*3))
    total_score=torque_score+rerun_score+rpm_score+dt_score+outlier_score
    score_10=round(total_score/10,1)
    if   score_10>=9.0: grade,color='Excellent','#10b981'
    elif score_10>=7.5: grade,color='Good',     '#3b82f6'
    elif score_10>=6.0: grade,color='Fair',     '#f59e0b'
    elif score_10>=4.0: grade,color='Poor',     '#f97316'
    else:               grade,color='Critical', '#ef4444'
    if   score_10>=9.0: stxt=f"Excellent — {in_window}/{total} joints within torque window, Rerun {rerun_rate:.1f}%."
    elif score_10>=7.5: stxt=f"Good — {total-in_window} joints outside optimum window, Rerun {rerun_rate:.1f}%."
    elif score_10>=6.0: stxt=f"Fair — Rerun rate {rerun_rate:.1f}%, review flagged joints."
    elif score_10>=4.0: stxt=f"Poor — Rerun rate {rerun_rate:.1f}%, {outliers} outliers. Comprehensive review required."
    else:               stxt=f"Critical — Rerun rate {rerun_rate:.1f}%, {outliers} outliers. Immediate review required."
    return {'score':score_10,'grade':grade,'color':color,'summary_text':stxt,
            'breakdown':{'Torque Compliance':round(torque_score,1),'Rerun Rate':round(rerun_score,1),
                         'RPM Consistency':round(rpm_score,1),'Delta Turns':round(dt_score,1),
                         'Outliers':round(outlier_score,1)},
            'details':{'in_window':in_window,'rerun_rate':round(rerun_rate,1),
                       'critical_rpm':crit_rpm,'bad_dt':bad_dt,'outliers':outliers}}


# ── PDF Builder ─────────────────────────────────────────────────────────────
def build_job_analysis_pdf(job, summary, joints, mode='flagged',
                            output_path=None, pdf_bytes=None, page_map=None):
    buf=io.BytesIO(); target=output_path or buf
    specs={}
    sj=summary.get('stats_json') or {}
    if isinstance(sj,str):
        try: sj=json.loads(sj)
        except: sj={}
    for k in ['max_torque','opt_torque','min_torque','high_shoulder','low_shoulder']:
        specs[k]=sj.get(k) or summary.get(k)
    ft_mean=summary.get('ft_mean') or 0; ft_std=summary.get('ft_std') or 1

    joint_data=[]
    for j in joints:
        findings=analyze_joint(j,specs,ft_mean,ft_std)
        prior=detect_prior_damage(j.get('joint_num'),joints,specs)
        verdict,vc,vbg=get_verdict(findings)
        has_issues=verdict!='OK' or prior is not None
        joint_data.append({'joint':j,'findings':findings,'prior':prior,
                           'verdict':verdict,'vc':vc,'vbg':vbg,'has_issues':has_issues})

    if mode=='critical':
        joint_data=[d for d in joint_data if d['verdict']=='REJECT'
                    or (d['prior'] and d['prior']['risk']=='CRITICAL')]
    elif mode in ('flagged','issues'):
        joint_data=[d for d in joint_data if d['has_issues']]

    rating=compute_job_rating(joints,summary,specs)

    doc=SimpleDocTemplate(target,pagesize=A4,
        leftMargin=15*mm,rightMargin=15*mm,topMargin=20*mm,bottomMargin=20*mm,
        title=f"Job Analysis — {job.get('job_number','')}")
    S=make_styles(); W=A4[0]-30*mm; story=[]

    # ── Cover ──────────────────────────────────────────────────────────────
    mode_label={'critical':'Critical Report — REJECT & Prior Damage Only',
                'flagged': 'Issues Report — Flagged & Rejected Joints',
                'issues':  'Issues Report — Flagged & Rejected Joints',
                'full':    'Full Report — All Joints'}.get(mode,'Issues Report')
    story.append(_colored_box(W,38*mm,colors.HexColor('#f0f6ff'),[
        Paragraph("Job Analysis Report",S['title']),
        Paragraph(mode_label,S['subtitle']),
        Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",S['body_sm']),
    ]))
    story.append(Spacer(1,5*mm))

    # Job info table
    story.append(_info_table([
        ['Job Number',job.get('job_number','—'),'Customer',job.get('customer','—')],
        ['Rig / Well', job.get('rig','—'),      'Status',  job.get('status','—')],
        ['Pipe Type',  summary.get('pipe_type','—'),'Tong',summary.get('tong_model','—') or '—'],
        ['Start Date', str(job.get('start_date') or '—')[:16],'Report Date',datetime.now().strftime('%Y-%m-%d')],
    ],W,S))
    story.append(Spacer(1,5*mm))

    # ── Rating Card ────────────────────────────────────────────────────────
    story.append(_rating_card(rating,W,S))
    story.append(Spacer(1,5*mm))

    # KPIs
    total=summary.get('total_joints',0) or len(joints)
    reruns=summary.get('rerun_count',0)
    n_shown=len(joint_data)
    kpi_data=[[
        _kpi_cell('Total Joints',str(total),BLUE,S),
        _kpi_cell('Shown in Report',str(n_shown),RED if n_shown>total*0.1 else ORANGE,S),
        _kpi_cell('Reruns',f"{reruns} ({summary.get('rerun_rate',0):.1f}%)",
                  RED if reruns/max(total,1)>0.10 else ORANGE,S),
        _kpi_cell('FT Mean',f"{ft_mean:.0f} ft-lb",BLUE,S),
    ]]
    kt=Table(kpi_data,colWidths=[W/4]*4)
    kt.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
                             ('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3)]))
    story.append(kt); story.append(Spacer(1,5*mm))

    # Status banner
    if n_shown==0: story.append(_banner("All Clear — No Issues Detected",GREEN,GREEN_DIM,W,S))
    elif n_shown<=total*0.05: story.append(_banner(f"{n_shown} Joint(s) Require Attention",ORANGE,ORANGE_DIM,W,S))
    else: story.append(_banner(f"{n_shown} Joints Have Issues — Review Required",RED,RED_DIM,W,S))
    story.append(Spacer(1,5*mm))

    # ── Summary table ──────────────────────────────────────────────────────
    story.append(Paragraph("Joint Summary",S['h1'])); story.append(Spacer(1,2*mm))
    hdr=['Joint#','FT\n(ft-lb)','ST\n(ft-lb)','RPM','ΔTurns','Runs','MTT\nVerdict','TRS\nVerdict']
    rows=[hdr]; row_styles=[]
    for idx,d in enumerate(joint_data,1):
        j=d['joint']; v=d['verdict']
        runs_count=d['prior']['total_runs'] if d['prior'] else 1
        rows.append([j.get('joint_label','?'),
            f"{j.get('final_torque',0):.0f}"  if j.get('final_torque') else '—',
            f"{j.get('shoulder_torque',0):.0f}" if j.get('shoulder_torque') else '—',
            f"{j.get('shoulder_rpm',0):.1f}"   if j.get('shoulder_rpm') else '—',
            f"{j.get('delta_turns',0):.3f}"    if j.get('delta_turns') else '—',
            str(runs_count), j.get('status','OK'), v])
        if v=='REJECT' or (d['prior'] and d['prior']['risk']=='CRITICAL'):
            row_styles.append(('BACKGROUND',(0,idx),(-1,idx),colors.HexColor('#fef2f2')))
        elif v=='CHECK':
            row_styles.append(('BACKGROUND',(0,idx),(-1,idx),colors.HexColor('#fffbeb')))
    tbl=Table(rows,colWidths=[20*mm,22*mm,22*mm,16*mm,18*mm,14*mm,22*mm,22*mm],repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),BLUE),('TEXTCOLOR',(0,0),(-1,0),WHITE),
        ('FONTNAME',(0,0),(-1,0),_FONT_BOLD),('FONTSIZE',(0,0),(-1,-1),8),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('FONTNAME',(0,1),(-1,-1),_FONT),('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,GREY_LIGHT]),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#d1d5db')),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),*row_styles]))
    story.append(tbl); story.append(PageBreak())

    # ── Detailed cards ─────────────────────────────────────────────────────
    story.append(Paragraph(
        "Detailed Joint Analysis" if mode=='full' else "Flagged & Rejected Joints — Detail",S['h1']))
    story.append(Spacer(1,2*mm))
    if not joint_data:
        story.append(_banner("No issues found — All joints passed.",GREEN,GREEN_DIM,W,S))
    else:
        for d in joint_data:
            story.extend(_joint_card(d,W,S,specs,ft_mean,ft_std,pdf_bytes=pdf_bytes,page_map=page_map or {}))
            story.append(Spacer(1,4*mm))

    doc.build(story,onFirstPage=_page_footer,onLaterPages=_page_footer)
    if output_path: return None
    return buf.getvalue()


# ── Rating Card ───────────────────────────────────────────────────────────
def _rating_card(rating, W, S):
    """Clean rating card with proper progress bars using colWidths approach."""
    score     = rating['score']
    grade     = rating['grade']
    color     = colors.HexColor(rating['color'])
    breakdown = rating['breakdown']
    max_each  = {'Torque Compliance':25,'Rerun Rate':25,
                 'RPM Consistency':20,'Delta Turns':15,'Outliers':15}

    # Left: score block
    score_rows = [
        [Paragraph("Job Quality Rating",
                   ParagraphStyle('rl', fontName=_FONT_BOLD, fontSize=9,
                                  textColor=TEXT_MID, leading=11))],
        [Paragraph(f"{score}/10",
                   ParagraphStyle('rs', fontName=_FONT_BOLD, fontSize=28,
                                  textColor=color, leading=32))],
        [Paragraph(grade,
                   ParagraphStyle('rg', fontName=_FONT_BOLD, fontSize=11,
                                  textColor=color, leading=13))],
        [Paragraph(rating.get('summary_text',''),
                   ParagraphStyle('rt', fontName=_FONT, fontSize=7,
                                  textColor=TEXT_LIGHT, leading=9))],
    ]
    score_tbl = Table(score_rows, colWidths=[W*0.28])
    score_tbl.setStyle(TableStyle([
        ('TOPPADDING',   (0,0),(-1,-1), 2),
        ('BOTTOMPADDING',(0,0),(-1,-1), 2),
        ('LEFTPADDING',  (0,0),(-1,-1), 10),
        ('RIGHTPADDING', (0,0),(-1,-1), 8),
        ('VALIGN',       (0,0),(-1,-1), 'MIDDLE'),
    ]))

    # Right: bar chart — each row = [label | bar_color | bar_empty | score]
    # Use 4 columns with fixed widths — no nested tables
    BAR_W    = W * 0.52
    LABEL_W  = W * 0.18
    SCORE_W  = W * 0.12
    bar_rows = []

    for label, val in breakdown.items():
        mx  = max_each.get(label, 25)
        pct = min(max(val / mx, 0.0), 1.0)
        bc  = (colors.HexColor('#10b981') if pct >= 0.8 else
               colors.HexColor('#f59e0b') if pct >= 0.5 else
               colors.HexColor('#ef4444'))
        filled_w = max(BAR_W * pct, 1)
        empty_w  = max(BAR_W - filled_w, 0)

        row = [
            Paragraph(label,
                      ParagraphStyle('lbl', fontName=_FONT, fontSize=8,
                                     textColor=TEXT_MID, leading=10)),
            '',  # filled portion — colored by BACKGROUND style
            '',  # empty portion  — grey
            Paragraph(f"{val:.0f}/{mx}",
                      ParagraphStyle('sc', fontName=_FONT_BOLD, fontSize=8,
                                     textColor=bc, leading=10)),
        ]
        bar_rows.append((row, bc, filled_w, empty_w))

    # Build table with dynamic column widths per row — use fixed avg widths
    # (ReportLab requires uniform colWidths per table)
    # Solution: one table per bar, stack them
    bar_elements = []
    for row_data, bc, fw, ew in bar_rows:
        if ew <= 0:
            cws = [LABEL_W, BAR_W, 0.1, SCORE_W]
        else:
            cws = [LABEL_W, fw, ew, SCORE_W]
        t = Table([row_data], colWidths=cws)
        t.setStyle(TableStyle([
            ('BACKGROUND',   (1,0),(1,0), bc),
            ('BACKGROUND',   (2,0),(2,0), colors.HexColor('#e5e7eb')),
            ('TOPPADDING',   (0,0),(-1,-1), 4),
            ('BOTTOMPADDING',(0,0),(-1,-1), 4),
            ('LEFTPADDING',  (0,0),(-1,-1), 3),
            ('RIGHTPADDING', (0,0),(-1,-1), 3),
            ('VALIGN',       (0,0),(-1,-1), 'MIDDLE'),
        ]))
        bar_elements.append([t])

    bars_tbl = Table(bar_elements, colWidths=[W*0.70])
    bars_tbl.setStyle(TableStyle([
        ('TOPPADDING',   (0,0),(-1,-1), 0),
        ('BOTTOMPADDING',(0,0),(-1,-1), 0),
        ('LEFTPADDING',  (0,0),(-1,-1), 0),
        ('RIGHTPADDING', (0,0),(-1,-1), 0),
    ]))

    outer = Table([[score_tbl, bars_tbl]], colWidths=[W*0.30, W*0.70])
    outer.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(-1,-1), colors.HexColor('#f8fafc')),
        ('BOX',          (0,0),(-1,-1), 1.5, color),
        ('LINEAFTER',    (0,0),(0,-1), 0.5, colors.HexColor('#d1d5db')),
        ('TOPPADDING',   (0,0),(-1,-1), 8),
        ('BOTTOMPADDING',(0,0),(-1,-1), 8),
        ('LEFTPADDING',  (0,0),(-1,-1), 0),
        ('RIGHTPADDING', (0,0),(-1,-1), 8),
        ('VALIGN',       (0,0),(-1,-1), 'MIDDLE'),
    ]))
    return outer


# ── Joint Card ────────────────────────────────────────────────────────────
def _joint_card(d, W, S, specs, ft_mean, ft_std, pdf_bytes=None, page_map=None):
    elements=[]
    j=d['joint']; verdict=d['verdict']; vc=d['vc']; prior=d['prior']
    jlabel=j.get('joint_label','?')

    v_text={'REJECT':'⛔ REJECT — Requires Immediate Review','CHECK':'⚠ CHECK — Engineering Flags',
            'MONITOR':'⚠ MONITOR — Minor Notes','OK':'✓ ACCEPTED'}.get(verdict,verdict)
    v_bg={'REJECT':RED_DIM,'CHECK':ORANGE_DIM,'MONITOR':ORANGE_DIM,'OK':GREEN_DIM}.get(verdict,WHITE)

    hdr=Table([[
        Paragraph(f"Joint #{jlabel}",ParagraphStyle('jh',fontName=_FONT_BOLD,fontSize=13,
            textColor=BLUE,leading=15)),
        Paragraph(v_text,ParagraphStyle('jv',fontName=_FONT_BOLD,fontSize=11,
            textColor=vc,leading=13,alignment=TA_RIGHT)),
    ]],colWidths=[W*0.5,W*0.5])
    hdr.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),v_bg),('TOPPADDING',(0,0),(-1,-1),8),
        ('BOTTOMPADDING',(0,0),(-1,-1),8),('LEFTPADDING',(0,0),(-1,-1),10),
        ('RIGHTPADDING',(0,0),(-1,-1),10),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('BOX',(0,0),(-1,-1),1,vc)]))
    # ── 1. HEADER + GRAPH together (never split across pages) ─────────────────
    keep_block = [hdr, Spacer(1, 3*mm)]

    graph_png = None
    if pdf_bytes:
        try:
            from services.graph_extractor import extract_joint_graph
            pm = page_map if page_map else {}
            graph_png = extract_joint_graph(pdf_bytes, j.get('joint_num',0), j.get('run_number',1), pm)
        except Exception as e:
            logger.debug(f"Graph extract failed joint {j.get('joint_num')}: {e}")

    if graph_png:
        keep_block.append(Paragraph("Torque vs Turns — Original MTT Graph", S['h2']))
        keep_block.append(RLImage(io.BytesIO(graph_png), width=W, height=W*0.46))
        keep_block.append(Spacer(1, 3*mm))
    else:
        # Placeholder when PDF graph not available
        no_graph = Table([[
            Paragraph("Graph not available — PDF graph pages not found in this report.",
                      ParagraphStyle('ng', fontName=_FONT, fontSize=9,
                                     textColor=colors.HexColor('#888888'), leading=12))
        ]], colWidths=[W])
        no_graph.setStyle(TableStyle([
            ('BACKGROUND',   (0,0),(-1,-1), colors.HexColor('#f5f5f5')),
            ('TOPPADDING',   (0,0),(-1,-1), 12),
            ('BOTTOMPADDING',(0,0),(-1,-1), 12),
            ('LEFTPADDING',  (0,0),(-1,-1), 10),
            ('BOX',          (0,0),(-1,-1), 0.5, colors.HexColor('#dddddd')),
        ]))
        keep_block.append(no_graph)
        keep_block.append(Spacer(1, 3*mm))

    elements.append(KeepTogether(keep_block))

    # ── 2. METRICS TABLE ───────────────────────────────────────────────────
    ft=j.get('final_torque') or 0; st=j.get('shoulder_torque') or 0
    rpm=j.get('shoulder_rpm') or 0; dt=j.get('delta_turns') or 0
    dt_str=str(j.get('datetime',''))[:16]; runs_n=prior['total_runs'] if prior else 1

    def spec_str(lo,hi):
        l,h=specs.get(lo),specs.get(hi)
        if l and h: return f"{l:,}–{h:,} ft-lb"
        if h:       return f"≤ {h:,} ft-lb"
        return '—'

    metrics=[
        ['Metric','Value','Specification','Status'],
        ['Final Torque',    f"{ft:.0f} ft-lb",    spec_str('min_torque','max_torque'),
         '✓ OK' if specs.get('min_torque') and specs.get('max_torque') and specs['min_torque']<=ft<=specs['max_torque'] else '⚠ ISSUE'],
        ['Shoulder Torque', f"{st:.0f} ft-lb",    spec_str('low_shoulder','high_shoulder'),
         '✓ OK' if specs.get('low_shoulder') and specs.get('high_shoulder') and specs['low_shoulder']<=st<=specs['high_shoulder'] else '⚠ ISSUE'],
        ['Shoulder RPM',    f"{rpm:.1f} RPM",      '2.5–6.0 RPM',
         '✓ OK' if 2.5<=rpm<=6.0 else '⚠ LOW' if rpm<2.5 else '⚠ HIGH'],
        ['Delta Turns',     f"{dt:.3f}",           '0.010–0.100',
         '✓ OK' if 0.010<=dt<=0.100 else '⚠ ISSUE'],
        ['Date / Time',     dt_str,'',''],
        ['Total Runs',      str(runs_n),'','⚠ RERUN' if runs_n>1 else ''],
    ]
    m_tbl=Table(metrics,colWidths=[35*mm,35*mm,50*mm,40*mm])
    m_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1e3a5f')),('TEXTCOLOR',(0,0),(-1,0),WHITE),
        ('FONTNAME',(0,0),(-1,0),_FONT_BOLD),('FONTSIZE',(0,0),(-1,-1),8),
        ('ALIGN',(0,0),(-1,-1),'LEFT'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('FONTNAME',(0,1),(-1,-1),_FONT),('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,GREY_LIGHT]),
        ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#d1d5db')),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),6)]))
    elements.append(m_tbl)

    # ── 3. PRIOR DAMAGE ────────────────────────────────────────────────────
    if prior:
        elements.append(Spacer(1,3*mm))
        pd_color=RED if prior['risk']=='CRITICAL' else ORANGE
        pd_bg=RED_DIM if prior['risk']=='CRITICAL' else ORANGE_DIM
        elements.append(Paragraph(
            f"{'🚨' if prior['risk']=='CRITICAL' else '⚠️'} PRIOR DAMAGE RISK — {prior['action']}",
            ParagraphStyle('pd',fontName=_FONT_BOLD,fontSize=10,textColor=pd_color,
                leading=13,backColor=pd_bg,borderPad=6,spaceBefore=2,spaceAfter=2)))
        elements.append(Paragraph(prior['action_detail'],S['ar']))
        elements.append(Spacer(1,2*mm))

        runs_hdr=['Run#','Final Torque','Shoulder T','RPM','Delta T','Issue']
        runs_rows=[runs_hdr]
        for run in prior['runs']:
            is_final=run==prior['final']; rn=run.get('run_number',1)
            r_flags=[f for f in prior['flags'] if f[1]==rn]
            issue_str=r_flags[0][2] if r_flags else ('Final Run (Accepted)' if is_final else '—')
            runs_rows.append([f"Run {rn}{' (Final)' if is_final else ''}",
                f"{run.get('final_torque',0):.0f}",f"{run.get('shoulder_torque',0):.0f}",
                f"{run.get('shoulder_rpm',0):.1f}",f"{run.get('delta_turns',0):.3f}",issue_str[:35]])
        r_tbl=Table(runs_rows,colWidths=[22*mm,24*mm,24*mm,16*mm,18*mm,W-104*mm])
        r_tbl.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#b91c1c')),('TEXTCOLOR',(0,0),(-1,0),WHITE),
            ('FONTNAME',(0,0),(-1,0),_FONT_BOLD),('FONTSIZE',(0,0),(-1,-1),8),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('FONTNAME',(0,1),(-1,-1),_FONT),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#fef2f2'),WHITE]),
            ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#fca5a5')),
            ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
            ('LEFTPADDING',(0,0),(-1,-1),4)]))
        elements.append(r_tbl); elements.append(Spacer(1,2*mm))
        for sev,rn,short,explanation in prior['flags']:
            c=RED if sev=='CRITICAL' else ORANGE
            elements.append(Paragraph(f"<b>{'🔴' if sev=='CRITICAL' else '🟠'} {short}</b>",
                ParagraphStyle('fs',fontName=_FONT_BOLD,fontSize=9,textColor=c,leading=12)))
            if explanation:
                elements.append(Paragraph(explanation,
                    ParagraphStyle('fe',fontName=_FONT,fontSize=8,textColor=TEXT_MID,
                        leading=12,leftIndent=10,spaceAfter=3,alignment=TA_RIGHT)))

    # ── 4. ENGINEERING FINDINGS ────────────────────────────────────────────
    non_ok=[f for f in d['findings'] if f[0]!='OK']
    if non_ok:
        elements.append(Spacer(1,2*mm))
        elements.append(Paragraph("Engineering Findings",S['h2']))
        for sev,cat,short_msg,explanation in non_ok:
            c=RED if sev=='REJECT' else ORANGE
            elements.append(Paragraph(
                f"<b>{'⛔' if sev=='REJECT' else '⚠️'} [{cat}]</b> {short_msg}",
                ParagraphStyle('find',fontName=_FONT_BOLD,fontSize=9,textColor=c,leading=12,spaceAfter=1)))
            if explanation:
                elements.append(Paragraph(explanation,
                    ParagraphStyle('exp',fontName=_FONT,fontSize=8,textColor=TEXT_MID,
                        leading=12,leftIndent=12,spaceAfter=4,alignment=TA_RIGHT)))

    elements.append(HRFlowable(width=W,thickness=0.5,color=colors.HexColor('#d1d5db')))
    return elements


# ── Helpers ───────────────────────────────────────────────────────────────
def _colored_box(width, height, bg_color, content_items):
    rows=[[item] for item in content_items]
    tbl=Table(rows,colWidths=[width])
    tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),bg_color),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12)]))
    return tbl

def _info_table(rows_data, width, S):
    rows=[]
    for r in rows_data:
        l1,v1,l2,v2=r
        rows.append([Paragraph(str(l1),S['label']),Paragraph(str(v1),S['body']),
                     Paragraph(str(l2),S['label']),Paragraph(str(v2),S['body'])])
    tbl=Table(rows,colWidths=[28*mm,width/2-28*mm,28*mm,width/2-28*mm])
    tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),GREY_LIGHT),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
        ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#d1d5db'))]))
    return tbl

def _kpi_cell(label, value, color, S):
    return Table([
        [Paragraph(label,ParagraphStyle('kl',fontName=_FONT,fontSize=7,textColor=TEXT_LIGHT,leading=9))],
        [Paragraph(value,ParagraphStyle('kv',fontName=_FONT_BOLD,fontSize=14,textColor=color,leading=16))],
    ],colWidths=['100%'])

def _banner(text, fg_color, bg_color, width, S):
    p=Paragraph(text,ParagraphStyle('banner',fontName=_FONT_BOLD,fontSize=11,
        textColor=fg_color,leading=14,alignment=TA_CENTER))
    tbl=Table([[p]],colWidths=[width])
    tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),bg_color),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('BOX',(0,0),(-1,-1),1,fg_color)]))
    return tbl

def _page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(_FONT,7); canvas.setFillColor(TEXT_LIGHT)
    canvas.drawString(15*mm,12*mm,"TRS Foundation Operations Platform — Confidential")
    canvas.drawRightString(A4[0]-15*mm,12*mm,f"Page {canvas.getPageNumber()}")
    canvas.restoreState()