# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['Downloader.pyw'],
    pathex=[],
    binaries=[
        ("Venv\\Lib\\site-packages\\win32more\\dll\\x86\\Microsoft.Graphics.Canvas.dll","win32more\\dll\\x86\\"),
        ("Venv\\Lib\\site-packages\\win32more\\dll\\x86\\Microsoft.Web.WebView2.Core.dll","win32more\\dll\\x86\\"),
        ("Venv\\Lib\\site-packages\\win32more\\dll\\x86\\Microsoft.Windows.ApplicationModel.Background.UniversalBGTask.dll","win32more\\dll\\x86\\"),
        ("Venv\\Lib\\site-packages\\win32more\\dll\\x86\\Microsoft.WindowsAppRuntime.Bootstrap.dll","win32more\\dll\\x86\\"),
        ("Venv\\Lib\\site-packages\\win32more\\dll\\x64\\Microsoft.Graphics.Canvas.dll","win32more\\dll\\x64\\"),
        ("Venv\\Lib\\site-packages\\win32more\\dll\\x64\\Microsoft.Web.WebView2.Core.dll","win32more\\dll\\x64\\"),
        ("Venv\\Lib\\site-packages\\win32more\\dll\\x64\\Microsoft.Windows.ApplicationModel.Background.UniversalBGTask.dll","win32more\\dll\\x64\\"),
        ("Venv\\Lib\\site-packages\\win32more\\dll\\x64\\Microsoft.WindowsAppRuntime.Bootstrap.dll","win32more\\dll\\x64\\"),
        ("Venv\\Lib\\site-packages\\win32more\\dll\\arm64\\Microsoft.Graphics.Canvas.dll","win32more\\dll\\arm64\\"),
        ("Venv\\Lib\\site-packages\\win32more\\dll\\arm64\\Microsoft.Web.WebView2.Core.dll","win32more\\dll\\arm64\\"),
        ("Venv\\Lib\\site-packages\\win32more\\dll\\arm64\\Microsoft.Windows.ApplicationModel.Background.UniversalBGTask.dll","win32more\\dll\\arm64\\"),
        ("Venv\\Lib\\site-packages\\win32more\\dll\\arm64\\Microsoft.WindowsAppRuntime.Bootstrap.dll","win32more\\dll\\arm64\\")
    ],
    datas=[
        ('Downloader.HomePage.xaml', '.'),
        ('Downloader.SettingsPage.xaml', '.'),
        ('Downloader.xaml', '.'),
        ('DownloadInfo.xaml', '.'),
        ('Loading.xaml', '.'),
        ('Downloader.SettingsPage.xaml', '.'),
        ('Template.xaml', '.')
    ],
    hiddenimports=[
        "win32more"
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
