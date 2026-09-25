@echo off
setlocal
cd /d "%~dp0"
title AURION ONE PC v3
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\bootstrap.ps1"
if errorlevel 1 pause
