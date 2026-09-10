"""Fail-closed Linux parser restrictions: one input file, read-only runtime, no sockets/process creation."""
import ctypes
import os
from pathlib import Path
import platform


def restrict(input_path):
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise RuntimeError('sandbox_platform_unsupported')
    libc = ctypes.CDLL(None, use_errno=True)
    abi = libc.syscall(444, 0, 0, 1)
    if abi < 3:
        raise RuntimeError('sandbox_landlock_unavailable')
    class Ruleset(ctypes.Structure):
        _fields_ = [('handled_access_fs', ctypes.c_uint64)]
    class PathRule(ctypes.Structure):
        _pack_ = 1
        _fields_ = [('allowed_access', ctypes.c_uint64), ('parent_fd', ctypes.c_int32)]
    handled = (1 << (16 if abi >= 5 else 15)) - 1
    rules = Ruleset(handled)
    descriptor = libc.syscall(444, ctypes.byref(rules), ctypes.sizeof(rules), 0)
    if descriptor < 0:
        raise RuntimeError('sandbox_ruleset_failed')
    try:
        allowed = [Path('/usr'), Path('/lib'), Path('/lib64'), Path(__file__).resolve().parents[1], Path(input_path).resolve()]
        for path in allowed:
            if not path.exists(): continue
            fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
            try:
                # READ_FILE and, only for directories, READ_DIR. No execute or write.
                rule = PathRule((1 << 2) | ((1 << 3) if path.is_dir() else 0), fd)
                if libc.syscall(445, descriptor, 1, ctypes.byref(rule), 0):
                    raise RuntimeError('sandbox_path_rule_failed')
            finally: os.close(fd)
        if libc.prctl(38, 1, 0, 0, 0) or libc.syscall(446, descriptor, 0):
            raise RuntimeError('sandbox_enforcement_failed')
    finally: os.close(descriptor)
    class Filter(ctypes.Structure):
        _fields_ = [('code', ctypes.c_ushort), ('jt', ctypes.c_ubyte), ('jf', ctypes.c_ubyte), ('k', ctypes.c_uint32)]
    class Program(ctypes.Structure):
        _fields_ = [('len', ctypes.c_ushort), ('filter', ctypes.POINTER(Filter))]
    # Validate AUDIT_ARCH_X86_64 and reject the x32 syscall ABI before matching numbers.
    instructions = [(0x20,0,0,4),(0x15,1,0,0xc000003e),(0x06,0,0,0x80000000),
                    (0x20,0,0,0),(0x45,0,1,0x40000000),(0x06,0,0,0x80000000)]
    for syscall in [41,42,53,56,57,58,59,62,101,200,234,272,310,311,308,322,435]:
        instructions.extend([(0x15,0,1,syscall),(0x06,0,0,0x00050001)])
    instructions.append((0x06,0,0,0x7fff0000))
    array = (Filter * len(instructions))(*(Filter(*item) for item in instructions))
    program = Program(len(array),array)
    if libc.prctl(22,2,ctypes.byref(program),0,0):
        raise RuntimeError('sandbox_seccomp_failed')


def environment(required):
    # Do not inherit provider keys, tokens, database configuration or cloud credentials.
    return {'PATH': '/usr/local/bin:/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE':'1',
            'PYTHONIOENCODING':'utf-8', 'REVIEW_SANDBOX_REQUIRED':'1' if required else '0',
            **({'SYSTEMROOT':os.environ['SYSTEMROOT']} if 'SYSTEMROOT' in os.environ else {})}
