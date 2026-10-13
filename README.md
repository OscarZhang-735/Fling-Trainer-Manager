# Trainer Manager

Trainer Manager is a Windows desktop app for finding, downloading, updating, and launching FLiNG trainers. It searches the main and archive catalogs, keeps a local trainer library, and shows download progress and cover previews.

## Run from source

From the project root, with Python 3.12 installed:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## Build locally

Install Nuitka in the same environment, then run the Windows standalone build:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe scripts\build_nuitka.py
```

Run `build/nuitka/TrainerManager.dist/TrainerManager.exe` from the resulting folder. Distribute the entire `TrainerManager.dist` folder. For another build, pass a new `--output-dir` because the script does not overwrite an existing distribution.
