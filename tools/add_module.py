import sys
import subprocess
import argparse
from pathlib import Path, PurePosixPath
import tempfile
import tarfile
from integrity import file_hash
import json

def make_git_archive(repo_path: Path, tag: str, output_path: Path):
    try:
        subprocess.run(
            ["git", "archive", "--format=tar.gz", "--output", str(output_path.absolute()), tag],
            cwd=repo_path,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error creating git archive: {e}")
        sys.exit(1)

def extract_module_content(archive_path: Path) -> str:
    with tarfile.open(archive_path, "r:gz") as tar:
        file = tar.extractfile("MODULE.bazel")
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
    parser.add_argument("local_git_repo_path", type=str, help="Path to the local git repository")
    parser.add_argument("remote_blob_path", type=str, help="SCP-compatible path to the remote blob storage folder")
    parser.add_argument("-t", "--tag", type=str, default=None, help="Git tag for the module version")
    parser.add_argument("-p", "--scp_port", type=int, default=22, help="Port for SCP connection (default: 22)")

    args = parser.parse_args()

    module_name = args.module_name
    module_version = args.module_version
    local_git_repo_path = Path(args.local_git_repo_path)
    git_repo_tag = args.tag or f"v{module_version}"

    if not local_git_repo_path.exists():
        print(f"Error: The specified local git repository path '{local_git_repo_path}' does not exist.")
        sys.exit(1)
    
    registry_module_path = MODULES_DIR / module_name / module_version
    if registry_module_path.exists():
        print(f"Error: The module '{module_name}' version '{module_version}' already exists in the registry.")
        sys.exit(1)
    
    tmp_dir = tempfile.TemporaryDirectory()

    archive_file = Path(tmp_dir.name) / f"archive.tar.gz"
    make_git_archive(local_git_repo_path, git_repo_tag, archive_file)

    module_content = extract_module_content(archive_file)
    integrity = file_hash(archive_file)
    partial_hash = integrity[7:17]

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

    with open(registry_module_path / "source.json", "wb+") as f:
        f.write(json.dumps(source_json, indent=2).encode())
