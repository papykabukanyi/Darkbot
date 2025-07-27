@echo off
echo ===== DARKBOT SNEAKER SCRAPER =====
echo Applying scraper fix...
python scraper_fix.py
echo Running bot with single site...
python main.py --sites sneakers --verbose

echo Scraping complete! Check results above.
pause
