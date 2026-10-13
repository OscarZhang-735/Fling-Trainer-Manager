"""Build a Windows standalone distribution without bundling local user data."""

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ENTRY_POINT = ROOT / "TrainerManager.py"
ASSETS = (
    "resource/anon.jpg",
    "resource/shoko.png",
    "resource/favicon.ico",
    "resource/dark/demo.qss",
    "resource/light/demo.qss",
)
REQUIRED_MODULES = ("nuitka", "PyQt5", "qfluentwidgets", "qframelesswindow", "requests", "rarfile", "lxml", "keyboard")


def build_command(output_dir):
    command = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--enable-plugin=pyqt5",
        "--windows-console-mode=disable",
        f"--windows-icon-from-ico={ROOT / 'resource/favicon.ico'}",
        "--include-package-data=qfluentwidgets",
        "--include-package-data=qframelesswindow",
        f"--output-dir={output_dir}",
    ]
    command.extend(f"--include-data-files={ROOT / asset}={asset}" for asset in ASSETS)
    command.append(str(ENTRY_POINT))
    return command


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="build/nuitka",
                        help="Output directory relative to the repository (default: build/nuitka)")
    parser.add_argument("--dry-run", action="store_true", help="Print the Nuitka command without building")
    args = parser.parse_args(argv)

    if sys.platform != "win32":
        parser.error("This build script targets Windows.")
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir = output_dir.resolve()
    dist_dir = output_dir / "TrainerManager.dist"

    missing_assets = [asset for asset in ASSETS if not (ROOT / asset).is_file()]
    if missing_assets:
        parser.error(f"Missing resources: {', '.join(missing_assets)}")
    if dist_dir.exists():
        parser.error(f"Distribution already exists: {dist_dir}. Choose a new --output-dir.")

    command = build_command(output_dir)
    if args.dry_run:
        print(subprocess.list2cmdline(command))
        return 0

    missing_modules = [name for name in REQUIRED_MODULES if importlib.util.find_spec(name) is None]
    if missing_modules:
        parser.error("Missing build dependencies: " + ", ".join(missing_modules)
                     + ". Install requirements.txt and requirements-build.txt into this Python environment.")

    subprocess.run(command, cwd=ROOT, check=True)
    if not (dist_dir / "TrainerManager.exe").is_file():
        parser.error(f"Nuitka did not create the expected executable in {dist_dir}")

    # Import only the standard-library-based storage module. Never copy the
    # development machine's data/data.json into a distribution.
    sys.path.insert(0, str(ROOT))
    from trainer_manager.services.storage import Data

    data_dir = dist_dir / "data"
    data_dir.mkdir(exist_ok=False)
    (data_dir / "data.json").write_text(
        json.dumps(Data().init_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Build ready: {dist_dir / 'TrainerManager.exe'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
