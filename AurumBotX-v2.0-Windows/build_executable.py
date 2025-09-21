#!/usr/bin/env python3
"""
AurumBotX Executable Builder
Build script for creating standalone executable with PyInstaller

Author: AurumBotX Team
Date: 13 Settembre 2025
Version: 2.0
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

class ExecutableBuilder:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.dist_dir = self.project_dir / "dist"
        self.build_dir = self.project_dir / "build"
        self.spec_file = self.project_dir / "aurumbotx.spec"
        
        print("🔨 AurumBotX Executable Builder")
        print("=" * 50)
        print(f"📁 Project Directory: {self.project_dir}")
        print(f"📦 Output Directory: {self.dist_dir}")
        print("=" * 50)
    
    def clean_build(self):
        """Clean previous build artifacts"""
        print("\n🧹 Cleaning previous build...")
        
        # Remove build directories
        for directory in [self.dist_dir, self.build_dir]:
            if directory.exists():
                shutil.rmtree(directory)
                print(f"✅ Removed {directory}")
        
        # Remove spec file
        if self.spec_file.exists():
            self.spec_file.unlink()
            print(f"✅ Removed {self.spec_file}")
    
    def create_spec_file(self):
        """Create PyInstaller spec file"""
        print("\n📝 Creating PyInstaller spec file...")
        
        spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files to include
datas = [
    ('config', 'config'),
    ('README.md', '.'),
    ('ROADMAP.md', '.'),
    ('VERSION', '.'),
]

# Hidden imports
hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'tkinter.scrolledtext',
    'sqlite3',
    'json',
    'threading',
    'webbrowser',
    'subprocess',
    'requests',
    'pandas',
    'numpy',
    'streamlit',
    'plotly',
    'binance',
    'ccxt',
]

# Analysis
a = Analysis(
    ['aurumbotx_gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove unnecessary modules to reduce size
a.binaries = [x for x in a.binaries if not x[0].startswith('matplotlib')]
a.binaries = [x for x in a.binaries if not x[0].startswith('scipy')]
a.binaries = [x for x in a.binaries if not x[0].startswith('PIL')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AurumBotX',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for windowed app
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
'''
        
        with open(self.spec_file, 'w') as f:
            f.write(spec_content)
        
        print(f"✅ Spec file created: {self.spec_file}")
    
    def create_version_file(self):
        """Create version file"""
        version_file = self.project_dir / "VERSION"
        with open(version_file, 'w') as f:
            f.write("2.0.0")
        print("✅ Version file created")
    
    def create_icon(self):
        """Create application icon"""
        print("\n🎨 Creating application icon...")
        
        # For now, we'll skip icon creation
        # In production, you would create a proper .ico file
        print("⚠️ Icon creation skipped (add icon.ico manually)")
    
    def install_dependencies(self):
        """Install build dependencies"""
        print("\n📦 Installing build dependencies...")
        
        dependencies = [
            "pyinstaller",
            "upx-ucl",  # For compression
        ]
        
        for dep in dependencies:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
                print(f"✅ {dep} installed")
            except subprocess.CalledProcessError:
                print(f"⚠️ Failed to install {dep}")
    
    def build_executable(self):
        """Build the executable"""
        print("\n🔨 Building executable...")
        
        try:
            # Run PyInstaller
            cmd = [
                "pyinstaller",
                "--clean",
                "--noconfirm",
                str(self.spec_file)
            ]
            
            print(f"🔧 Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Executable built successfully!")
                return True
            else:
                print(f"❌ Build failed:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False
    
    def create_installer_script(self):
        """Create installer script"""
        print("\n📦 Creating installer script...")
        
        # Windows batch installer
        installer_bat = self.dist_dir / "install.bat"
        with open(installer_bat, 'w') as f:
            f.write('''@echo off
echo 🚀 AurumBotX Installer
echo =====================

echo 📁 Creating installation directory...
set INSTALL_DIR=%USERPROFILE%\\AurumBotX
mkdir "%INSTALL_DIR%" 2>nul

echo 📋 Copying files...
copy "AurumBotX.exe" "%INSTALL_DIR%\\"
xcopy "config" "%INSTALL_DIR%\\config\\" /E /I /Y 2>nul

echo 🖥️ Creating desktop shortcut...
echo [InternetShortcut] > "%USERPROFILE%\\Desktop\\AurumBotX.url"
echo URL=file:///%INSTALL_DIR%\\AurumBotX.exe >> "%USERPROFILE%\\Desktop\\AurumBotX.url"

echo ✅ Installation completed!
echo 🚀 You can now run AurumBotX from your desktop
pause
''')
        
        # Linux/Mac installer
        installer_sh = self.dist_dir / "install.sh"
        with open(installer_sh, 'w') as f:
            f.write('''#!/bin/bash
echo "🚀 AurumBotX Installer"
echo "====================="

INSTALL_DIR="$HOME/AurumBotX"

echo "📁 Creating installation directory..."
mkdir -p "$INSTALL_DIR"

echo "📋 Copying files..."
cp "AurumBotX" "$INSTALL_DIR/"
cp -r config "$INSTALL_DIR/" 2>/dev/null || true

echo "🔧 Setting permissions..."
chmod +x "$INSTALL_DIR/AurumBotX"

echo "🖥️ Creating desktop shortcut..."
cat > "$HOME/Desktop/AurumBotX.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=AurumBotX
Comment=Professional Cryptocurrency Trading Bot
Exec=$INSTALL_DIR/AurumBotX
Icon=$INSTALL_DIR/icon.png
Terminal=false
Categories=Office;Finance;
EOF

chmod +x "$HOME/Desktop/AurumBotX.desktop"

echo "✅ Installation completed!"
echo "🚀 You can now run AurumBotX from your desktop"
''')
        
        # Make executable
        os.chmod(installer_sh, 0o755)
        
        print("✅ Installer scripts created")
    
    def create_readme(self):
        """Create README for distribution"""
        print("\n📖 Creating distribution README...")
        
        readme_content = '''# 🚀 AurumBotX - Professional Trading Bot

## 📦 Installation

### Windows:
1. Run `install.bat` as Administrator
2. Follow the installation prompts
3. Launch AurumBotX from desktop shortcut

### Linux/Mac:
1. Run `chmod +x install.sh && ./install.sh`
2. Launch AurumBotX from desktop shortcut

## ⚡ Quick Start

1. **Launch Application**: Double-click AurumBotX icon
2. **Configure API Keys**: Go to Settings tab
3. **Set Risk Parameters**: Adjust trading settings
4. **Start Trading**: Click "Start Trading" button

## 🔧 System Requirements

- **OS**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB free space
- **Internet**: Stable connection required

## 📊 Features

- ✅ AI-powered trading strategies
- ✅ Real-time market analysis
- ✅ Advanced risk management
- ✅ Multi-exchange support
- ✅ 24/7 automated trading
- ✅ Native desktop interface
- ✅ Web dashboard integration

## 🛡️ Security

- ✅ Local data storage
- ✅ Encrypted API keys
- ✅ No data transmission to third parties
- ✅ Emergency stop functionality

## 📞 Support

- 📧 Email: support@aurumbotx.ai
- 💬 Telegram: @AurumBotX_Bot
- 📖 Documentation: https://docs.aurumbotx.ai
- 🌐 Website: https://aurumbotx.ai

## ⚠️ Disclaimer

Trading cryptocurrencies involves substantial risk of loss. 
Past performance does not guarantee future results.
Only trade with funds you can afford to lose.

---

© 2025 AurumBotX Team - All Rights Reserved
'''
        
        readme_file = self.dist_dir / "README.txt"
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        print("✅ Distribution README created")
    
    def package_release(self):
        """Package the release"""
        print("\n📦 Packaging release...")
        
        # Create release directory
        release_dir = self.project_dir / "release"
        release_dir.mkdir(exist_ok=True)
        
        # Create zip package
        import zipfile
        
        zip_name = f"AurumBotX-v2.0-{sys.platform}.zip"
        zip_path = release_dir / zip_name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add executable
            exe_name = "AurumBotX.exe" if sys.platform == "win32" else "AurumBotX"
            exe_path = self.dist_dir / exe_name
            if exe_path.exists():
                zipf.write(exe_path, exe_name)
            
            # Add config directory
            config_dir = self.project_dir / "config"
            if config_dir.exists():
                for file_path in config_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = f"config/{file_path.relative_to(config_dir)}"
                        zipf.write(file_path, arcname)
            
            # Add installer scripts
            for installer in ["install.bat", "install.sh"]:
                installer_path = self.dist_dir / installer
                if installer_path.exists():
                    zipf.write(installer_path, installer)
            
            # Add README
            readme_path = self.dist_dir / "README.txt"
            if readme_path.exists():
                zipf.write(readme_path, "README.txt")
        
        print(f"✅ Release package created: {zip_path}")
        return zip_path
    
    def get_build_info(self):
        """Get build information"""
        exe_name = "AurumBotX.exe" if sys.platform == "win32" else "AurumBotX"
        exe_path = self.dist_dir / exe_name
        
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            return {
                "executable": str(exe_path),
                "size_mb": f"{size_mb:.1f} MB",
                "platform": sys.platform,
                "exists": True
            }
        else:
            return {"exists": False}
    
    def build_complete(self):
        """Complete build process"""
        print("\n🚀 Starting complete build process...")
        
        try:
            # Clean previous build
            self.clean_build()
            
            # Create necessary files
            self.create_version_file()
            self.create_icon()
            
            # Install dependencies
            self.install_dependencies()
            
            # Create spec file
            self.create_spec_file()
            
            # Build executable
            if not self.build_executable():
                return False
            
            # Create installer and documentation
            self.create_installer_script()
            self.create_readme()
            
            # Package release
            zip_path = self.package_release()
            
            # Get build info
            build_info = self.get_build_info()
            
            # Success summary
            print("\n🎉 BUILD COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            
            if build_info["exists"]:
                print(f"📁 Executable: {build_info['executable']}")
                print(f"📊 Size: {build_info['size_mb']}")
                print(f"🖥️ Platform: {build_info['platform']}")
            
            print(f"📦 Release Package: {zip_path}")
            print(f"📁 Distribution: {self.dist_dir}")
            
            print("\n🎯 Next Steps:")
            print("1. Test the executable")
            print("2. Distribute the zip package")
            print("3. Share with users!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Build failed: {e}")
            return False

def main():
    """Main build function"""
    builder = ExecutableBuilder()
    
    # Ask for confirmation
    print("\nThis will build AurumBotX executable.")
    response = input("Continue? (y/N): ").lower().strip()
    
    if response != 'y':
        print("Build cancelled.")
        return
    
    # Run build
    success = builder.build_complete()
    
    if success:
        print("\n🎉 Build successful! Executable ready for distribution.")
    else:
        print("\n❌ Build failed. Check errors above.")

if __name__ == "__main__":
    main()

