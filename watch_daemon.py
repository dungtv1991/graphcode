"""
Watch Daemon — Auto-rebuild knowledge graph on .dart file changes.
Debounce 3s: chỉ rebuild sau khi không có thay đổi mới trong 3 giây.
"""
import os
import sys
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class DartFileHandler(FileSystemEventHandler):
    """Watches .dart files, debounces changes, then triggers rebuild."""

    def __init__(self, rebuild_callback, debounce_seconds: float = 3.0):
        super().__init__()
        self.rebuild_callback = rebuild_callback
        self.debounce_seconds = debounce_seconds
        self._timer: threading.Timer | None = None
        self._changed_files: set = set()
        self._lock = threading.Lock()

    def _is_dart_file(self, path: str) -> bool:
        return path.endswith('.dart') and not path.endswith('.g.dart')

    def on_modified(self, event):
        if not event.is_directory and self._is_dart_file(event.src_path):
            self._schedule_rebuild(event.src_path)

    def on_created(self, event):
        if not event.is_directory and self._is_dart_file(event.src_path):
            self._schedule_rebuild(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory and self._is_dart_file(event.src_path):
            self._schedule_rebuild(event.src_path)

    def _schedule_rebuild(self, file_path: str):
        with self._lock:
            self._changed_files.add(file_path)
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self.debounce_seconds, self._do_rebuild)
            self._timer.daemon = True
            self._timer.start()

    def _do_rebuild(self):
        with self._lock:
            files = list(self._changed_files)
            self._changed_files.clear()
            self._timer = None

        if files:
            try:
                print(f"[watch] Rebuilding for {len(files)} changed file(s)...", file=sys.stderr)
                self.rebuild_callback(files)
                print(f"[watch] Rebuild complete.", file=sys.stderr)
            except Exception as e:
                print(f"[watch] Rebuild error: {e}", file=sys.stderr)


def start_watcher(root_dir: str, rebuild_callback) -> Observer:
    """Start watching all khlc-*/lib/ directories for .dart changes.
    
    Args:
        root_dir: Parent directory containing khlc-* repos
        rebuild_callback: Function accepting list of changed file paths
    
    Returns:
        Observer instance (already started as daemon thread)
    """
    handler = DartFileHandler(rebuild_callback)
    observer = Observer()
    observer.daemon = True

    watch_dirs = []
    for d in os.listdir(root_dir):
        if d.startswith('khlc-'):
            lib_path = os.path.join(root_dir, d, 'lib')
            if os.path.isdir(lib_path):
                watch_dirs.append(lib_path)

    if not watch_dirs:
        print(f"[watch] No khlc-*/lib/ dirs found in {root_dir}", file=sys.stderr)
        return observer

    for path in watch_dirs:
        observer.schedule(handler, path, recursive=True)

    observer.start()
    print(f"[watch] Watching {len(watch_dirs)} directories for .dart changes", file=sys.stderr)
    return observer
