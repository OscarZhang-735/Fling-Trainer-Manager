"""Shared startup configuration snapshot and fonts (legacy semantics)."""

from trainer_manager import services as utils

Font = utils.Font()
PREP = utils.Data.json_read("data/data.json")
USER_NAME = PREP["config"]["program"]["username"]
USER_AVATAR = PREP["config"]["program"]["user_avatar"]
ICON = PREP["config"]["program"]["icon"]
TITLE = PREP["config"]["program"]["title"]
NET = PREP["config"]["program"]["connection_allow"]
