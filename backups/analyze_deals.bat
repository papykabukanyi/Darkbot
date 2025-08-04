@echo off
echo Analyzing Sneaker Deals...
python analyze_deals.py --input sneaker_deals.csv --format table %*
pause
