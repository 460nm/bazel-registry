import sys
import hashlib
import base64
from pathlib import Path
import requests

def file_hash(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as file:
        while True:
            data = file.read(65536)
            if not data:
                break
            sha256_hash.update(data)
    return "sha256-" + base64.b64encode(sha256_hash.digest()).decode()

def url_hash(url: str) -> str:
    sha256_hash = hashlib.sha256()
    with requests.get(url, stream=True) as resp:
        resp.raise_for_status()
        while True:
            data = resp.raw.read(65536)
            if not data:
                break
            sha256_hash.update(data)
    return "sha256-" + base64.b64encode(sha256_hash.digest()).decode()

if __name__ == "__main__" and len(sys.argv) > 1:
    path = Path(sys.argv[1])
    if path.exists():
        print(file_hash(path))
    else:
        print(url_hash(sys.argv[1]))

