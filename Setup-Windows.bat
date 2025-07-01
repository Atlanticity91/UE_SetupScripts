@echo off

pushd %~dp0
python Scripts/Setup.py --engine UE_5.6 --project "%~dp0GameName.uproject"
popd

pause
