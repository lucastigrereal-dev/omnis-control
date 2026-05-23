import os

OBSIDIAN_VAULT = os.path.normpath(os.path.expanduser(
    "~/Desktop/ARQUIVOS_MANUS_CLAUDE/OBSIDIAN/ComandoCentral"
))
TIMEOUT = 10


def _count_md_files(root: str) -> tuple[int, list[str], bool]:
    """Count .md files and list top-level folders using os.walk.

    Returns (count, top_folders, partial_flag).
    """
    md_count = 0
    top_folders = []
    partial = False

    try:
        for entry in os.scandir(root):
            if entry.is_dir():
                top_folders.append(entry.path)
    except OSError:
        pass

    try:
        for dirpath, _dirnames, filenames in os.walk(root):
            for f in filenames:
                if f.endswith(".md"):
                    md_count += 1
    except OSError:
        partial = True

    top_names = sorted(os.path.basename(p) for p in top_folders)
    return md_count, top_names[:15], partial


def check() -> dict[str, object]:
    vault_exists = os.path.isdir(OBSIDIAN_VAULT)

    if not vault_exists:
        return {
            "vault_found": False,
            "vault_path": OBSIDIAN_VAULT,
            "error": "Vault não encontrado no caminho esperado",
        }

    md_count, top_folders, partial = _count_md_files(OBSIDIAN_VAULT)

    return {
        "vault_found": True,
        "vault_path": OBSIDIAN_VAULT,
        "md_file_count": md_count,
        "md_count_partial": partial,
        "top_folders": top_folders,
    }
