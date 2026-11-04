@echo off
title Control Dimensional Calidad - SIGRAMA
echo =======================================================
echo Iniciando Servidor Streamlit Local...
echo =======================================================
cd /d "C:\Users\albertol\.gemini\antigravity\scratch\control-dimensional-calidad"
"C:\Users\albertol\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run app.py --server.port 8501
pause
