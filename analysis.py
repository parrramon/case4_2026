import os
import stat
from typing import Tuple, Dict, Any

import utils
import navigation


def count_files(path: str) -> Tuple[bool, int]:
    """Recursive file count in the Windows directory."""

    success, items = navigation.list_directory(path)

    if not success:
        return False, 0

    total = 0

    for item in items:
        item_path = os.path.join(path, item["name"])

        if os.path.islink(item_path):
            continue

        if item["type"] == "file":
            total += 1

        elif item["type"] == "directory":
            if os.path.isjunction(item_path):
                continue

            success, subfolder_count = count_files(item_path)

            if not success:
                return False, 0

            total += subfolder_count

    return True, total


def count_bytes(path: str) -> Tuple[bool, int]:
    """Recursive calculation of the total file size in bytes."""

    success, items = navigation.list_directory(path)

    if not success:
        return False, 0

    total_bytes = 0

    for item in items:
        item_path = os.path.join(path, item["name"])

        if os.path.islink(item_path):
            continue

        if item["type"] == "file":
            total_bytes += item["size"]

        elif item["type"] == "directory":
            if os.path.isjunction(item_path):
                continue

            success, subfolder_bytes = count_bytes(item_path)

            if not success:
                return False, 0

            total_bytes += subfolder_bytes

    return True, total_bytes


def analyze_windows_file_types(
        path: str) -> Tuple[bool, Dict[str, Dict[str, Any]]]:
    """Analysis of file types by extensions in Windows."""

    success, items = navigation.list_directory(path)

    if not success:
        return False, {}

    statistics = {}

    for item in items:
        item_path = os.path.join(path, item["name"])

        if os.path.islink(item_path):
            continue

        if item["type"] == "file":
            name = item["name"]
            size = item["size"]

            extension = os.path.splitext(name)[1].lower()

            if not extension:
                extension = "[без расширения]"

            if extension not in statistics:
                statistics[extension] = {
                    "count": 0,
                    "size": 0
                }

            statistics[extension]["count"] += 1
            statistics[extension]["size"] += size

        elif item["type"] == "directory":
            if os.path.isjunction(item_path):
                continue

            success, subfolder_stats = analyze_windows_file_types(item_path)

            if not success:
                return False, {}

            for extension, data in subfolder_stats.items():
                if extension not in statistics:
                    statistics[extension] = {
                        "count": 0,
                        "size": 0
                    }

                statistics[extension]["count"] += data["count"]
                statistics[extension]["size"] += data["size"]

    return True, statistics


def get_windows_file_attributes_stats(path: str) -> Dict[str, int]:
    """Statistics of Windows file attributes."""

    statistics = {
        "hidden": 0,
        "system": 0,
        "readonly": 0
    }

    success, items = navigation.list_directory(path)

    if not success:
        return statistics

    for item in items:
        item_path = os.path.join(path, item["name"])

        if os.path.islink(item_path):
            continue

        if item["type"] == "file":
            try:
                file_info = os.stat(item_path, follow_symlinks=False)
                attributes = file_info.st_file_attributes

                if attributes & stat.FILE_ATTRIBUTE_HIDDEN:
                    statistics["hidden"] += 1

                if attributes & stat.FILE_ATTRIBUTE_SYSTEM:
                    statistics["system"] += 1

                if attributes & stat.FILE_ATTRIBUTE_READONLY:
                    statistics["readonly"] += 1

            except (OSError, AttributeError):
                continue

        elif item["type"] == "directory":
            if os.path.isjunction(item_path):
                continue

            subfolder_stats = get_windows_file_attributes_stats(item_path)

            for attribute in statistics:
                statistics[attribute] += subfolder_stats[attribute]

    return statistics


def show_windows_directory_stats(path: str) -> bool:
    """Output of the Windows Catalyst statistics."""

    success, file_count = count_files(path)
    if not success:
        print("Ошибка при подсчёте файлов.")
        return False

    success, total_bytes = count_bytes(path)
    if not success:
        print("Ошибка при подсчёте размера.")
        return False

    success, file_types = analyze_windows_file_types(path)
    if not success:
        print("Ошибка при анализе расширений.")
        return False

    attributes = get_windows_file_attributes_stats(path)

    directory_count = 0
    largest_files = []
    visited = set()

    def collect_info(current_path: str) -> bool:
        nonlocal directory_count

        real_path = os.path.normcase(
            os.path.realpath(current_path)
        )

        if real_path in visited:
            return True

        visited.add(real_path)

        directory_success, items = navigation.list_directory(current_path)
        if not directory_success:
            return False

        for item in items:
            item_path = os.path.join(
                current_path, item["name"]
            )

            if os.path.islink(item_path):
                continue

            if item["type"] == "file":
                largest_files.append(
                    (item_path, item["size"])
                )

            elif item["type"] == "directory":
                if os.path.isjunction(item_path):
                    continue

                directory_count += 1

                if not collect_info(item_path):
                    return False

        return True

    if not collect_info(path):
        print("Ошибка при обходе каталогов.")
        return False

    largest_files.sort(
        key=lambda file: file[1],
        reverse=True
    )

    print("\nСТАТИСТИКА КАТАЛОГА WINDOWS")
    print("-" * 50)
    print(f"Путь: {path}")
    print(f"Количество файлов: {file_count}")
    print(f"Количество папок: {directory_count}")
    print(f"Общий размер: {utils.format_size(total_bytes)}")

    print("\nСТАТИСТИКА ПО РАСШИРЕНИЯМ")
    for extension, data in sorted(file_types.items()):
        size_text = utils.format_size(data["size"])
        print(f"{extension}: {data['count']} шт., {size_text}")

    print("\nАТРИБУТЫ ФАЙЛОВ")
    for attribute, count in attributes.items():
        print(f"{attribute}: {count}")

    print("\nКРУПНЕЙШИЕ ФАЙЛЫ")
    for file_path, size in largest_files[:5]:
        print(f"{file_path}: {utils.format_size(size)}")

    print("-" * 50)

    return True