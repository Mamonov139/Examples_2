goto start
----------------------------------------------------------------------------
Запуск планировщика
----------------------------------------------------------------------------
:start
%PAYMENTS_PROJECT_DRIVE%
cd %PAYMENTS_PROJECT_DIR%
cd payments
SET PID_FILE=.\temp\beat.pid
IF EXIST %PID_FILE% SET /P PID= < .\temp\beat.pid
IF EXIST %PID_FILE% TASKKILL /F /PID %PID%
IF EXIST %PID_FILE% DEL /F .\temp\beat.pid
.\MainApp\celery_beat.cmd