from pathlib import Path

import typer
from typer import Typer, Option
from watchdog.observers import Observer

from modules.file_handler import Handler
from modules.settings import settings

commands = Typer()


@commands.command()
def listen_and_send(
    to: str = Option(None, "--to", help="Recipient. Defaults to SMTP__TO from the environment."),
    path: Path = Option("data", help="Directory to watch."),
    extensions: list[str] = Option(["pdf"], "--extensions", "-e", help="Extensions to watch. Repeat the option for several."),
):

    recipient = to or settings.smtp.to
    if not recipient:
        raise typer.BadParameter("No recipient: pass --to or set SMTP__TO.")

    suffixes = {"." + extension.lower().lstrip(".") for extension in extensions}

    sent_dir = path / "sent"
    failed_dir = path / "failed"
    sent_dir.mkdir(parents=True, exist_ok=True)
    failed_dir.mkdir(parents=True, exist_ok=True)

    handler = Handler(suffixes, recipient, sent_dir, failed_dir)

    observer = Observer()
    observer.schedule(handler, str(path), recursive=False)
    observer.start()
    print(f"listening on {path} for {', '.join(sorted(suffixes))} -> {recipient}", flush=True)

    for entry in sorted(path.iterdir()):
        if entry.is_file():
            handler.handle(entry)

    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
