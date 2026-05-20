# TRS Platform — Month + 5-Role Operational Dashboards

## Implemented

### Job Files Structure
New structure:
Company → Year → Month → Rig → Connection Type → Files

Example:
KHALDA / 2026 / 04-April / EDC 82 / TENARIS BLUE

The month is detected automatically from:
1. Start Date Time / End Date Time
2. ISO date inside the report
3. Report Date
4. Current month fallback

### Roles
The system now supports 5 roles:

- Admin
- Manager
- Engineer
- Supervisor
- Operator

Default demo users:
- admin / admin123
- manager / manager123
- engineer / engineer123
- supervisor / supervisor123
- operator / operator123

### Operator Dashboard
Operators now get a personal dashboard showing:
- My jobs
- My uploaded reports
- Analyzed jobs
- Average rerun %
- Performance score
- Recent reports and analysis

### Supervisor Dashboard
Supervisor role has a field-control workspace for:
- Team jobs
- Job reports
- Equipment status

## Notes
Existing SQLite databases are migrated automatically with `job_month` columns.
For production PostgreSQL, run the updated schema/migrations before launch.
