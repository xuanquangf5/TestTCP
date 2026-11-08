"""Build, smoke-test, and archive the native app on each CI runner."""

import platform
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = sys.argv[1]
    targets = {
        'Windows-x86': ('Windows', 32), 'Windows-x64': ('Windows', 64),
        'macOS-x64': ('Darwin', 64), 'macOS-arm64': ('Darwin', 64),
        'Linux-x64': ('Linux', 64), 'Linux-arm64': ('Linux', 64),
    }
    expected_os, bits = targets[target]
    if platform.system() != expected_os or (sys.maxsize > 2**32) != (bits == 64):
        raise RuntimeError(f'Wrong Python/OS for {target}')
    machine = platform.machine().lower()
    if bits == 64 and ('arm' in machine or 'aarch64' in machine) != target.endswith('arm64'):
        raise RuntimeError(f'Wrong architecture for {target}: {machine}')
    version = (ROOT / 'VERSION').read_text().strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('Invalid VERSION')
    subprocess.run([sys.executable, 'app.py', '--smoke-test'], cwd=ROOT, check=True, timeout=30)
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
               '--name', 'TestTCP', '--windowed']
    # macOS app bundles use onedir; Windows/Linux use one executable.
    command.append('--onedir' if expected_os == 'Darwin' else '--onefile')
    subprocess.run(command + ['app.py'], cwd=ROOT, check=True)
    dist = ROOT / 'dist'
    if expected_os == 'Windows':
        binary = dist / 'TestTCP.exe'
    elif expected_os == 'Darwin':
        binary = dist / 'TestTCP.app' / 'Contents' / 'MacOS' / 'TestTCP'
    else:
        binary = dist / 'TestTCP'
    subprocess.run([str(binary), '--smoke-test'], cwd=ROOT, check=True, timeout=60)
    release = ROOT / 'release'
    release.mkdir(exist_ok=True)
    name = f'TestTCP-{version}-{target}'
    if expected_os == 'Darwin':
        subprocess.run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent',
                        str(dist / 'TestTCP.app'), str(release / f'{name}.zip')], check=True)
    elif expected_os == 'Windows':
        with zipfile.ZipFile(release / f'{name}.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.write(binary, binary.name)
            archive.write(ROOT / 'README.md', 'README.md')
    else:
        with tarfile.open(release / f'{name}.tar.gz', 'w:gz') as archive:
            archive.add(binary, arcname=binary.name)
            archive.add(ROOT / 'README.md', arcname='README.md')
    print(f'Built and verified {name}', flush=True)


if __name__ == '__main__':
    main()
