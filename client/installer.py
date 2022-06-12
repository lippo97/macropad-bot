import PyInstaller.__main__
import site

path = site.getsitepackages()[0]

PyInstaller.__main__.run([
    'client/main.py',
    '--onefile',
    '--paths',
    path
])
