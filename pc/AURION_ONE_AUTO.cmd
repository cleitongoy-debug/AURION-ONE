@echo off
setlocal EnableExtensions EnableDelayedExpansion
title AURION ONE - AUTO CONFIG
cd /d "%~dp0"
if not exist logs mkdir logs
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0aurion_autoconfig.ps1"
pause
