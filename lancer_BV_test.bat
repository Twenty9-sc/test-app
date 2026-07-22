@echo off
title BV - Portail Beraudy et Vaure
cd /d "C:\BV\app"
"C:\BV\venv\Scripts\python.exe" -m streamlit run "test.py" --server.address 0.0.0.0 --server.port 8501 --server.headless true
pause