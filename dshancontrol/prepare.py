#!/usr/bin/env python3
"""Prepare the pinned native DshanControl board integration without flashing."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--application', type=Path, required=True, help='Clean DshanControl Git checkout at pinned commit')
    parser.add_argument('--output', type=Path, required=True, help='New directory outside both source repositories')
    args = parser.parse_args()
    hardware = Path(__file__).resolve().parents[1]
    app, output = args.application.resolve(), args.output.resolve()
    lock = json.loads((hardware / 'dshancontrol/release-inputs.json').read_text())
    for root in (hardware, app):
        if git(root, 'status', '--porcelain', '--untracked-files=normal'):
            parser.error('Use a clean committed tree: ' + str(root))
    if git(app, 'rev-parse', 'HEAD') != lock['application_commit']:
        parser.error('Application commit differs from the release recipe')
    if git(hardware, 'diff', lock['bsp_commit'], 'HEAD', '--', 'buildroot-2026.02.1', '.gitmodules', 'linux-imx', 'uboot-imx'):
        parser.error('BSP baseline changed; review and update the release recipe')
    if (output.exists() or any(root == output or root in output.parents for root in (hardware, app))
            or any(ch.isspace() for ch in str(output) + str(hardware))):
        parser.error('Use a new output without whitespace outside the source trees')
    with tempfile.TemporaryDirectory(prefix='dshan-locked-input-') as temp:
        source = Path(temp) / 'application.tar.gz'
        subprocess.run(['git', '-C', str(app), 'archive', '--format=tar.gz', '-o', str(source), lock['application_commit']], check=True)
        if hashlib.sha256(source.read_bytes()).hexdigest() != lock['application_source_sha256']:
            parser.error('Pinned source archive hash mismatch')
        output.mkdir(parents=True)
        external = output / 'external'
        shutil.copytree(hardware / 'dshancontrol/board/buildroot', external)
        # This release recipe deliberately retains the exact A snapshot layout used
        # during the build. Board inputs are checked against authoritative H below.
        snapshot = external / 'app-source'
        snapshot.mkdir()
        with tarfile.open(source) as package:
            package.extractall(snapshot, filter='data')
    board = hardware / 'dshancontrol/board'
    for folder in ('buildroot', 'runtime', 'maintenance'):
        for path in (board / folder).rglob('*'):
            if path.is_file():
                relative = path.relative_to(board)
                matching = snapshot / 'boards/imx6ull-pro' / relative
                if not matching.is_file() or path.read_bytes() != matching.read_bytes():
                    raise RuntimeError('Board migration differs from pinned A: ' + str(relative))
    identity = {'application_commit': lock['application_commit'], 'bsp_commit': lock['bsp_commit'],
                'hardware_commit': git(hardware, 'rev-parse', 'HEAD'),
                'hardware_repository': 'https://github.com/dshanpi/aibsp-imx6ull-pro_linux5.4.47',
                'release_kind': 'system', 'qualification': 'development-draft-not-qualified'}
    (external / 'overlay/etc/dshancontrol/build-source.json').write_text(json.dumps(identity, indent=2) + '\n')
    for path in (external / 'overlay/etc/init.d').iterdir():
        path.chmod(0o755)
    helper = snapshot / 'scripts/prepare_imx6ull.py'
    spec = importlib.util.spec_from_file_location('config_merge', helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    build = output / 'buildroot'
    command = ['make', '-C', str(hardware / 'buildroot-2026.02.1'), 'O=' + str(build), 'BR2_EXTERNAL=' + str(external)]
    subprocess.run(command + ['100ask_imx6ull-pro_defconfig'], check=True)
    module.merge_config(build / '.config', (external / 'dshancontrol.fragment').read_text()
        + '\nBR2_ROOTFS_OVERLAY="board/100ask/imx6ull-pro/rootfs-overlay ' + str(external / 'overlay') + '"\n'
        + 'BR2_GLOBAL_PATCH_DIR="board/100ask/imx6ull-pro/patches ' + str(external / 'patches') + '"\n')
    subprocess.run(command + ['olddefconfig'], check=True)
    files = {p.relative_to(snapshot).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(snapshot.rglob('*')) if p.is_file()}
    record = dict(identity, application_status='', source_files_sha256=files,
                  config_sha256=hashlib.sha256((build / '.config').read_bytes()).hexdigest(),
                  hardware_validation='not-run', scope='pinned-hardware-and-application-source-inputs')
    (output / 'provenance.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Prepared. Build with: CCACHE=none CCACHE_DISABLE=1 make -C', build, '-j8')


if __name__ == '__main__':
    main()
