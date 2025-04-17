@echo off
echo Starting Faithful OTP Server...

cd ../

:main
C:\panda3d-otp-with-decompile\built_x64\python\python.exe -m core_components.faithful_otp
pause
goto :main
