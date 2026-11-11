@echo off
:: ============================================================
::  Reinicio automatico noturno - Windows
::  Cria uma tarefa agendada que reinicia o PC todo dia.
::  Executar como ADMINISTRADOR (botao direito > Executar como administrador)
:: ============================================================

:: ---- CONFIGURACAO ----
set HORARIO=03:00
set AVISO_SEG=300
set NOME_TAREFA=ReinicioNoturno
:: ----------------------

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Execute este arquivo como Administrador.
    pause
    exit /b 1
)

echo Criando tarefa "%NOME_TAREFA%" para reiniciar todo dia as %HORARIO%...

schtasks /Create /TN "%NOME_TAREFA%" /SC DAILY /ST %HORARIO% /RU SYSTEM /RL HIGHEST /F ^
 /TR "shutdown.exe /r /f /t %AVISO_SEG% /c \"Reinicio automatico programado em 5 minutos. Salve seu trabalho.\""

if %errorlevel% neq 0 (
    echo [ERRO] Falha ao criar a tarefa.
    pause
    exit /b 1
)

:: Permite rodar na bateria e acordar o PC se estiver em suspensao
powershell -NoProfile -Command ^
 "$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun -StartWhenAvailable;" ^
 "Set-ScheduledTask -TaskName '%NOME_TAREFA%' -Settings $s | Out-Null"

echo.
echo [OK] Tarefa criada. O PC vai reiniciar todo dia as %HORARIO%.
echo      Para conferir:  schtasks /Query /TN "%NOME_TAREFA%"
echo      Para cancelar um reinicio em andamento:  shutdown /a
echo      Para remover:   schtasks /Delete /TN "%NOME_TAREFA%" /F
echo.
pause
