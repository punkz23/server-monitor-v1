# Build Server Monitor Mobile APK
# PowerShell script for building Flutter APK

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Building Server Monitor Mobile APK" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if Flutter is installed
try {
    $flutterVersion = flutter --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Flutter is not installed or not in PATH"
    }
    Write-Host "Flutter version: $flutterVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Flutter is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Flutter and add it to your PATH" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Clean previous builds
Write-Host "`nCleaning previous builds..." -ForegroundColor Yellow
flutter clean
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Clean failed, continuing anyway..." -ForegroundColor Yellow
}

# Get dependencies
Write-Host "`nGetting dependencies..." -ForegroundColor Yellow
flutter pub get
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to get dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Android setup
Write-Host "`nChecking Android setup..." -ForegroundColor Yellow
flutter doctor --android-licenses
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Android licenses not accepted, attempting to accept..." -ForegroundColor Yellow
    "y" | flutter doctor --android-licenses
}

# Build APK (Debug)
Write-Host "`nBuilding Debug APK..." -ForegroundColor Green
flutter build apk --debug
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Debug APK build failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "`nDebug APK built successfully!" -ForegroundColor Green
Write-Host "Location: build\app\outputs\flutter-apk\app-debug.apk" -ForegroundColor Cyan

# Ask if user wants release build
$buildRelease = Read-Host "`nBuild Release APK? (y/n): "
if ($buildRelease -eq "y" -or $buildRelease -eq "Y") {
    Write-Host "`nBuilding Release APK..." -ForegroundColor Green
    flutter build apk --release
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Release APK build failed" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "`nRelease APK built successfully!" -ForegroundColor Green
    Write-Host "Location: build\app\outputs\flutter-apk\app-release.apk" -ForegroundColor Cyan
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Build completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nAPK files are located in:" -ForegroundColor Yellow
Write-Host "build\app\outputs\flutter-apk\" -ForegroundColor Cyan
Write-Host "`nTo install on device:" -ForegroundColor Yellow
Write-Host "1. Enable USB debugging on Android device" -ForegroundColor White
Write-Host "2. Connect device via USB" -ForegroundColor White
Write-Host "3. Run: flutter install" -ForegroundColor White
Write-Host "`nOr install directly: adb install build\app\outputs\flutter-apk\app-debug.apk" -ForegroundColor White

Read-Host "`nPress Enter to exit"
