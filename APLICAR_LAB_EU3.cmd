@echo off
setlocal
cd /d "%~dp0"
where gradle >nul 2>nul || (echo Gradle 8.9 deve estar instalado. Nenhum APK antigo sera instalado.& exit /b 1)
where adb >nul 2>nul || (echo Android platform-tools deve estar instalado.& exit /b 1)
if not defined ANDROID_HOME (echo Defina ANDROID_HOME para o Android SDK com plataforma 35.& exit /b 1)
call gradle -p android --no-daemon :app:assembleDebug
if errorlevel 1 exit /b 1
adb get-state
if errorlevel 1 exit /b 1
adb install -r "android\app\build\outputs\apk\debug\app-debug.apk"
if errorlevel 1 (echo Instalacao interrompida. Nao desinstale para contornar assinatura.& exit /b 1)
echo Preview instalado. Abra Lab IA e Pesquisa metodo EU3. Nao substitui o pacote principal.
