@echo off
cd /d "C:\dev\deoprediction"
call ".venv\Scripts\activate.bat"
python -m app.scripts.update_football_daily --days 14 --start-offset -1 >> "C:\dev\deoprediction\logs\football_daily_update.log" 2>&1
