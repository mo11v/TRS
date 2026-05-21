# Run this PowerShell script as the Windows user that owns the Google OAuth token.
# It schedules a daily TRS Google Drive backup at 02:00 AM.
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = "python"
$Script = Join-Path $ProjectDir "scripts\google_drive_backup.py"
$Action = New-ScheduledTaskAction -Execute $Python -Argument "`"$Script`" --once" -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "TRS Google Drive Daily Backup" -Action $Action -Trigger $Trigger -Settings $Settings -Force
Write-Host "TRS Google Drive Daily Backup task installed."
