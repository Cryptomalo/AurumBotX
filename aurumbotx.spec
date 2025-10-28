# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Aggiungere i file principali e le dipendenze nascoste
a = Analysis(
    ['start_aurumbotx.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('src/web', 'src/web'),  # PWA Web Interface (HTML/CSS/JS)
        ('config', 'config'),    # Configuration files (e.g., live_testing_50usdt.json)
        ('src/dashboards', 'src/dashboards'), # Streamlit dashboard files
        ('src/analytics', 'src/analytics'), # Analytics files (if needed)
        ('src/reporting', 'src/reporting'), # Reporting files (e.g., templates for PDF)
        ('src/visuals', 'src/visuals'), # Visuals files (e.g., Plotly charts)
        ('requirements.txt', '.'), # Per riferimento
    ],
    hiddenimports=[
        'streamlit',
        'plotly',
        'pandas',
        'numpy',
        'sqlalchemy',
        'python_binance',
        'fpdf2',
        'reportlab',
        'ta',
        'yfinance',
        'cryptography',
        'aiohttp',
        'websockets',
        'psutil',
        # Aggiungere altre librerie complesse se necessario
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Creazione dell'eseguibile (EXE)
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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Creazione del pacchetto (se necessario, ad esempio un installer)
# Non necessario per un singolo eseguibile, ma utile per la distribuzione
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AurumBotX',
)
