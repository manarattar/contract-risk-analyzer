"""Reject a tampered COPY without touching any stored encrypted backup."""
import importlib.util
from pathlib import Path
import shutil
import tempfile

spec=importlib.util.spec_from_file_location('backup','/srv/apps/contracts-v2/operations/backup.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
source=sorted(module.ROOT.glob('contracts-v2-*.tar.enc'))[-1]
with tempfile.TemporaryDirectory(prefix='contracts-tamper-check-') as temp:
    copy=Path(temp)/source.name
    shutil.copyfile(source,copy)
    shutil.copyfile(source.with_suffix('.json'),copy.with_suffix('.json'))
    data=bytearray(copy.read_bytes());data[-1]^=1;copy.write_bytes(data)
    module.ROOT=Path(temp)
    try:module.rehearse()
    except ValueError as error:
        assert 'authentication failed' in str(error)
    else:raise AssertionError('Tampered backup was accepted')
print('Authenticated backup tamper rejection verified; stored backup unchanged.')
