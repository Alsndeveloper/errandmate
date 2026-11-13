@echo off
title ErrandMate - FastAPI Backend Server
color 0B
echo ==============================================================
echo                 ErrandMate Backend API Server
echo ==============================================================
echo.
echo Starting FastAPI server with Uvicorn...
echo Database: ErrandMate\ErrandMate.db
echo Web Application: http://127.0.0.1:8000/
echo Swagger API Docs: http://127.0.0.1:8000/docs
echo ReDoc Reference: http://127.0.0.1:8000/redoc
echo.
python run_server.py
pause
