"""
TRS AI Insights Service — Phase 5
كشف الشذوذ وتحليل الأداء بدون ML libraries
يستخدم: Z-score, IQR, Moving Average, Trend Analysis

لا يحتاج numpy أو sklearn — pure Python فقط
"""

import math
import json
import logging
from datetime import datetime
from database.db import q1, qa, qx

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
#  Statistics helpers — pure Python
# ══════════════════════════════════════════════════════════════

def _mean(values: list[float]) -> float:
    v = [x for x in values if x is not None]
    return sum(v) / len(v) if v else 0.0


def _std(values: list[float]) -> float:
    v = [x for x in values if x is not None]
    if len(v) < 2:
        return 0.0
    m = _mean(v)
    variance = sum((x - m) ** 2 for x in v) / (len(v) - 1)
    return math.sqrt(variance)


def _median(values: list[float]) -> float:
    v = sorted(x for x in values if x is not None)
    if not v:
        return 0.0
    n = len(v)
    mid = n // 2
    return v[mid] if n % 2 else (v[mid - 1] + v[mid]) / 2


def _percentile(values: list[float], p: float) -> float:
    v = sorted(x for x in values if x is not None)
    if not v:
        return 0.0
    idx = (len(v) - 1) * p / 100
    lo, hi = int(idx), min(int(idx) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (idx - lo)


def _moving_avg(values: list[float], window: int = 5) -> list[float]:
    result = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        chunk = [v for v in values[start:i + 1] if v is not None]
        result.append(sum(chunk) / len(chunk) if chunk else None)
    return result


def _trend_slope(values: list[float]) -> float:
    """Linear regression slope — positive = increasing, negative = decreasing"""
    v = [(i, x) for i, x in enumerate(values) if x is not None]
    if len(v) < 2:
        return 0.0
    n = len(v)
    xs = [p[0] for p in v]
    ys = [p[1] for p in v]
    x_mean = _mean(xs)
    y_mean = _mean(ys)
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    den = sum((x - x_mean) ** 2 for x in xs)
    return num / den if den else 0.0


# ══════════════════════════════════════════════════════════════
#  Anomaly Detection
# ══════════════════════════════════════════════════════════════

def detect_anomalies(readings: list[dict], param: str,
                     z_threshold: float = 2.5) -> list[dict]:
    """
    Z-score anomaly detection على بارامتر معين
    يرجع القراءات الشاذة مع score وسبب
    """
    values = [r.get(param) for r in readings if r.get(param) is not None]
    if len(values) < 5:
        return []

    mu  = _mean(values)
    sig = _std(values)
    if sig == 0:
        return []

    # IQR bounds
    q1v = _percentile(values, 25)
    q3v = _percentile(values, 75)
    iqr = q3v - q1v
    lo  = q1v - 1.5 * iqr
    hi  = q3v + 1.5 * iqr

    anomalies = []
    for i, r in enumerate(readings):
        v = r.get(param)
        if v is None:
            continue
        z = abs((v - mu) / sig)
        if z > z_threshold or v < lo or v > hi:
            anomalies.append({
                "index":     i,
                "ts":        r.get("ts", ""),
                "value":     v,
                "z_score":   round(z, 2),
                "mean":      round(mu, 2),
                "std":       round(sig, 2),
                "reason":    "spike" if v > hi else "drop",
                "severity":  "Critical" if z > 4 else "Warning",
                "param":     param,
            })
    return anomalies


def detect_all_anomalies(readings: list[dict]) -> dict:
    """يكشف الشذوذ في كل البارامترات"""
    params = ["torque", "turns", "rpm", "pressure", "temperature", "weight"]
    result = {}
    total  = 0
    for p in params:
        anom = detect_anomalies(readings, p)
        if anom:
            result[p] = anom
            total += len(anom)
    return {"anomalies": result, "total": total}


# ══════════════════════════════════════════════════════════════
#  Job Performance Analysis
# ══════════════════════════════════════════════════════════════

def analyze_job(job_id: int) -> dict:
    """تحليل شامل لأداء جوب معين"""
    readings = qa("""
        SELECT * FROM historian_readings
        WHERE job_id=? ORDER BY ts ASC
    """, (job_id,))

    if not readings:
        return {"job_id": job_id, "status": "no_data"}

    job   = q1("SELECT * FROM jobs WHERE id=?", (job_id,))
    stats = q1("SELECT * FROM job_summary_stats WHERE job_id=?", (job_id,))

    torques   = [r["torque"]   for r in readings if r["torque"]   is not None]
    turns     = [r["turns"]    for r in readings if r["turns"]    is not None]
    rpms      = [r["rpm"]      for r in readings if r["rpm"]      is not None]
    pressures = [r["pressure"] for r in readings if r["pressure"] is not None]

    # Torque trend
    torque_slope = _trend_slope(torques)
    torque_trend = "increasing" if torque_slope > 5 else "decreasing" if torque_slope < -5 else "stable"

    # Stability score (lower CV = more stable)
    def cv(vals):
        m = _mean(vals)
        return (_std(vals) / m * 100) if m else 0

    stability_score = max(0, 100 - cv(torques) * 2) if torques else 0

    # Anomalies
    anom = detect_all_anomalies(readings)

    # Performance score (0-100)
    perf = _compute_performance_score(
        stability=stability_score,
        anomaly_count=anom["total"],
        reading_count=len(readings),
        torque_peak=max(torques) if torques else 0,
        torque_avg=_mean(torques),
    )

    # Insights text
    insights = _generate_insights(
        torques, turns, rpms, pressures,
        torque_trend, anom, stability_score, job
    )

    return {
        "job_id":          job_id,
        "job_number":      job["job_number"] if job else "",
        "status":          "analyzed",
        "reading_count":   len(readings),
        "torque": {
            "mean":    round(_mean(torques), 2),
            "std":     round(_std(torques), 2),
            "min":     round(min(torques), 2)  if torques else 0,
            "max":     round(max(torques), 2)  if torques else 0,
            "median":  round(_median(torques), 2),
            "trend":   torque_trend,
            "slope":   round(torque_slope, 4),
            "cv_pct":  round(cv(torques), 1),
        },
        "turns": {
            "total":   round(sum(turns), 2) if turns else 0,
            "mean":    round(_mean(turns), 2),
        },
        "rpm": {
            "mean":    round(_mean(rpms), 2),
            "max":     round(max(rpms), 2) if rpms else 0,
        },
        "stability_score": round(stability_score, 1),
        "performance_score": round(perf, 1),
        "anomaly_count":   anom["total"],
        "anomalies":       anom["anomalies"],
        "insights":        insights,
        "analyzed_at":     datetime.now().isoformat(),
    }


def _compute_performance_score(stability, anomaly_count, reading_count,
                                torque_peak, torque_avg) -> float:
    score = 100.0
    # Penalize for anomalies
    score -= min(30, anomaly_count * 3)
    # Reward for stability
    score = score * 0.6 + stability * 0.4
    # Penalize for very low readings
    if reading_count < 10:
        score *= 0.7
    return max(0, min(100, score))


def _generate_insights(torques, turns, rpms, pressures,
                       trend, anom, stability, job) -> list[dict]:
    insights = []

    # Torque trend insight
    if trend == "increasing":
        insights.append({
            "type":    "warning",
            "icon":    "📈",
            "title":   "Torque في ارتفاع مستمر",
            "detail":  "قراءات الـ Torque في ارتفاع تدريجي — تحقق من حالة الجهاز",
        })
    elif trend == "decreasing" and torques:
        insights.append({
            "type":    "info",
            "icon":    "📉",
            "title":   "Torque في انخفاض",
            "detail":  "قراءات الـ Torque تنخفض — قد يكون الجوب يقترب من الاكتمال",
        })

    # Stability
    if stability < 40:
        insights.append({
            "type":    "critical",
            "icon":    "⚡",
            "title":   "تذبذب عالي في القراءات",
            "detail":  f"معامل التباين {100-stability:.0f}% — القراءات غير مستقرة، تحقق من الاتصالات",
        })
    elif stability > 80:
        insights.append({
            "type":    "success",
            "icon":    "✅",
            "title":   "أداء مستقر",
            "detail":  f"معامل الاستقرار {stability:.0f}% — الجهاز يعمل بانتظام",
        })

    # Anomalies
    total_anom = anom["total"]
    if total_anom > 10:
        insights.append({
            "type":    "critical",
            "icon":    "🔴",
            "title":   f"تحذير: {total_anom} قراءة شاذة",
            "detail":  "عدد كبير من القراءات خارج النطاق الطبيعي — يُنصح بمراجعة البيانات",
        })
    elif total_anom > 3:
        insights.append({
            "type":    "warning",
            "icon":    "🟡",
            "title":   f"{total_anom} قراءة شاذة",
            "detail":  "بعض القراءات خارج النطاق المتوقع — تابع الوضع",
        })
    elif total_anom == 0 and torques:
        insights.append({
            "type":    "success",
            "icon":    "🟢",
            "title":   "لا توجد شذوذات",
            "detail":  "كل القراءات ضمن النطاق الطبيعي",
        })

    # RPM insight
    if rpms and _mean(rpms) > 80:
        insights.append({
            "type":    "warning",
            "icon":    "🌀",
            "title":   "RPM مرتفع",
            "detail":  f"متوسط RPM = {_mean(rpms):.1f} — تحقق من حدود الجهاز",
        })

    # Pressure
    if pressures and max(pressures) > 300:
        insights.append({
            "type":    "warning",
            "icon":    "💧",
            "title":   "ضغط مرتفع",
            "detail":  f"أعلى ضغط = {max(pressures):.1f} PSI",
        })

    return insights


# ══════════════════════════════════════════════════════════════
#  Cross-job comparison insights
# ══════════════════════════════════════════════════════════════

def compare_job_performance(job_ids: list[int]) -> list[dict]:
    """يقارن أداء عدة جوبات ويرتبهم"""
    results = []
    for jid in job_ids:
        analysis = analyze_job(jid)
        if analysis.get("status") == "no_data":
            continue
        results.append({
            "job_id":            jid,
            "job_number":        analysis["job_number"],
            "performance_score": analysis["performance_score"],
            "stability_score":   analysis["stability_score"],
            "anomaly_count":     analysis["anomaly_count"],
            "reading_count":     analysis["reading_count"],
            "torque_avg":        analysis["torque"]["mean"],
            "torque_max":        analysis["torque"]["max"],
            "torque_trend":      analysis["torque"]["trend"],
        })
    results.sort(key=lambda x: x["performance_score"], reverse=True)
    return results


# ══════════════════════════════════════════════════════════════
#  Store & retrieve analysis results
# ══════════════════════════════════════════════════════════════

def save_analysis(job_id: int, result: dict):
    """يحفظ نتيجة التحليل في الـ DB"""
    qx("""
        INSERT INTO job_ai_insights
            (job_id, performance_score, stability_score, anomaly_count,
             torque_trend, insights_json, analyzed_at)
        VALUES (?,?,?,?,?,?,datetime('now'))
        ON CONFLICT(job_id) DO UPDATE SET
            performance_score=excluded.performance_score,
            stability_score=excluded.stability_score,
            anomaly_count=excluded.anomaly_count,
            torque_trend=excluded.torque_trend,
            insights_json=excluded.insights_json,
            analyzed_at=datetime('now')
    """, (
        job_id,
        result.get("performance_score", 0),
        result.get("stability_score", 0),
        result.get("anomaly_count", 0),
        result.get("torque", {}).get("trend", "stable"),
        json.dumps(result.get("insights", []), ensure_ascii=False),
    ))


def get_saved_analysis(job_id: int) -> dict | None:
    return q1("SELECT * FROM job_ai_insights WHERE job_id=?", (job_id,))


def get_fleet_insights() -> dict:
    """نظرة AI على كل الأسطول"""
    all_insights = qa("""
        SELECT jai.*, j.job_number, j.customer, j.status,
               d.code device_code
        FROM job_ai_insights jai
        JOIN jobs j ON j.id=jai.job_id
        LEFT JOIN devices d ON d.id=j.assigned_device_id
        ORDER BY jai.performance_score DESC
    """)

    if not all_insights:
        return {"status": "no_data", "insights": []}

    scores = [r["performance_score"] for r in all_insights]
    fleet_avg = _mean(scores)

    critical = [r for r in all_insights if r["performance_score"] < 40]
    excellent = [r for r in all_insights if r["performance_score"] >= 80]
    high_anom = [r for r in all_insights if r["anomaly_count"] > 5]

    return {
        "status":        "ok",
        "fleet_avg_score": round(fleet_avg, 1),
        "total_analyzed": len(all_insights),
        "excellent":     len(excellent),
        "critical":      len(critical),
        "high_anomaly":  len(high_anom),
        "top_performer": all_insights[0] if all_insights else None,
        "needs_attention": critical[:3],
        "all":           all_insights,
    }
