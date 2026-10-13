"""Entry point for source runs and the Nuitka standalone build."""

import os
from pathlib import Path


# Existing UI and storage code resolve data and resource paths from cwd.
# Nuitka places this entry point beside the distributed resource directory.
os.chdir(Path(__file__).resolve().parent)

from trainer_manager.application import main  # noqa: E402


if __name__ == "__main__":
    main()
