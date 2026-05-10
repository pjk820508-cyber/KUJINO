@echo off
chcp 65001 > nul
title KUJINO - EXE 빌드

echo ========================================
echo   KUJINO - EXE 자동 빌드
echo ========================================
echo.

REM 1. Python 설치 확인
echo [1/4] Python 설치 확인 중...
python --version > nul 2>&1
if errorlevel 1 (
    echo.
    echo [오류] Python이 설치되어 있지 않습니다!
    echo.
    echo 해결 방법:
    echo   1. https://www.python.org/downloads/ 에서 Python 다운로드
    echo   2. 설치 시 "Add Python to PATH" 체크박스 반드시 선택
    echo   3. 설치 후 이 배치 파일을 다시 실행
    echo.
    pause
    exit /b 1
)
echo    OK
echo.

REM 2. 필요한 라이브러리 설치
echo [2/4] PyQt5, pygame, PyInstaller 설치 중... ^(처음 한 번만 시간 걸립니다^)
python -m pip install --upgrade pip --quiet
python -m pip install PyQt5 pygame pyinstaller --quiet
if errorlevel 1 (
    echo.
    echo [오류] 라이브러리 설치 실패. 인터넷 연결을 확인하세요.
    pause
    exit /b 1
)
echo    OK
echo.

REM 3. 이전 빌드 파일 청소
echo [3/4] 이전 빌드 정리 중...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist KUJINO.spec del KUJINO.spec
echo    OK
echo.

REM 4. PyInstaller로 EXE 빌드
echo [4/4] EXE 파일 생성 중... ^(1~3분 정도 걸립니다^)
echo.
python -m PyInstaller --name=KUJINO --onefile --windowed --clean --add-data="assets;assets" --hidden-import=pygame kujino_app.py

if errorlevel 1 (
    echo.
    echo [오류] 빌드 실패. 위의 메시지를 확인하세요.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   빌드 성공!
echo ========================================
echo.
echo EXE 파일 위치: dist\KUJINO.exe
echo.
echo 이제 dist 폴더의 KUJINO.exe를 더블클릭하면 실행됩니다.
echo 다른 PC로 복사해서 써도 됩니다 ^(Python 설치 불필요^)
echo.
echo [TIP] 사운드가 필요하면 KUJINO.exe와 같은 폴더에
echo       sounds 폴더를 만들고 mp3 파일들을 넣으세요.
echo       (bgm.mp3, win.mp3, flip.mp3 등)
echo.

REM dist 폴더 자동으로 열어주기
explorer dist

pause
