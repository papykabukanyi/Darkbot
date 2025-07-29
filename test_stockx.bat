@echo off
echo Running the StockX scraper test...
cd C:\Users\lovingtracktor\Desktop\Darkbot
C:\Users\lovingtracktor\Desktop\Darkbot\.venv\Scripts\python.exe test_stockx.py > stockx_test_results.txt
echo Test completed. Results saved to stockx_test_results.txt
echo.
type stockx_test_results.txt
pause
