import fnmatch
import os
import stat
from typing import Any, Dict, Iterator, List
import utils
import navigation
import analysis

def _files_in_directory(path: str) -> Iterator[str]:
    """Recursively yield file paths using the navigation module."""
    # Получаем содержимое папки через модуль другого участника.
    success, items = navigation.list_directory(path)
    if not success:
        return

    for item in items:
        file_path = os.path.join(path, item['name'])

        # Ссылки и junctions пропускаем, чтобы не зациклиться.
        if os.path.islink(file_path):
            continue

        if hasattr(os.path, 'isjunction'):
            if os.path.isjunction(file_path):
                continue

        if item['type'] == 'file':
            yield file_path

        elif item['type'] == 'directory':
            # Yield from передаёт файлы из вложенной папки наверх.
            yield from _files_in_directory(file_path)

def find_files_windows(pattern: str, path: str,
                       case_sensitive: bool = False) -> List[str]:
    """Recursively find files matching a Windows wildcard pattern."""

    results = []

    # Общее количество нужно для отображения прогресса поиска.
    success, total = analysis.count_files(path)
    checked = 0

    for file_path in _files_in_directory(path):
        checked += 1
        name = os.path.basename(file_path)

        # По умолчанию Windows-поиск не учитывает регистр.
        if not case_sensitive:
            name = name.casefold()
            search_pattern = pattern.casefold()
        else:
            search_pattern = pattern

        if fnmatch.fnmatchcase(name, search_pattern):
            results.append(file_path)

        # Выводим прогресс не для каждого файла, а раз в 1000.
        if success and total and checked % 1000 == 0:
            print(f"Проверено файлов: {checked} из {total}")

    if success:
        print(f"Поиск завершён. Проверено файлов: {checked} из {total}")

    return results

def find_by_windows_extension(extensions: List[str],
                              path: str) -> List[str]:
    """Recursively find files with selected Windows extensions."""
    # Аналитика заранее собирает статистику по расширениям.
    success, types = analysis.analyze_windows_file_types(path)
    if not success:
        print('Не удалось получить статистику типов файлов.')

    # Приводим '.TXT' и 'txt' к одинаковому виду '.txt'.
    wanted = {'.' + ext.lower().lstrip('.') for ext in extensions}
    results = []

    for file_path in _files_in_directory(path):
        extension = os.path.splitext(file_path)[1].lower()
        if extension in wanted:
            results.append(file_path)

    return results

def find_large_files_windows(min_size_mb: float,
                             path: str) -> List[Dict[str, Any]]:
    """Recursively find files larger than a given size in MB."""

    results = []
    minimum = min_size_mb * 1024 * 1024

    # Используем функцию аналитика для общей оценки размера папки.
    success, total_bytes = analysis.count_bytes(path)
    if success:
        print(f"Общий размер папки: {utils.format_size(total_bytes)}")

    for file_path in _files_in_directory(path):
        try:
            size = os.path.getsize(file_path)
        except OSError:
            # Недоступный файл не должен останавливать поиск.
            continue

        if size >= minimum:
            results.append({
                'path': file_path,
                'size_mb': round(size / (1024 * 1024), 2),
                'type': os.path.splitext(file_path)[1].lower()
            })

    return results

def find_windows_system_files(path: str) -> List[str]:
    """Find Windows executables and libraries in system folders."""

    results = []
    extensions = {'.exe', '.dll', '.sys'}

    # Системная папка берётся из Windows, а не из имени диска.
    windows_dir = os.environ.get('SystemRoot', 'C:\\Windows')
    system_dirs = [windows_dir]

    # Получаем специальные папки через модуль навигации.
    special = navigation.get_windows_special_folders()
    for name, folder in special.items():
        if name.lower() in {'windows', 'system32', 'syswow64'}:
            system_dirs.append(folder)

    for file_path in _files_in_directory(path):
        extension = os.path.splitext(file_path)[1].lower()
        if extension not in extensions:
            continue

        # Проверяем, лежит ли файл внутри системной папки.
        in_system_dir = False
        for folder in system_dirs:
            try:
                common = os.path.commonpath([file_path, folder])
                if os.path.normcase(common) == os.path.normcase(folder):
                    in_system_dir = True
                    break
            except ValueError:
                # Пути на разных дисках не имеют общего корня.
                continue

        try:
            attrs = os.stat(file_path).st_file_attributes
            system_attr = bool(attrs & stat.FILE_ATTRIBUTE_SYSTEM)
        except (OSError, AttributeError):
            system_attr = False

        if in_system_dir or system_attr:
            results.append(file_path)

    return results

def format_windows_search_results(results: List,
                                  search_type: str) -> None:
    """Print Windows search results with file sizes and attributes."""

    print(f"\nРезультаты поиска: {search_type}")
    print('-' * 50)

    if not results:
        print('Ничего не найдено.')
        return

    # Получаем сводку атрибутов через модуль аналитика.
    paths = [item['path'] if isinstance(item, dict) else item
             for item in results]
    folders = {os.path.dirname(file_path) for file_path in paths}
    for folder in folders:
        try:
            stats = analysis.get_windows_file_attributes_stats(folder)
            print(f"Атрибуты в {folder}: {stats}")
        except OSError:
            pass

    for number, item in enumerate(results, 1):
        file_path = item['path'] if isinstance(item, dict) else item
        try:
            size = utils.format_size(os.path.getsize(file_path))
            attrs = os.stat(file_path).st_file_attributes
        except (OSError, AttributeError):
            size = 'недоступен'
            attrs = 0

        flags = []
        if attrs & stat.FILE_ATTRIBUTE_HIDDEN:
            flags.append('скрытый')

        if attrs & stat.FILE_ATTRIBUTE_SYSTEM:
            flags.append('системный')

        if attrs & stat.FILE_ATTRIBUTE_READONLY:
            flags.append('только чтение')

        print(f"{number}. {file_path}")
        print(f"   Размер: {size}")

        if flags:
            print(f"   Атрибуты: {', '.join(flags)}")

    print(f"Всего найдено: {len(results)}")

def search_menu_handler(current_path: str) -> bool:
    """Show the search menu and run the selected search."""

    while True:
        print('\nПОИСК ФАЙЛОВ')
        print(f"Папка: {current_path}")
        print('1. По названию')
        print('2. По расширению')
        print('3. По размеру')
        print('4. Системные файлы')
        print('5. Статистика папки')
        print('0. Вернуться в главное меню')

        choice = input('Команда: ').strip()

        match choice:

            case '1':
                pattern = input('Шаблон (* и ?): ').strip()
                if not pattern:
                    print('Введите шаблон.')
                    continue
                results = find_files_windows(pattern, current_path)
                format_windows_search_results(results, 'по названию')

            case '2':
                value = input('Расширения через запятую: ')
                extensions = [part.strip() for part in value.split(',')
                              if part.strip()]
                if not extensions:
                    print('Введите расширения.')
                    continue
                results = find_by_windows_extension(extensions,
                                                    current_path)
                format_windows_search_results(results, 'по расширению')

            case '3':
                try:
                    minimum = float(input('Минимум в МБ: '))
                    if minimum < 0:
                        raise ValueError
                except ValueError:
                    print('Введите неотрицательное число.')
                    continue
                results = find_large_files_windows(minimum,
                                                   current_path)
                format_windows_search_results(results, 'по размеру')

            case '4':
                results = find_windows_system_files(current_path)
                format_windows_search_results(results, 'системные файлы')

            case '5':
                analysis.show_windows_directory_stats(current_path)

            case '0':
                return True

            case _:
                print('Неизвестная команда.')
