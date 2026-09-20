"""Atomic saves and a locked recovery file for each concurrently open workspace."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid


def atomic_write(path, text):
    path = Path(path)
    # Preserve symlinks: replace their target instead of replacing the link itself.
    if path.is_symlink():
        path = path.resolve()
    temp = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='',
                                         dir=path.parent, delete=False) as stream:
            temp = stream.name
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            os.chmod(temp, path.stat().st_mode)
        os.replace(temp, path)
    finally:
        if temp and os.path.exists(temp):
            os.unlink(temp)


def fingerprint(path):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


class SessionStore:
    """OS locks prevent two running app instances from replacing each other's tabs."""
    def __init__(self, settings_path):
        self.folder = Path(settings_path).parent / 'sessions'
        self.folder.mkdir(parents=True, exist_ok=True)
        self.lock = None
        self.path = None
        candidates = sorted(self.folder.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
        for path in candidates:
            if self._claim(path):
                break
        if self.path is None:
            self._claim(self.folder / (uuid.uuid4().hex + '.json'))

    def _claim(self, path):
        stream = open(str(path) + '.lock', 'a+b')
        try:
            stream.seek(0)
            if os.name == 'nt':
                import msvcrt
                # Windows byte-range locks may extend past EOF.
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            stream.close()
            return False
        self.lock, self.path = stream, path
        return True

    def load(self):
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or not isinstance(data.get('tabs'), list):
                return {}
            data['tabs'] = [tab for tab in data['tabs'] if isinstance(tab, dict)
                            and isinstance(tab.get('code'), str)
                            and tab.get('lang') in ('c', 'cpp')
                            and isinstance(tab.get('name'), str)
                            and (tab.get('path') is None or isinstance(tab.get('path'), str))]
            return data
        except (OSError, ValueError, TypeError):
            return {}

    def save(self, data):
        atomic_write(self.path, json.dumps(data, ensure_ascii=False))

    def close(self):
        if self.lock:
            self.lock.close()
            self.lock = None
