import sys
import subprocess
import argparse
from pathlib import Path, PurePosixPath
import tempfile
import tarfile
from integrity import file_hash
import json
import urllib.request

def download_archive(archive_url: str) -> Path:
    filename, _ = urllib.request.urlretrieve(archive_url)
    return Path(filename)

def extract_module_content(archive_path: Path, prefix: str | None) -> str:
    with tarfile.open(archive_path, "r:gz") as tar:
        file = tar.extractfile(("" if str is None else (prefix + "/")) + "MODULE.bazel")
        if file is None:
            print("Error: MODULE.bazel file not found in the archive.")
            sys.exit(1)
        return file.read().decode()

def upload_to_blob_storage(local_path: Path, remote_path: str, scp_port: int = 22):
    try:
        ssh_login = remote_path.split(":")[0]
        ssh_path = str(PurePosixPath(remote_path.split(":")[1]).parent)

        subprocess.run(
            ["ssh", "-p", str(scp_port), ssh_login, f"mkdir -p {ssh_path}"],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

        subprocess.run(
            ["scp", "-P", str(scp_port), str(local_path), remote_path],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error uploading to blob storage: {e}")
        sys.exit(1)

MODULES_DIR = Path(__file__).parent.parent / "modules"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add a module to the registry.")
    parser.add_argument("module_name", type=str, help="Name of the module to add")
    parser.add_argument("module_version", type=str, help="Version of the module to add")
    parser.add_argument("archive_url", type=str, help="Path to the archive URL")
    parser.add_argument("remote_blob_path", type=str, help="SCP-compatible path to the remote blob storage folder")
    parser.add_argument("-p", "--scp_port", type=int, default=22, help="Port for SCP connection (default: 22)")
    parser.add_argument("--prefix", type=str, help="Archive prefix")

    args = parser.parse_args()

    module_name = args.module_name
    module_version = args.module_version
    archive_url = args.archive_url
    archive_prefix = args.prefix

    registry_module_path = MODULES_DIR / module_name / module_version
    if registry_module_path.exists():
        print(f"Error: The module '{module_name}' version '{module_version}' already exists in the registry.")
        sys.exit(1)
    
    archive_file = download_archive(archive_url)

    module_content = extract_module_content(archive_file, archive_prefix)
    integrity = file_hash(archive_file)
    partial_hash = integrity[7:17].replace("/", "_")

    registry_module_path.mkdir(parents=True, exist_ok=True)
    with open(registry_module_path / "MODULE.bazel", "wb+") as f:
        f.write(module_content.encode())
    
    blob_path = f"{module_name}/{module_version}-{partial_hash}.tar.gz"
    remote_blob_path = f"{args.remote_blob_path}/{blob_path}"

    upload_to_blob_storage(archive_file, remote_blob_path, args.scp_port)
    
    source_json = {
        "url": f"https://bazel.stevenlr.com/blobs/{blob_path}",
        "integrity": integrity,
    }

    if archive_prefix is not None:
        source_json["strip_prefix"] = archive_prefix

    with open(registry_module_path / "source.json", "wb+") as f:
        f.write(json.dumps(source_json, indent=2).encode())
