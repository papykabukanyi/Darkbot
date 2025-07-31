@echo off
echo Running the Enhanced StockX Profit Finder...
cd C:\Users\lovingtracktor\Desktop\Darkbot

:: Set Python executable path
set PYTHON_PATH=C:\Users\lovingtracktor\Desktop\Darkbot\.venv\Scripts\python.exe

:: Create logs directory if it doesn't exist
if not exist logs mkdir logs

:: Set timestamp for log file
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set datetime=%%a
set log_date=%datetime:~0,8%
set log_time=%datetime:~8,6%
set LOGFILE=logs\stockx_profit_finder_%log_date%_%log_time%.log

:: Run the enhanced profit finder script
echo Running enhanced profit finder... (This may take several minutes)
%PYTHON_PATH% enhanced_stockx_profit_finder.py > %LOGFILE% 2>&1

echo Test completed. Results saved to stockx_profit_analysis.json
echo Log saved to %LOGFILE%
echo.
echo Displaying top 10 profitable sneakers:
echo --------------------------------------
%PYTHON_PATH% -c "import json; data=json.load(open('stockx_profit_analysis.json')); products=data.get('profitable_products', [])[:10]; print(f'Analysis Date: {data.get(\"analysis_date\")}\n'); [print(f'{i+1}. {p[\"title\"]} - ${p[\"profit_amount\"]:.2f} ({p[\"profit_percentage\"]:.1f}%)') for i,p in enumerate(products)]"
pause
