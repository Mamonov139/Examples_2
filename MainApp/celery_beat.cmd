goto start
----------------------------------------------------------------------------
Инструкция запуска отбивки времени

----------------------------------------------------------------------------
:start
start venv\Scripts\celery -A MainApp.celery beat -s %PAYMENTS_PROJECT_DRIVE%%PAYMENTS_PROJECT_DIR%\payments\temp\beat ^
                          --pidfile=%PAYMENTS_PROJECT_DRIVE%%PAYMENTS_PROJECT_DIR%\payments\temp\beat.pid ^
                          --logfile=%PAYMENTS_PROJECT_DRIVE%%PAYMENTS_PROJECT_DIR%\payments\logs\beat.log