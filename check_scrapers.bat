@echo off
echo Running scraper health check...
cd C:\Users\lovingtracktor\Desktop\Darkbot
C:\Users\lovingtracktor\Desktop\Darkbot\.venv\Scripts\python.exe scripts\check_scrapers.py %*
pause
