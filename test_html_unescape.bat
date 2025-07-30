@echo off
echo Testing HTML unescaping functionality...
cd C:\Users\lovingtracktor\Desktop\Darkbot
C:\Users\lovingtracktor\Desktop\Darkbot\.venv\Scripts\python.exe test_html_unescape.py > html_unescape_test_results.txt
echo Test completed. Results saved to html_unescape_test_results.txt
echo.
type html_unescape_test_results.txt
pause
