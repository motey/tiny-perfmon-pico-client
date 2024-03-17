from pathlib import Path, PurePath

pico_path = "/media/tim/CIRCUITPY/"
source_dir = "./pico-client"
extra_files = ["font5x8.bin"]
allowed_files = ["boot.py", "code.py", "main.py"]


def upload(overwrite: bool = False, extrafiles_exist_ok=True):
    p = Path(pico_path)
    if not p.exists():
        raise LookupError(f"Pico not found at {pico_path}")
    local_dir = Path(source_dir)
    for local_dir_obj in local_dir.iterdir():
        if not local_dir_obj.exists() or local_dir_obj.name not in allowed_files:
            continue
        local_file_path = local_dir_obj
        remote_file_path = Path(PurePath(p, local_dir_obj.name))

        if not local_file_path.exists():
            raise LookupError(
                f"Could not find local file {local_file_path} for upload to {pico_path}"
            )
        if remote_file_path.exists() and overwrite:
            remote_file_path.unlink()
        elif remote_file_path.exists():
            raise ValueError(
                f"Target '{remote_file_path}' already exists. Enable 'overwrite' if you want to replace it with {local_file_path}"
            )
        remote_file_path.write_text(local_file_path.read_text())
    for xfile in extra_files:
        local_file_path = local_dir_obj
        remote_file_path = Path(PurePath(p, local_dir_obj.name))
        print("TODO + libs")


upload(overwrite=True)
