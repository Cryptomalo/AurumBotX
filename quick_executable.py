#!/usr/bin/env python3
"""
AurumBotX Quick Executable Builder
Simplified build for immediate executable creation

Author: AurumBotX Team
Date: 13 Settembre 2025
Version: 2.0
"""

import os
import sys
import subprocess
from pathlib import Path

def create_simple_executable():
    """Create simple executable with basic PyInstaller"""
    print("🚀 AurumBotX Quick Executable Builder")
    print("=" * 50)
    
    project_dir = Path(__file__).parent
    
    # Simple PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=AurumBotX",
        "--add-data=config:config",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=sqlite3",
        "--hidden-import=json",
        "--hidden-import=threading",
        "--hidden-import=webbrowser",
        "aurumbotx_gui.py"
    ]
    
    print(f"🔧 Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Executable created successfully!")
            
            # Check if file exists
            exe_path = project_dir / "dist" / "AurumBotX.exe"
            if not exe_path.exists():
                exe_path = project_dir / "dist" / "AurumBotX"
            
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"📁 Executable: {exe_path}")
                print(f"📊 Size: {size_mb:.1f} MB")
                
                # Create simple installer
                create_simple_installer(exe_path)
                
                return True
            else:
                print("❌ Executable not found after build")
                return False
        else:
            print(f"❌ Build failed:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Build timeout (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def create_simple_installer(exe_path):
    """Create simple installer script"""
    print("\n📦 Creating installer...")
    
    dist_dir = exe_path.parent
    
    # Windows installer
    installer_bat = dist_dir / "install.bat"
    with open(installer_bat, 'w') as f:
        f.write(f'''@echo off
echo 🚀 AurumBotX Quick Installer
echo ========================

set INSTALL_DIR=%USERPROFILE%\\AurumBotX
mkdir "%INSTALL_DIR%" 2>nul

echo Copying AurumBotX...
copy "{exe_path.name}" "%INSTALL_DIR%\\"

echo Creating desktop shortcut...
echo [InternetShortcut] > "%USERPROFILE%\\Desktop\\AurumBotX.url"
echo URL=file:///%INSTALL_DIR%\\{exe_path.name} >> "%USERPROFILE%\\Desktop\\AurumBotX.url"

echo ✅ Installation completed!
echo You can now run AurumBotX from your desktop
pause
''')
    
    # Linux installer
    installer_sh = dist_dir / "install.sh"
    with open(installer_sh, 'w') as f:
        f.write(f'''#!/bin/bash
echo "🚀 AurumBotX Quick Installer"
echo "========================"

INSTALL_DIR="$HOME/AurumBotX"
mkdir -p "$INSTALL_DIR"

echo "Copying AurumBotX..."
cp "{exe_path.name}" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/{exe_path.name}"

echo "Creating desktop shortcut..."
cat > "$HOME/Desktop/AurumBotX.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=AurumBotX
Comment=Professional Cryptocurrency Trading Bot
Exec=$INSTALL_DIR/{exe_path.name}
Terminal=false
Categories=Office;Finance;
EOF

chmod +x "$HOME/Desktop/AurumBotX.desktop"

echo "✅ Installation completed!"
echo "You can now run AurumBotX from your desktop"
''')
    
    os.chmod(installer_sh, 0o755)
    
    print(f"✅ Installers created in {dist_dir}")

def main():
    """Main function"""
    if not create_simple_executable():
        print("\n❌ Quick build failed")
        return
    
    print("\n🎉 QUICK BUILD COMPLETED!")
    print("📁 Check dist/ directory for executable")
    print("📦 Use install.bat (Windows) or install.sh (Linux) to install")

if __name__ == "__main__":
    main()

