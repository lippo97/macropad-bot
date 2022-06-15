import PyInstaller.__main__
import site
import shutil
from os import path

site_packages_path = site.getsitepackages()[0]

PyInstaller.__main__.run([
    'client/main.py',
    '--onefile',
    '--paths',
    site_packages_path,
    '--name',
    'macropad-client'
])


shutil.copyfile('keys.toml', path.join('dist', 'keys.toml'))
