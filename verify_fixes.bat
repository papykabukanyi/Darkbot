@echo off
echo Running verification script...
cd C:\Users\lovingtracktor\Desktop\Darkbot
C:\Users\lovingtracktor\Desktop\Darkbot\.venv\Scripts\python.exe verify_fixes.py > verification_results.txt 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Verification completed successfully.
) else (
    echo Verification failed with error code %ERRORLEVEL%.
)
echo Check verification_results.txt for details.
notepad verification_results.txt
pause
