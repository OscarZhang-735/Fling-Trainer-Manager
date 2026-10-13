"""Desktop entry point and compatibility exports for existing imports."""

from trainer_manager.application import exit_handler, main, setup_check
from trainer_manager.runtime import Font, PREP, USER_NAME, USER_AVATAR, ICON, TITLE, NET
from trainer_manager.ui.common import Error, WorkerThread, Widget
from trainer_manager.ui.search import SearchWidget
from trainer_manager.ui.library import LibraryWidget
from trainer_manager.ui.games import GameWidget
from trainer_manager.ui.settings import SettingWidget
from trainer_manager.ui.saves import SavingWidget
from trainer_manager.ui.patches import PatchWidget
from trainer_manager.ui.navigation import AvatarWidget, CustomTitleBar
from trainer_manager.ui.window import Window


if __name__ == "__main__":
    main()
