import shutil
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler

from modules.mailer import send_file


def wait_until_written(path: Path, timeout: float = 60.0) -> bool:
    deadline = time.monotonic() + timeout
    previous = -1
    while time.monotonic() < deadline:
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            return False
        if size == previous:
            return True
        previous = size
        time.sleep(0.5)
    return False


def move_aside(path: Path, target_dir: Path) -> Path:
    destination = target_dir / path.name
    if destination.exists():
        stamp = time.strftime("%Y%m%d-%H%M%S")
        destination = target_dir / f"{path.stem}.{stamp}{path.suffix}"
        counter = 1
        while destination.exists():
            destination = target_dir / f"{path.stem}.{stamp}-{counter}{path.suffix}"
            counter += 1
    shutil.move(str(path), str(destination))
    return destination


class Handler(FileSystemEventHandler):
    def __init__(self, suffixes: set[str], to: str, sent_dir: Path, failed_dir: Path):
        self.suffixes = suffixes
        self.to = to
        self.sent_dir = sent_dir
        self.failed_dir = failed_dir
        self._lock = threading.Lock()
        self._claimed: set[Path] = set()

    def on_created(self, event):
        if event.is_directory:
            return
        self.handle(Path(event.src_path))

    def on_moved(self, event):
        if event.is_directory:
            return
        self.handle(Path(event.dest_path))

    def _claim(self, path: Path) -> bool:
        with self._lock:
            if path in self._claimed:
                return False
            self._claimed.add(path)
            return True

    def _release(self, path: Path) -> None:
        with self._lock:
            self._claimed.discard(path)

    def handle(self, path: Path) -> None:
        if path.suffix.lower() not in self.suffixes:
            return
        if path.parent in (self.sent_dir, self.failed_dir):
            return
        if not path.exists():
            return
        if not self._claim(path):
            return

        try:
            if not wait_until_written(path):
                print(f"skipped {path.name}: still being written", flush=True)
                return

            try:
                send_file(path, self.to)
            except Exception as error:
                print(f"failed {path.name}: {error}", flush=True)
                self._quarantine(path, self.failed_dir)
            else:
                print(f"sent {path.name}", flush=True)
                self._quarantine(path, self.sent_dir)
        finally:
            self._release(path)

    def _quarantine(self, path: Path, target_dir: Path) -> None:
        try:
            move_aside(path, target_dir)
        except OSError as error:
            print(f"could not move {path.name} to {target_dir.name}: {error}", flush=True)
