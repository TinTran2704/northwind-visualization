@echo off
setlocal EnableDelayedExpansion

:: ============================================================
:: run.bat  —  Setup venv + chạy test_connection cho Northwind
:: Chạy từ thư mục bất kỳ cũng được, script tự tìm repo root
:: ============================================================

:: Tìm repo root (2 cấp trên bin\windows\)
set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%..\..\"
pushd "%ROOT%"
set "ROOT=%CD%"
popd

echo.
echo ============================================================
echo  Northwind Visualization — Metabase Client Setup
echo  Repo root: %ROOT%
echo ============================================================
echo.

:: ------------------------------------------------------------
:: 1. Kiểm tra Python
:: ------------------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Khong tim thay Python. Cai Python 3.8+ va them vao PATH.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] %%v

:: ------------------------------------------------------------
:: 2. Tạo virtual environment nếu chưa có
:: ------------------------------------------------------------
set "VENV=%ROOT%\.venv"

if not exist "%VENV%\Scripts\activate.bat" (
    echo [INFO] Tao virtual environment tai .venv ...
    python -m venv "%VENV%"
    if errorlevel 1 (
        echo [ERROR] Khong the tao venv.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment da tao.
) else (
    echo [OK] Virtual environment da co san.
)

:: ------------------------------------------------------------
:: 3. Kích hoạt venv
:: ------------------------------------------------------------
call "%VENV%\Scripts\activate.bat"
echo [OK] Da kich hoat venv.

:: ------------------------------------------------------------
:: 4. Cài / cập nhật dependencies
:: ------------------------------------------------------------
echo [INFO] Cai dependencies tu scripts\requirements.txt ...
python -m pip install -q --upgrade pip
python -m pip install -q -r "%ROOT%\scripts\requirements.txt"
if errorlevel 1 (
    echo [ERROR] pip install that bai.
    pause
    exit /b 1
)
echo [OK] Dependencies da cai xong.

:: ------------------------------------------------------------
:: 5. Kiểm tra file .env
:: ------------------------------------------------------------
if not exist "%ROOT%\.env" (
    echo [WARN] Khong tim thay .env — copy tu .env.example ...
    if exist "%ROOT%\.env.example" (
        copy "%ROOT%\.env.example" "%ROOT%\.env" >nul
        echo [WARN] Da copy .env.example -> .env
        echo [WARN] Sua METABASE_PASSWORD trong .env truoc khi chay lai.
        pause
        exit /b 0
    ) else (
        echo [ERROR] Khong co .env.example. Tao file .env thu cong.
        pause
        exit /b 1
    )
)
echo [OK] Tim thay .env.

:: ------------------------------------------------------------
:: 6. Chạy test
:: ------------------------------------------------------------
echo.
echo [INFO] Chay test_connection.py ...
echo ------------------------------------------------------------
cd /d "%ROOT%"
python scripts\test_connection.py
set "EXIT_CODE=%ERRORLEVEL%"

echo ------------------------------------------------------------
if %EXIT_CODE% == 0 (
    echo [OK] Ket noi thanh cong!
) else (
    echo [ERROR] Test that bai. Xem log phia tren.
)

echo.
pause
exit /b %EXIT_CODE%
