"""Small shared directory helper; does not suppress access-control failures."""

def ensure_directory(path):
    if path.is_symlink():
        raise ValueError('Data directories cannot be symlinks')
    if path.is_dir():
        return
    if path.parent != path:
        ensure_directory(path.parent)
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        if path.is_symlink() or not path.is_dir():
            raise
