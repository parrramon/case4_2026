import os
import platform
from pathlib import Path
from typing import Union, List, Tuple
import ctypes

FILE_ATTRIBUTE_HIDDEN = 0x02

PathString = Union[str, Path]

def is_windows_os() -> bool:
    """Checking that the program is running on Windows."""
    return platform.system() == "Windows"


def validate_windows_path(path: PathString) -> Tuple[bool, str]:
    """Checking the correctness of the Windows path"""

    path = str(path)

    if not path:
        return False, "Путь не может быть пустым"

    forbidden_chars = '/<>:"|?*'

    for index, char in enumerate(path):
        if char in forbidden_chars:
            if char == ":" and index == 1 and path[0].isalpha():
                continue

            return False, "Путь содержит запрещённые символы"

    if len(path) > 260:
        return False, "Путь превышает допустимую длину (260 символов)"

    if not os.path.exists(path):
        return False, "Указанный путь не существует"

    return True, ""


def format_size(size_bytes: int) -> str:
    """Formatting the file size in a readable form for Windows"""

    if size_bytes < 1024:
        return f"{size_bytes} B"

    size = size_bytes / 1024
    units = ["KB", "MB", "GB", "TB"]

    for unit in units:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size:.1f} PB"


def get_parent_path(path: PathString) -> str:
    """Obtaining the parent directory, taking into account Windows paths."""

    path = os.path.normpath(str(path))

    parent = os.path.dirname(path)

    if not parent:
        return path

    if len(parent) == 2 and parent[1] == ":":
        parent += os.sep

    return parent


def safe_windows_listdir(path: PathString) -> List[str]:
    """Secure retrieval of directory contents in Windows"""

    try:
        return os.listdir(path)

    except PermissionError:
        return []

    except FileNotFoundError:
        return []

    except OSError:
        return []


def is_hidden_windows_file(path: PathString) -> bool:
    """Checking whether a file is hidden in Windows"""

    if not is_windows_os():
        return False

    try:
        attributes = ctypes.windll.kernel32.GetFileAttributesW(str(path))

        if attributes == -1:
            return False

        return bool(attributes & FILE_ATTRIBUTE_HIDDEN)

    except (OSError, AttributeError):
        return False