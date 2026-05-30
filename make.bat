@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  make.bat  —  Northwind Visualization task runner
::  Usage: make <target>
::  Targets: up | setup | export | import | reset | screenshot | help
:: ============================================================

set "ROOT=%~dp0"
set "VENV=%ROOT%.venv\Scripts\activate.bat"
set "COMPOSE=docker compose"

if "%1"==""           goto HELP
if "%1"=="help"       goto HELP
if "%1"=="up"               goto UP
if "%1"=="setup"            goto SETUP
if "%1"=="setup-metabase"   goto SETUP_METABASE
if "%1"=="export"           goto EXPORT
if "%1"=="import"           goto IMPORT
if "%1"=="reset"            goto RESET
if "%1"=="reset-metabase"   goto RESET_METABASE
if "%1"=="screenshot"       goto SCREENSHOT

echo [ERROR] Unknown target: %1
goto HELP

:: ── up ──────────────────────────────────────────────────────
:UP
echo [make up] Starting Metabase...
cd /d "%ROOT%"
%COMPOSE% up -d
if errorlevel 1 (echo [ERROR] docker compose failed & exit /b 1)
echo.
echo Waiting for Metabase to be healthy (up to 90s)...
set /a waited=0
:WAIT_LOOP
docker inspect northwind_metabase --format "{{.State.Health.Status}}" 2>nul | findstr /i "healthy" >nul
if not errorlevel 1 goto HEALTHY
timeout /t 5 /nobreak >nul
set /a waited+=5
if !waited! geq 90 (
    echo [WARN] Metabase not healthy after 90s — check: docker logs northwind_metabase
    goto DONE
)
goto WAIT_LOOP
:HEALTHY
echo [OK] Metabase is up at http://localhost:3000
goto DONE

:: ── setup ───────────────────────────────────────────────────
:SETUP
echo [make setup] Running setup scripts 01 → 02 → 03...
cd /d "%ROOT%"
if not exist "%ROOT%.venv\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
)
call "%ROOT%.venv\Scripts\activate.bat"
pip install -q -r scripts\requirements.txt

echo.
echo [1/3] Setting semantic types...
python scripts\01_set_semantic_types.py
if errorlevel 1 (echo [ERROR] Script 01 failed & exit /b 1)

echo.
echo [2/3] Creating Questions...
python scripts\02_create_questions.py
if errorlevel 1 (echo [ERROR] Script 02 failed & exit /b 1)

echo.
echo [3/3] Creating Dashboards...
python scripts\03_create_dashboards.py
if errorlevel 1 (echo [ERROR] Script 03 failed & exit /b 1)

echo.
echo [make setup] Done! Open http://localhost:3000
goto DONE

:: ── setup-metabase ─────────────────────────────────────────
:SETUP_METABASE
echo [make setup-metabase] YAML-driven setup (questions + dashboards from config/)...
cd /d "%ROOT%"
if not exist "%ROOT%.venv\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
)
call "%ROOT%.venv\Scripts\activate.bat"
pip install -q -r requirements.txt
python scripts\setup_metabase.py
if errorlevel 1 (echo [ERROR] setup_metabase failed & exit /b 1)
goto DONE

:: ── reset-metabase ──────────────────────────────────────────
:RESET_METABASE
echo [make reset-metabase] Deleting Metabase data volume and restarting...
cd /d "%ROOT%"
%COMPOSE% down -v
%COMPOSE% up -d
echo [OK] Metabase reset. Complete wizard at http://localhost:3000 then run:
echo      make setup-metabase
goto DONE

:: ── export ──────────────────────────────────────────────────
:EXPORT
echo [make export] Exporting config to metabase-config/exports/...
cd /d "%ROOT%"
call "%ROOT%.venv\Scripts\activate.bat"
python scripts\04_export_config.py
if errorlevel 1 (echo [ERROR] Export failed & exit /b 1)
echo.
echo [OK] Export complete. Commit metabase-config/exports/ to git for version control.
goto DONE

:: ── import ──────────────────────────────────────────────────
:IMPORT
echo [make import] Importing config from metabase-config/exports/...
cd /d "%ROOT%"
call "%ROOT%.venv\Scripts\activate.bat"
python scripts\05_import_config.py
if errorlevel 1 (echo [ERROR] Import failed & exit /b 1)
goto DONE

:: ── reset ───────────────────────────────────────────────────
:RESET
echo [make reset] WARNING: This will DELETE all Metabase data and restart fresh.
echo Press Ctrl+C to cancel, or
pause
cd /d "%ROOT%"
%COMPOSE% down -v
echo [INFO] Restarting...
%COMPOSE% up -d
echo [OK] Metabase reset. Run "make setup" or "make import" to restore config.
goto DONE

:: ── screenshot ──────────────────────────────────────────────
:SCREENSHOT
echo.
echo ============================================================
echo  Screenshot Checklist — capture these dashboards:
echo ============================================================
echo.
echo  1. Sales Overview    http://localhost:3000  (find in Northwind/Executive)
echo     Save as: screenshots\sales_overview_main_%DATE:~-4,4%%DATE:~-10,2%%DATE:~-7,2%.png
echo.
echo  2. Product Performance  (Northwind/Sales)
echo     Save as: screenshots\product_performance_%DATE:~-4,4%%DATE:~-10,2%%DATE:~-7,2%.png
echo.
echo  3. Customer Geography   (Northwind/Marketing)
echo     Save as: screenshots\customer_geography_%DATE:~-4,4%%DATE:~-10,2%%DATE:~-7,2%.png
echo.
echo  4. Employee Performance (Northwind/Sales)
echo     Save as: screenshots\employee_performance_%DATE:~-4,4%%DATE:~-10,2%%DATE:~-7,2%.png
echo.
echo  5. ETL Pipeline Health  (Northwind/Operations)
echo     Save as: screenshots\etl_health_%DATE:~-4,4%%DATE:~-10,2%%DATE:~-7,2%.png
echo.
echo  Tips:
echo    - Use full-screen browser (F11) for cleanest screenshots
echo    - Run all questions first so charts render with data
echo    - Windows Snipping Tool: Win + Shift + S
echo ============================================================
goto DONE

:: ── help ────────────────────────────────────────────────────
:HELP
echo.
echo  Northwind Visualization — make.bat
echo.
echo  Usage: make ^<target^>
echo.
echo  Targets:
echo    up               Start Metabase container (waits for healthy)
echo    setup-metabase   YAML-driven setup: create all 13 questions + 5 dashboards
echo    setup            Legacy numbered scripts 01-03
echo    export           Export Questions + Dashboards to metabase-config/exports/
echo    import           Recreate from exports on a new machine
echo    reset-metabase   Wipe Metabase volume + restart (destructive!)
echo    reset            Delete all Metabase data and restart fresh
echo    screenshot  Show checklist of dashboards to screenshot
echo    help        Show this message
echo.
echo  Typical first-run workflow:
echo    make up
echo    ^(complete setup wizard at http://localhost:3000^)
echo    make setup
echo    make export
echo.
echo  Restore on new machine:
echo    make up
echo    ^(complete setup wizard^)
echo    make import
goto DONE

:DONE
echo.
endlocal
