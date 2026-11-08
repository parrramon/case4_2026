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
    # TODO: Использовать utils.get_parent_path() для получения родителя
    # Проверить валидность нового пути через utils.validate_windows_path()
    # Учесть переход между дисками
    pass

def move_down(current_path: str, target_dir: str) -> Tuple[bool, str]:
    """Navigating to the specified subdirectory in Windows"""
    # TODO: Проверить что target_dir существует через utils.safe_windows_listdir()
    # Сформировать новый путь и проверить через utils.validate_windows_path()
    # Вернуть (True, новый_путь) при успехе, (False, текущий_путь) при ошибке
    pass

def get_windows_special_folders() -> Dict[str, str]:
    """Obtaining paths to special Windows folders"""
    # TODO: Вернуть словарь с путями к папкам:
    # {'Desktop': 'C:\\Users\\...', 'Documents': '...', 'Downloads': '...'}
    # Использовать os.environ для получения USERPROFILE и других переменных
    pass
