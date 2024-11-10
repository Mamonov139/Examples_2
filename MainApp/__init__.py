import os
from shutil import rmtree

from AuthManager import current_user, WithCurrentUser, RoleEnum, DepartmentEnum

from Config import configs


def clear_cache():

    if os.path.exists(configs.get('cache').get('base_path')):
        rmtree(configs.get('cache').get('base_path'))

    BASE_PATH = configs.get('downloads').get('excel')
    CACHE_PATH = f"{configs.get('cache').get('base_path')}{os.path.splitdrive(BASE_PATH)[-1]}"
    os.makedirs(CACHE_PATH)


__all__ = (current_user, clear_cache, WithCurrentUser, RoleEnum,DepartmentEnum)
