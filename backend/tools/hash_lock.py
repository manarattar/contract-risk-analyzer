"""Attach official PyPI artifact hashes to pip-compile's exact resolved pins.

Usage: python backend/tools/hash_lock.py RESOLVED.txt LOCK.txt
Resolve dependencies with pip-compile first; this script does not resolve versions.
Uses HTTPS metadata, fails closed on unexpected input and writes only on success.
"""
import concurrent.futures
import json
from pathlib import Path
import re
import sys
import urllib.request


def hashed_pin(line):
    match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)(; .+)?", line)
    if not match:
        raise ValueError(f"Expected an exact package pin: {line}")
    name, version, _ = match.groups()
    with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=60) as response:
        metadata = json.load(response)
    hashes = sorted({item["digests"]["sha256"] for item in metadata["urls"] if not item.get("yanked")})
    if not hashes or any(not re.fullmatch(r"[0-9a-f]{64}", value) for value in hashes):
        raise ValueError(f"No valid published hashes for {name}")
    return line + " \\\n" + " \\\n".join("    --hash=sha256:" + value for value in hashes)


def main():
    source, target = map(Path, sys.argv[1:])
    pins = [line.strip() for line in source.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(hashed_pin, pins))
    target.write_text("# Exact dependencies resolved with pip-compile; artifact SHA256 values from PyPI HTTPS metadata.\n"
                      "# Regenerate from requirements.in / requirements-test.in; see operations.md.\n\n"
                      + "\n".join(rows) + "\n", encoding="utf-8")
    print(f"Wrote {target}: {len(rows)} pinned packages with published artifact hashes.")


if __name__ == "__main__":
    main()
