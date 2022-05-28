import subprocess

cmds = [
    'nuitka',
    '--onefile',
    '--windows-icon-from-ico=icon.png',
    '--windows-disable-console',
    '--windows-company-name=tarngaina',
    '--windows-product-name=cslmao',
    '--windows-file-version=3.3.4.0',
    '--windows-product-version=3.3.4.0',
    '--plugin-enable=tk-inter',
    '--plugin-enable=numpy',
    'cslmao.py'
]

p = subprocess.Popen(
    cmds, shell = True,
    stdout = subprocess.PIPE, stderr = subprocess.STDOUT,
)
for line in p.stdout:
    print(line.decode()[:-1])
    
input()
