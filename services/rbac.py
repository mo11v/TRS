"""
TRS Platform — Role Based Access Control (RBAC)
================================================
5 Roles:
  Admin       → full access
  Manager     → full operational access, no destructive admin controls unless allowed
  Engineer    → analysis, job files, equipment engineering
  Supervisor  → field supervision, team jobs, limited edits
  Operator    → own jobs/uploads, personal performance dashboard
"""

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse

ROLES = ["Admin", "Manager", "Engineer", "Supervisor", "Operator"]

PERMISSIONS: dict[str, list[str]] = {
    "dashboard":           ["Admin", "Manager", "Engineer", "Supervisor", "Operator"],

    "jobs.view":           ["Admin", "Manager", "Engineer", "Supervisor", "Operator"],
    "jobs.create":         ["Admin", "Manager", "Engineer", "Supervisor", "Operator"],
    "jobs.edit":           ["Admin", "Manager", "Engineer", "Supervisor"],
    "jobs.delete":         ["Admin", "Manager"],
    "jobs.change_status":  ["Admin", "Manager", "Engineer", "Supervisor"],

    "mtt.upload":          ["Admin", "Manager", "Engineer", "Supervisor", "Operator"],

    "analysis.view":       ["Admin", "Manager", "Engineer", "Supervisor", "Operator"],
    "analysis.export":     ["Admin", "Manager", "Engineer", "Supervisor"],

    "job_files.view":      ["Admin", "Manager", "Engineer", "Supervisor", "Operator"],
    "job_files.upload":    ["Admin", "Manager", "Engineer", "Supervisor", "Operator"],
    "job_files.delete":    ["Admin", "Manager"],

    "equipment.view":      ["Admin", "Manager", "Engineer", "Supervisor", "Operator"],
    "equipment.edit":      ["Admin", "Manager", "Engineer", "Supervisor"],
    "equipment.delete":    ["Admin", "Manager"],

    "fleet.view":          ["Admin", "Manager", "Engineer", "Supervisor"],
    "ai.view":             ["Admin", "Manager", "Engineer"],
    "ai.run":              ["Admin", "Manager", "Engineer"],
    "reports.download":    ["Admin", "Manager", "Engineer", "Supervisor"],

    "scada.view":          ["Admin", "Manager", "Engineer", "Supervisor", "Operator"],
    "scada.push":          ["Admin", "Manager", "Engineer", "Supervisor", "Operator"],

    "devices.view":        ["Admin", "Manager", "Engineer", "Supervisor", "Operator"],
    "devices.create":      ["Admin", "Manager", "Engineer"],
    "devices.edit":        ["Admin", "Manager", "Engineer", "Supervisor"],
    "devices.delete":      ["Admin"],

    "users.view":          ["Admin", "Manager"],
    "users.create":        ["Admin"],
    "users.edit":          ["Admin"],
    "users.delete":        ["Admin"],

    "settings.view":       ["Admin", "Manager"],
    "settings.edit":       ["Admin"],
}

ROLE_LEVEL = {"Admin": 5, "Manager": 4, "Engineer": 3, "Supervisor": 2, "Operator": 1, "Field Operator": 1}

ROLE_NAV = {
    "Admin":      ["dashboard", "job_files", "equipment", "jobs", "devices", "analysis", "fleet", "ai", "scada", "users", "settings"],
    "Manager":    ["dashboard", "job_files", "equipment", "jobs", "devices", "analysis", "fleet", "ai", "scada", "settings"],
    "Engineer":   ["dashboard", "job_files", "equipment", "jobs", "devices", "analysis", "fleet", "ai", "scada"],
    "Supervisor": ["dashboard", "job_files", "equipment", "jobs", "devices", "analysis", "scada"],
    "Operator":   ["dashboard", "job_files", "jobs", "analysis", "scada"],
    "Field Operator": ["dashboard", "job_files", "jobs", "analysis", "scada"],
}


class RBAC:
    @staticmethod
    def _role(user: dict) -> str:
        role = (user or {}).get("role", "Operator")
        return "Operator" if role == "Field Operator" else role

    @staticmethod
    def can(user: dict, permission: str) -> bool:
        if not user:
            return False
        return RBAC._role(user) in PERMISSIONS.get(permission, [])

    @staticmethod
    def require(request: Request, permission: str, session_store: dict = None):
        token = request.cookies.get("trs_session") or request.cookies.get("jam_session")
        if not token or not session_store or token not in session_store:
            return None, RedirectResponse("/login", status_code=303)
        sess = session_store.get(token)
        if not sess:
            return None, RedirectResponse("/login", status_code=303)
        from datetime import datetime
        exp = datetime.fromisoformat(sess.get("expires", "1970-01-01"))
        if datetime.now() > exp:
            session_store.pop(token, None)
            return None, RedirectResponse("/login", status_code=303)
        user = sess.get("user")
        if not user:
            return None, RedirectResponse("/login", status_code=303)
        if not RBAC.can(user, permission):
            return None, HTMLResponse(_forbidden_page(user, permission), status_code=403)
        return user, None

    @staticmethod
    def nav_items(user: dict) -> list[str]:
        if not user:
            return []
        return ROLE_NAV.get(RBAC._role(user), ["dashboard"])

    @staticmethod
    def role_level(role: str) -> int:
        return ROLE_LEVEL.get("Operator" if role == "Field Operator" else role, 0)

    @staticmethod
    def is_admin(user: dict) -> bool:
        return user and RBAC._role(user) == "Admin"

    @staticmethod
    def is_management(user: dict) -> bool:
        return user and RBAC._role(user) in ("Admin", "Manager")

    @staticmethod
    def is_engineer_plus(user: dict) -> bool:
        return user and RBAC._role(user) in ("Admin", "Manager", "Engineer")

    @staticmethod
    def is_supervisor_plus(user: dict) -> bool:
        return user and RBAC._role(user) in ("Admin", "Manager", "Engineer", "Supervisor")

    @staticmethod
    def is_operator(user: dict) -> bool:
        return user and RBAC._role(user) == "Operator"


def _forbidden_page(user: dict, permission: str) -> str:
    role = (user or {}).get("role", "Operator")
    name = (user or {}).get("full_name") or (user or {}).get("username", "")
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Access Denied — TRS Platform</title>
<style>
body{{font-family:sans-serif;background:#050d1a;color:#e2e8f0;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;flex-direction:column;gap:16px}}
.icon{{font-size:64px}} h1{{font-size:28px;font-weight:800;color:#ef4444;margin:0}}
p{{color:#94a3b8;text-align:center;max-width:420px;line-height:1.6}}
.role{{display:inline-block;padding:4px 12px;background:rgba(20,184,166,.15);color:#14b8a6;border-radius:20px;font-size:12px;font-weight:600}}
.btn{{padding:10px 20px;background:#3b82f6;color:#fff;border:none;border-radius:8px;font-size:14px;cursor:pointer;text-decoration:none;font-weight:600}}
</style></head>
<body><div class="icon">🔒</div><h1>Access Denied</h1>
<p>Hey <strong>{name}</strong>, your role <span class="role">{role}</span> doesn't have access to <strong>{permission}</strong>.<br>Contact your administrator if you need access.</p>
<a href="/" class="btn">← Back to Dashboard</a></body></html>"""


rbac = RBAC()
