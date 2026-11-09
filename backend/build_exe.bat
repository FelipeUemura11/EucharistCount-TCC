@echo off
rem Gera dist\EucharistCount.exe: um arquivo so, com dashboard, modelo, configuracao e camera dentro.
rem Precisa de: Windows, Python 3.11 (comando "py -3.11") e Node.js com npm.
rem Uso: dois cliques neste arquivo, ou "build_exe.bat" de dentro de backend\.
setlocal
cd /d "%~dp0"

echo.
echo [1/4] Compilando o dashboard (frontend)...
pushd ..\frontend
call npm ci
if errorlevel 1 goto erro_front
call npm run build
if errorlevel 1 goto erro_front
popd

echo.
echo [2/4] Preparando o ambiente de build (.venv-build, separado do .venv de desenvolvimento)...
if not exist ".venv-build\Scripts\python.exe" (
    py -3.11 -m venv .venv-build
    if errorlevel 1 goto erro
)
call ".venv-build\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto erro
pip install -r requirements-build.txt
if errorlevel 1 goto erro

echo.
echo [3/4] Conferindo o modelo de deteccao...
if not exist "modelos\yolo11n.onnx" (
    python -m scripts.preparar_modelo --modelo yolo11n --imgsz 640
    if errorlevel 1 goto erro
)

echo.
echo [4/4] Gerando o executavel (demora alguns minutos)...
rem A fonte da camera (CAMERA_FONTE no .env) vai dentro do .exe.
if not exist ".env" (
    echo Falta o arquivo backend\.env com CAMERA_FONTE=rtsp://... da camera da paroquia.
    echo Copie o .env.example para .env, preencha o link e rode de novo.
    goto erro
)
pyinstaller eucharist_count.spec --noconfirm --clean
if errorlevel 1 goto erro

echo.
echo Pronto: %~dp0dist\EucharistCount.exe
echo A camera do .env ja vai dentro do .exe: e so entregar o arquivo.
pause
exit /b 0

:erro_front
popd
:erro
echo.
echo Falhou no passo acima. Leia a mensagem de erro, corrija e rode de novo.
pause
exit /b 1
