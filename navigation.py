import os
from datetime import datetime
from typing import List, Dict, Any, Tuple
import utils  # Импорт функций архитектора


def get_current_drive() -> str:
    """Getting the current Windows drive"""

    current_path = os.getcwd()

    drive, _ = os.path.splitdrive(current_path)

    return drive


def list_available_drives() -> List[str]:
    """Obtaining a list of available Windows drives"""

    if not utils.is_windows_os():
        return []

    try:
        return [drive.rstrip("\\") for drive in os.listdrives()]

    except OSError:
        return []


def list_directory(path: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """Displaying the contents of a directory in Windows"""

    items = utils.safe_windows_listdir(path)

    if not items:
        if not os.path.isdir(path):
            return False, []

        try:
            os.listdir(path)
        except OSError:
            return False, []
    result = []

    try:
        for name in items:
            full_path = os.path.join(path, name)

            try:
                file_info = os.stat(full_path)

                item = {
                    'name': name,
                    'type': 'directory' if os.path.isdir(full_path) else 'file',
                    'size': file_info.st_size,
                    'modified': datetime.fromtimestamp(file_info.st_mtime).strftime('%Y-%m-%d'),
                    'hidden': utils.is_hidden_windows_file(full_path)
                }

                result.append(item)

            except OSError:
                continue

        return True, result

    except OSError:
        return False, []


def format_directory_output(items: List[Dict[str, Any]], current_path: str = "") -> None:
    """Formatted output of directory contents for Windows"""

    print("\nСОДЕРЖИМОЕ ПАПКИ")
    print("-" * 75)
    print(f"{'ТИП':<10} {'НАЗВАНИЕ':<25} {'РАЗМЕР':<12} {'ДАТА ИЗМЕНЕНИЯ':<15}")
    print("-" * 75)

    directories = 0
    files = 0

    # Сначала показываем папки, затем файлы
    items = sorted(items, key=lambda item: (
        item.get('type') != 'directory',
        item.get('name', '').lower()
    ))

    for item in items:
        name = item.get('name', 'Неизвестно')
        item_type = item.get('type', 'file')
        size = item.get('size', 0)
        modified = item.get('modified', 'Неизвестно')
        hidden = item.get('hidden', False)

        if item_type == 'directory':
            type_name = '[ПАПКА]'
            size_text = '—'
            directories += 1
        else:
            type_name = '[ФАЙЛ]'
            size_text = utils.format_size(size)
            files += 1

        hidden_text = ' [СКРЫТЫЙ]' if hidden else ''

        print(
            f"{type_name:<10} "
            f"{name:<25} "
            f"{size_text:<12} "
            f"{modified:<15}"
            f"{hidden_text}"
        )

    print("-" * 75)
    print(f"Всего: {directories} папок, {files} файлов")

    # Если находимся в корне диска, показываем доступные диски
    if current_path:
        drive, _ = os.path.splitdrive(current_path)
        drive_root = drive + os.sep

        if os.path.abspath(current_path) == os.path.abspath(drive_root):
            print("\nДОСТУПНЫЕ ДИСКИ:")

            for available_drive in list_available_drives():
                print(f"  {available_drive}")


def move_up(current_path: str) -> str:
    """Navigating to the parent directory in Windows"""

    parent_path = utils.get_parent_path(current_path)

    if os.path.normpath(parent_path) == os.path.normpath(current_path):

        current_drive = os.path.splitdrive(current_path)[0].upper()

        available_drives = [
            drive.upper() for drive in list_available_drives()
        ]

        if len(available_drives) <= 1:
            return current_path

        if current_drive not in available_drives:
            return current_path

        current_index = available_drives.index(current_drive)

        next_index = (current_index + 1) % len(available_drives)

        new_path = available_drives[next_index] + os.sep

    else:
        new_path = parent_path

    is_valid, error = utils.validate_windows_path(new_path)

    if not is_valid:
        return current_path

    return new_path


def move_down(current_path: str, target_dir: str) -> Tuple[bool, str]:
    """Navigating to the specified subdirectory in Windows"""

    items = utils.safe_windows_listdir(current_path)

    # Проверяем, существует ли целевая папка в текущей папке
    if target_dir.casefold() not in [item.casefold() for item in items]:
        return False, current_path

    new_path = os.path.join(current_path, target_dir)

    # Проверяем, что путь существует и является папкой
    if not os.path.isdir(new_path):
        return False, current_path

    # Проверяем корректность пути
    is_valid, error = utils.validate_windows_path(new_path)

    if not is_valid:
        return False, current_path

    # Проверяем доступность содержимого папки
    items = utils.safe_windows_listdir(new_path)

    if not items:
        try:
            os.listdir(new_path)
        except OSError:
            return False, current_path

    return True, new_path


def get_windows_special_folders() -> Dict[str, str]:
    """Obtaining paths to special Windows folders"""

    user_profile = os.environ.get("USERPROFILE")

    if not user_profile:
        return {}

    folders = {
        "Desktop": os.path.join(user_profile, "Desktop"),
        "Documents": os.path.join(user_profile, "Documents"),
        "Downloads": os.path.join(user_profile, "Downloads"),
        "Pictures": os.path.join(user_profile, "Pictures"),
        "Music": os.path.join(user_profile, "Music"),
        "Videos": os.path.join(user_profile, "Videos")
    }

    return {
        name: path
        for name, path in folders.items()
        if os.path.isdir(path)
    }

