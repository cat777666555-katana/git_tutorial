@echo off

cd /d %~dp0
pushd ..\..\scripts
for /f "usebackq tokens=1,2 delims==" %%A in (`powershell -NoProfile -ExecutionPolicy Bypass -File .\env_loader.ps1 ..\.env`) do (
    set "%%A=%%B"
)
popd



rem set DOCS_PATH=%~1
set DOCS_PATH=..\..\docs


if "%DOCS_PATH%"=="" (
    echo 使用方法: build.bat ^<docsフォルダのパス^>
    echo 例: build.bat docs
    pause
    exit /b
)

powershell -ExecutionPolicy Bypass -File "%~dp0site.ps1" "%DOCS_PATH%"
move plantuml-*.png .\site\
pause
