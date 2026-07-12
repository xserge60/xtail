@echo off
setlocal

:: 1. Ищем номер версии в главном скрипте (заменить main.py на имя главного скрипта проекта). 
set verFile=xtail.py

:: 2. Извлекаем версию
::for /f "usebackq tokens=*" %%a in (`python -c "import re; f=open('%verFile%', encoding='utf-8'); print(re.search(r'__version__\s*=\s*[\x27\x22]([^\x27\x22]+)', f.read()).group(1))"`) do (set vers=%%a)
for /f "usebackq tokens=*" %%a in (`python -I -c "import re; f=open(r'%~dp0%verFile%', encoding='utf-8'); print(re.search(r'__version__\s*=\s*[\x27\x22]([^\x27\x22]+)', f.read()).group(1))"`) do (set vers=%%a)
set vers="5.1.6"

:: 3. Формируем сообщение коммита
:: %1 - это первый аргумент, переданный при запуске скрипта
if "%~1"=="" (
    set commitMsg=Обновление версии %vers%
) else (
    set commitMsg=Обновление версии %vers%: %~1
)

echo Сообщение коммита: "%commitMsg%"

