"""Build verificável do material versionado; Docker é acrescentado na etapa 3."""

import hashlib
import io
from pathlib import Path
import subprocess
import tarfile


if __name__ == "__main__":
    output = Path(".artifacts")
    output.mkdir(exist_ok=True)
    filenames = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
    with tarfile.open(output / "foundation.tar.gz", "w:gz") as archive:
        for name in sorted(filter(None, filenames)):
            data = Path(name).read_bytes()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(data))
    with tarfile.open(output / "foundation.tar.gz") as archive:
        for member in archive.getmembers():
            assert archive.extractfile(member).read() == Path(member.name).read_bytes()
    print("source bundle verified", hashlib.sha256((output / "foundation.tar.gz").read_bytes()).hexdigest())
