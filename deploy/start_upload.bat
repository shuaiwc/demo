@echo off
setlocal enabledelayedexpansion
if not exist "start_config.txt" (
    echo Error: unable to find start_config.txt
    pause
    exit /b 1
)

for /f "usebackq delims=" %%f in ("start_config.txt") do (
    if "%%f"=="test" (
        call upload_41.bat
    ) else if "%%f"=="baxi" (
        call upload_baxi.bat
    ) else if "%%f"=="america" (
        call upload_america.bat
    ) else (
        echo Unknown value: %%f
    )
)