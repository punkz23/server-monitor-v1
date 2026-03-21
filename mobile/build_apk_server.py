import os
import subprocess
import shutil
from pathlib import Path

def main():
    print("🚀 Building Server Monitor Release APK for Server")
    
    project_root = Path(r"C:\Users\ServerAdmin\projects\server-monitor-v1\mobile")
    os.chdir(project_root)
    
    # Environment Setup
    flutter_bin = r"C:\Users\ServerAdmin\development\flutter\bin"
    flutter_cmd = os.path.join(flutter_bin, "flutter.bat")
    java_home = r"C:\Program Files\Android\Android Studio\jbr"
    android_sdk = r"C:\Users\ServerAdmin\AppData\Local\Android\Sdk"
    
    # Update Environment
    os.environ["JAVA_HOME"] = java_home
    os.environ["ANDROID_HOME"] = android_sdk
    os.environ["PATH"] = f"{flutter_bin};{os.path.join(java_home, 'bin')};{os.environ['PATH']}"
    
    if not os.path.exists(flutter_cmd):
        print(f"❌ Flutter not found at {flutter_cmd}")
        return

    print(f"✅ Using Flutter: {flutter_cmd}")
    
    # Step 1: Clean
    print("🧹 Cleaning project...")
    subprocess.run([flutter_cmd, "clean"], shell=True)
    
    # Step 2: Pub Get
    print("📦 Getting dependencies...")
    subprocess.run([flutter_cmd, "pub", "get"], shell=True)
    
    # Step 3: Build Release APK
    print("🔨 Building Release APK...")
    result = subprocess.run([flutter_cmd, "build", "apk", "--release", "--no-pub", "--android-skip-build-dependency-validation"], shell=True)
    
    if result.returncode == 0:
        src_apk = project_root / "build" / "app" / "outputs" / "flutter-apk" / "app-release.apk"
        if src_apk.exists():
            dest_apk = project_root / "build" / "app" / "outputs" / "flutter-apk" / "Server_Monitor_v1.0.apk"
            shutil.copy2(src_apk, dest_apk)
            print(f"🎉 Build successful!")
            print(f"📱 APK Location: {dest_apk}")
        else:
            print("❌ APK built but not found at expected location.")
    else:
        print("❌ Build failed.")

if __name__ == "__main__":
    main()
