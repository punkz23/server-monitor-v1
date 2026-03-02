@echo off
echo ========================================
echo Building Server Monitor Mobile APK
echo ========================================

REM Check if Flutter is installed
flutter --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Flutter is not installed or not in PATH
    echo Please install Flutter and add it to your PATH
    pause
    exit /b 1
)

echo Flutter version:
flutter --version

REM Clean previous builds
echo.
echo Cleaning previous builds...
flutter clean
if %errorlevel% neq 0 (
    echo WARNING: Clean failed, continuing anyway...
)

REM Get dependencies
echo.
echo Getting dependencies...
flutter pub get
if %errorlevel% neq 0 (
    echo ERROR: Failed to get dependencies
    pause
    exit /b 1
)

REM Check for Android SDK
echo.
echo Checking Android setup...
flutter doctor --android-licenses
if %errorlevel% neq 0 (
    echo WARNING: Android licenses not accepted, attempting to accept...
    echo y | flutter doctor --android-licenses
)

REM Build APK (Debug)
echo.
echo Building Debug APK...
flutter build apk --debug
if %errorlevel% neq 0 (
    echo ERROR: Debug APK build failed
    pause
    exit /b 1
)

echo.
echo Debug APK built successfully!
echo Location: build\app\outputs\flutter-apk\app-debug.apk

REM Ask if user wants release build
set /p build_release=Build Release APK? (y/n): 
if /i "%build_release%"=="y" (
    echo.
    echo Building Release APK...
    flutter build apk --release
    if %errorlevel% neq 0 (
        echo ERROR: Release APK build failed
        pause
        exit /b 1
    )
    echo.
    echo Release APK built successfully!
    echo Location: build\app\outputs\flutter-apk\app-release.apk
)

echo.
echo ========================================
echo Build completed!
echo ========================================
echo.
echo APK files are located in:
echo build\app\outputs\flutter-apk\
echo.
echo To install on device:
echo 1. Enable USB debugging on Android device
echo 2. Connect device via USB
echo 3. Run: flutter install
echo.
pause
