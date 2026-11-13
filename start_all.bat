@echo off
title ErrandMate - Full Platform Launcher
echo ==============================================================
echo           ErrandMate Full Platform (Server + Desktop)
echo ==============================================================
echo.
echo 1. Launching FastAPI Backend Server in background...
start "ErrandMate Server" cmd /k "run_server.bat"
echo 2. Launching Desktop GUI Client...
start "ErrandMate Desktop" cmd /k "run_desktop.bat"
echo.
echo Both services have been launched!
timeout /t 3 >nul
