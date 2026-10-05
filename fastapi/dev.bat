@echo off
cd /d %~dp0

if not exist ".venv\Scripts\python.exe" (
  echo [error] 未找到虚拟环境 fastapi\.venv
  echo 请先执行: python -m venv .venv
  exit /b 1
)

echo [info] 安装/更新依赖...
".venv\Scripts\python.exe" -m pip install -r requirements.txt -q
if errorlevel 1 exit /b 1

echo [info] 启动后端 http://127.0.0.1:8000
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
