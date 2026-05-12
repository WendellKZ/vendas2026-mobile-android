@echo off
echo =====================================================
echo Vendas 2026 Mobile - Gerar APK Debug
echo =====================================================
echo.
echo Este script funciona se o Gradle/Android Studio estiver configurado no Windows.
echo Se nao funcionar, use pelo Android Studio:
echo Build ^> Build Bundle(s) / APK(s) ^> Build APK(s)
echo.
if exist gradlew.bat (
  call gradlew.bat assembleDebug
) else (
  echo gradlew.bat nao encontrado neste projeto.
  echo Abra no Android Studio e gere pelo menu Build.
  pause
  exit /b 1
)
echo.
echo APK gerado em: app\build\outputs\apk\debug\app-debug.apk
pause
