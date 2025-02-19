@echo off

setlocal enabledelayedexpansion

REM  设置 Git Bash 路径
set "GIT_BASH_PATH=C:\Program Files\Git\git-bash.exe"

REM 检查 Git Bash 是否安装
if not exist "%GIT_BASH_PATH%" (
    echo Error: Unable to find Git Bash, please check if GIT_BASH_PATH configuration is correct!
    pause
    exit /b 1
)
REM 检查配置文件是否存在
if not exist "upload_config_file.txt" (
    echo Error: unable to find upload_config_file.txt
    pause
    exit /b 1
)

REM 检查配置文件是否存在
if not exist "upload_config_list.txt" (
    echo Error: unable to find upload_config_list.txt
    pause
    exit /b 1
)

for /f "usebackq delims=" %%f in ("upload_config_list.txt") do (
    set "SCP_COMMAND=scp -r %%f* s41:/tmp"
    echo Executing command: !SCP_COMMAND!
    start "" "%GIT_BASH_PATH%" -c "!SCP_COMMAND!"

    timeout /t 1 /nobreak > nul
)

for /f "usebackq delims=" %%f in ("upload_config_file.txt") do (
    set "SCP_COMMAND=scp '%%f' s41:/tmp"
    echo Executing command: !SCP_COMMAND!
    start "" "%GIT_BASH_PATH%" -c "!SCP_COMMAND!"

    timeout /t 1 /nobreak > nul
)


pause

exit /b 0