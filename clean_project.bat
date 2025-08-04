@echo off
echo Cleaning up unnecessary files...

:: First, make sure we have a backup directory
if not exist backups mkdir backups

:: Move unnecessary scripts to backup directory
move analyze_deals.bat backups\
move analyze_deals.py backups\
move auto_start.bat backups\
move bot_test.py backups\
move check_scrapers.bat backups\
move check_system.bat backups\
move check_system.sh backups\
move cleanup.bat backups\
move config_complete.bat backups\
move debug_scraping.py backups\
move docker-compose.yml backups\
move docker-entrypoint.sh backups\
move docker-healthcheck.sh backups\
move Dockerfile backups\
move docker_test.py backups\
move enhanced_stockx_profit_finder.py backups\
move fix-docker-cmd.bat backups\
move fix_r2storage.bat backups\
move fix_r2storage.py backups\
move main.py backups\
move main.py.new backups\
move main_improved.py backups\
move main_restored.py backups\
move mock_data.json backups\
move mock_data.py backups\
move monitor_darkbot.bat backups\
move monitor_darkbot.py backups\
move multi_source_profit_finder.py backups\
move notifications.py backups\
move proxy_manager.bat backups\
move proxy_manager.py backups\
move proxy_test.py backups\
move quick_email_test.py backups\
move railway.json backups\
move run_all_tests.bat backups\
move run_bot.bat backups\
move run_bot_prod.bat backups\
move run_continuous.bat backups\
move run_darkbot.bat backups\
move run_fixed_bot.bat backups\
move run_improved_bot.bat backups\
move run_profit_finder.bat backups\
move run_simple_bot.bat backups\
move run_simplified.bat backups\
move run_undefeated.bat backups\
move run_with_undefeated.py backups\
move run_working_scrapers.bat backups\
move scraper_fix.py backups\
move setup_autostart.bat backups\
move simple_runner.py backups\
move simplified_config.py backups\
move test.py backups\
move test_adidas_scraper.bat backups\
move test_adidas_scraper.py backups\
move test_credentials.py backups\
move test_deal_intelligence.py backups\
move test_email.py backups\
move test_email_notification.py backups\
move test_email_notifications.bat backups\
move test_email_now.bat backups\
move test_fallback_scraper.py backups\
move test_fixes.bat backups\
move test_html_unescape.bat backups\
move test_html_unescape.py backups\
move test_html_unescaping.bat backups\
move test_html_unescaping.py backups\
move test_imports.py backups\
move test_notification.py backups\
move test_output.py backups\
move test_sale_urls.bat backups\
move test_sale_urls.py backups\
move test_scheduling.py backups\
move test_scrapers.bat backups\
move test_scrapers.py backups\
move test_stockx.bat backups\
move test_stockx.py backups\
move test_undefeated.py backups\
move test_undefeated_file.py backups\
move test_undefeated_scraper.bat backups\
move test_undefeated_scraper.py backups\
move test_webdriver.py backups\
move test_webdriver_file.py backups\
move update_fix_r2storage.bat backups\
move verify_credentials.py backups\
move verify_fixes.bat backups\
move verify_fixes.py backups\
move verify_sites.bat backups\
move view_deals.bat backups\
move view_deals.py backups\

:: Move unnecessary markdown files
move DARKBOT_FIX.md backups\
move FIXES.md backups\
move FIXES_SUMMARY.md backups\
move HTML_UNESCAPING_FIX.md backups\
move IMPROVEMENTS.md backups\
move PROFIT_FINDER_AND_MONITORING.md backups\
move PROXY_CONFIGURATION.md backups\
move RAILWAY_DEPLOYMENT.md backups\
move README_IMPROVED.md backups\
move STOCKX_SCRAPER_UPDATE.md backups\
move STREAMLINED.md backups\
move UPGRADE_INFO.md backups\
move README-SIMPLIFIED.txt backups\

:: Move unnecessary data files
move verification_results.txt backups\
move undefeated_test_output.txt backups\
move webdriver_test_output.txt backups\
move stockx_test_results.txt backups\
move sneaker_deals.csv backups\
move sneaker_deals.db backups\

:: Move unnecessary directories with content
move tests backups\
move docs backups\
move scripts backups\
move temp backups\
move test_data backups\
move storage backups\

@echo off
echo Cleaning up SneakerBot project...
echo ===============================

REM Create backups directory if it doesn't exist
if not exist backups mkdir backups

REM Copy config_fixed.py to config.py
echo Updating config.py...
copy config_fixed.py config.py

REM Clean up config directory
if exist config mkdir backups\config
move config\sites.py backups\config\
move config\__init__.py backups\config\
move config\__pycache__ backups\config\

REM Clean up scrapers directory
if exist scrapers mkdir backups\scrapers
move scrapers\adidas.py backups\scrapers\
move scrapers\champssports.py backups\scrapers\
move scrapers\factory.py backups\scrapers\
move scrapers\fallback_scraper.py backups\scrapers\
move scrapers\footlocker.py backups\scrapers\
move scrapers\idsports.py backups\scrapers\
move scrapers\sneakers.py backups\scrapers\
move scrapers\stockx.py backups\scrapers\
move scrapers\undefeated.py backups\scrapers\
move scrapers\base_scraper.py.new backups\scrapers\
move scrapers\base_scraper.py.simplified backups\scrapers\
move scrapers\__pycache__ backups\scrapers\

REM Clean up utils directory
if exist utils mkdir backups\utils
move utils\captcha_handler.py backups\utils\
move utils\fallback_proxy.py backups\utils\
move utils\market_data.py backups\utils\
move utils\price_comparison.py backups\utils\
move utils\proxy_manager.py backups\utils\
move utils\rate_limiting.py backups\utils\
move utils\site_verifier.py backups\utils\
move utils\verify_sites.py backups\utils\
move utils\webdriver.py backups\utils\
move utils\__pycache__ backups\utils\

REM Move unused batch files to backups
mkdir backups\batch_files
move analyze_deals.bat backups\batch_files\
move auto_start.bat backups\batch_files\
move check_scrapers.bat backups\batch_files\
move check_system.bat backups\batch_files\
move cleanup.bat backups\batch_files\
move config_complete.bat backups\batch_files\
move fix-docker-cmd.bat backups\batch_files\
move fix_r2storage.bat backups\batch_files\
move monitor_darkbot.bat backups\batch_files\
move proxy_manager.bat backups\batch_files\
move run_all_tests.bat backups\batch_files\
move run_bot.bat backups\batch_files\
move run_bot_prod.bat backups\batch_files\
move run_continuous.bat backups\batch_files\
move run_darkbot.bat backups\batch_files\
move run_fixed_bot.bat backups\batch_files\
move run_improved_bot.bat backups\batch_files\
move run_profit_finder.bat backups\batch_files\
move run_simple_bot.bat backups\batch_files\
move run_simplified.bat backups\batch_files\
move run_undefeated.bat backups\batch_files\
move run_working_scrapers.bat backups\batch_files\
move setup_autostart.bat backups\batch_files\
move test_adidas_scraper.bat backups\batch_files\
move test_email_notifications.bat backups\batch_files\
move test_email_now.bat backups\batch_files\
move test_fixes.bat backups\batch_files\
move test_html_unescape.bat backups\batch_files\
move test_html_unescaping.bat backups\batch_files\
move test_sale_urls.bat backups\batch_files\
move test_scrapers.bat backups\batch_files\
move test_stockx.bat backups\batch_files\
move test_undefeated_scraper.bat backups\batch_files\
move update_fix_r2storage.bat backups\batch_files\
move verify_fixes.bat backups\batch_files\
move verify_sites.bat backups\batch_files\
move view_deals.bat backups\batch_files\

REM Move unused Python files to backups
mkdir backups\python_files
move analyze_deals.py backups\python_files\
move bot_test.py backups\python_files\
move check_system.sh backups\python_files\
move debug_scraping.py backups\python_files\
move docker_test.py backups\python_files\
move enhanced_stockx_profit_finder.py backups\python_files\
move fix_r2storage.py backups\python_files\
move main.py backups\python_files\
move main.py.new backups\python_files\
move main_improved.py backups\python_files\
move main_restored.py backups\python_files\
move mock_data.py backups\python_files\
move monitor_darkbot.py backups\python_files\
move multi_source_profit_finder.py backups\python_files\
move notifications.py backups\python_files\
move proxy_manager.py backups\python_files\
move proxy_test.py backups\python_files\
move quick_email_test.py backups\python_files\
move run_with_undefeated.py backups\python_files\
move scraper_fix.py backups\python_files\
move simple_runner.py backups\python_files\
move simplified_config.py backups\python_files\
move storage.py backups\python_files\
move test.py backups\python_files\
move test_adidas_scraper.py backups\python_files\
move test_credentials.py backups\python_files\
move test_deal_intelligence.py backups\python_files\
move test_email.py backups\python_files\
move test_email_notification.py backups\python_files\
move test_fallback_scraper.py backups\python_files\
move test_html_unescape.py backups\python_files\
move test_html_unescaping.py backups\python_files\
move test_imports.py backups\python_files\
move test_notification.py backups\python_files\
move test_output.py backups\python_files\
move test_sale_urls.py backups\python_files\
move test_scheduling.py backups\python_files\
move test_scrapers.py backups\python_files\
move test_stockx.py backups\python_files\
move test_undefeated.py backups\python_files\
move test_undefeated_file.py backups\python_files\
move test_webdriver.py backups\python_files\
move test_webdriver_file.py backups\python_files\
move verify_credentials.py backups\python_files\
move verify_fixes.py backups\python_files\
move view_deals.py backups\python_files\

REM Move unused markdown files to backups
mkdir backups\documentation
move DARKBOT_FIX.md backups\documentation\
move FIXES.md backups\documentation\
move FIXES_SUMMARY.md backups\documentation\
move HTML_UNESCAPING_FIX.md backups\documentation\
move IMPROVEMENTS.md backups\documentation\
move PROFIT_FINDER_AND_MONITORING.md backups\documentation\
move PROXY_CONFIGURATION.md backups\documentation\
move RAILWAY_DEPLOYMENT.md backups\documentation\
move README.md backups\documentation\
move README-SIMPLIFIED.txt backups\documentation\
move README_IMPROVED.md backups\documentation\
move STOCKX_SCRAPER_UPDATE.md backups\documentation\
move STREAMLINED.md backups\documentation\
move UPGRADE_INFO.md backups\documentation\

REM Move other files to backups
mkdir backups\other
move .dockerignore backups\other\
move .env backups\other\
move .env.sample backups\other\
move docker-compose.yml backups\other\
move docker-entrypoint.sh backups\other\
move docker-healthcheck.sh backups\other\
move Dockerfile backups\other\
move mock_data.json backups\other\
move Procfile backups\other\
move proxies.json backups\other\
move railway.json backups\other\
move requirements-streamlined.txt backups\other\
move sneaker_deals.csv backups\other\
move sneaker_deals.db backups\other\
move stockx_test_results.txt backups\other\
move undefeated_test_output.txt backups\other\
move verification_results.txt backups\other\
move webdriver_test_output.txt backups\other\

REM Move config_new.py after copying to config.py
move config_new.py backups\

echo Clean up complete. Unnecessary files moved to backups directory.
