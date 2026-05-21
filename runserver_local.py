import subprocess
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PORT_PATH = BASE_DIR / ".runserver.port"


def main():
    port = PORT_PATH.read_text(encoding="utf-8").strip()
    log_path = BASE_DIR / f"runserver.{int(time.time())}.log"

    with log_path.open("a", encoding="utf-8") as log_file:
        subprocess.run(
            [
                str(BASE_DIR / ".venv" / "Scripts" / "python.exe"),
                "manage.py",
                "runserver",
                f"127.0.0.1:{port}",
                "--noreload",
            ],
            cwd=BASE_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            check=False,
        )


if __name__ == "__main__":
    main()
