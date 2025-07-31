@echo off
echo Running the Multi-Source Profit Finder...
cd C:\Users\lovingtracktor\Desktop\Darkbot

:: Set Python executable path
set PYTHON_PATH=C:\Users\lovingtracktor\Desktop\Darkbot\.venv\Scripts\python.exe

:: Create logs directory if it doesn't exist
if not exist logs mkdir logs

:: Set timestamp for log file
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set datetime=%%a
set log_date=%datetime:~0,8%
set log_time=%datetime:~8,6%
set LOGFILE=logs\profit_finder_%log_date%_%log_time%.log

:: Run the enhanced profit finder script
echo Running multi-source profit finder... (This may take several minutes)
%PYTHON_PATH% multi_source_profit_finder.py > %LOGFILE% 2>&1

echo Test completed.
echo Log saved to %LOGFILE%
echo.

:: Check if results file exists before trying to display results
if exist profit_analysis.json (
    echo Displaying top profitable items:
    echo --------------------------------------
    %PYTHON_PATH% -c "import json; import os; filename='profit_analysis.json'; print(f'Analysis from {filename}:'); data=json.load(open(filename)) if os.path.exists(filename) else {'profitable_products':[]}; products=data.get('profitable_products', [])[:10]; print(f'Analysis Date: {data.get(\"analysis_date\", \"N/A\")}\n'); [print(f'{i+1}. {p.get(\"title\", \"Unknown\")} ({p.get(\"source\", \"Unknown\")}) - ${p.get(\"profit_amount\", 0):.2f} ({p.get(\"profit_percentage\", 0):.1f}%)') for i,p in enumerate(products)] if products else print('No profitable products found.')"
) else (
    echo Results file profit_analysis.json was not created.
    echo Check the log file for errors.
)

pause
