"""Shared startup configuration snapshot and fonts (legacy semantics)."""

from pathlib import Path

from trainer_manager import services as utils

Font = utils.Font()
PREP = utils.Data.load_config("data/data.json")
USER_NAME = PREP["config"]["program"]["username"]
USER_AVATAR = PREP["config"]["program"]["user_avatar"]
ICON = str(Path(__file__).resolve().parent.parent / "resource" / "favicon.ico")
TITLE = PREP["config"]["program"]["title"]
NET = PREP["config"]["program"]["connection_allow"]
