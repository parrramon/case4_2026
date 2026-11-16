import fnmatch, os, stat
from typing import Any, Dict, List
import analysis, navigation, utils

def _get_files(path: str) -> List[str]:
    """Recursively collect file paths from Windows folders."""

    # Получаем содержимое папки через модуль навигации.
    success, items = navigation.list_directory(path)

    if not success:
        return []

    files = []

    for item in items:
        file_path = os.path.join(path, item['name'])

        # Пропускаем ссылки, чтобы не попасть в бесконечный цикл.
        if os.path.islink(file_path) or os.path.isjunction(file_path):
            continue

        if item['type'] == 'file':
            files.append(file_path)

        elif item['type'] == 'directory':
            # Вызываем эту же функцию для вложенной папки.
            files.extend(_get_files(file_path))

    return files

def _inside_folder(file_path: str, folder: str) -> bool:
    """Check whether a file is located inside a folder."""

    # Сравниваем полные пути без учёта регистра Windows.
    file_path = os.path.normcase(os.path.abspath(file_path))
    folder = os.path.normcase(os.path.abspath(folder))

    try:
        return os.path.commonpath([file_path, folder]) == folder
    except ValueError:
        # Пути на разных дисках не имеют общего корня.
        return False

def find_files_windows(pattern: str, path: str, case_sensitive: bool = False) -> List[str]:
    """Find files by Windows wildcard patterns."""

    # Аналитик считает файлы для отображения прогресса.
    success, total = analysis.count_files(path)
    checked = 0
    results = []

    if not case_sensitive:
        pattern = pattern.casefold()

    for file_path in _get_files(path):
        checked += 1
        name = os.path.basename(file_path)

        # В Windows поиск обычно не зависит от регистра букв.
        if not case_sensitive:
            name = name.casefold()

        if fnmatch.fnmatchcase(name, pattern):
            results.append(file_path)

        if success and checked % 1000 == 0:
            print(f'Проверено файлов: {checked} из {total}')

    if success:
        print(f'Поиск завершён. Проверено файлов: {checked} из {total}')

    return results

def find_by_windows_extension(extensions: List[str], path: str) -> List[str]:
    """Find files with selected Windows extensions."""

    # Приводим расширения к виду '.txt', '.exe' и т. д.
    wanted = []

    for extension in extensions:
        extension = extension.strip().lower()

        if not extension:
            continue

        if not extension.startswith('.'):
            extension = '.' + extension

        wanted.append(extension)

    if not wanted:
        return []

    # Проверяем статистику, чтобы избежать ненужного поиска.
    success, types = analysis.analyze_windows_file_types(path)

    if success and not any(extension in types for extension in wanted):
        return []

    results = []

    for file_path in _get_files(path):
        extension = os.path.splitext(file_path)[1].lower()

        if extension in wanted:
            results.append(file_path)

    return results

def find_large_files_windows(min_size_mb: float, path: str) -> List[Dict[str, Any]]:
    """Find files at least as large as the given size in MB."""

    # Переводим мегабайты в байты для сравнения размеров.
    minimum = min_size_mb * 1024 * 1024
    results = []

    # Если вся папка меньше порога, подходящих файлов нет.
    success, total_bytes = analysis.count_bytes(path)

    if success and total_bytes < minimum:
        return []

    for file_path in _get_files(path):
        try:
            size = os.path.getsize(file_path)
        except OSError:
            # Недоступные файлы пропускаем.
            continue

        if size >= minimum:
            results.append({
                'path': file_path,
                'size_mb': round(size / (1024 * 1024), 2),
                'type': os.path.splitext(file_path)[1].lower()
            })

    return results

def find_windows_system_files(path: str) -> List[str]:
    """Find Windows system executables, libraries and drivers."""

    # Учитываем Windows и папки установленных программ.
    system_folders = [
        os.environ.get('SystemRoot', 'C:\\Windows'),
        os.environ.get('ProgramFiles', 'C:\\Program Files'),
        os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')
    ]

    # Пользовательские специальные папки не считаем системными.
    user_folders = navigation.get_windows_special_folders().values()
    extensions = ['.exe', '.dll', '.sys']
    results = []

    for file_path in _get_files(path):
        extension = os.path.splitext(file_path)[1].lower()

        if extension not in extensions:
            continue

        in_system_folder = any(_inside_folder(file_path, folder) for folder in system_folders)
        in_user_folder = any(_inside_folder(file_path, folder) for folder in user_folders)

        try:
            attributes = os.stat(file_path).st_file_attributes
            is_system = bool(attributes & stat.FILE_ATTRIBUTE_SYSTEM)
        except (OSError, AttributeError):
            is_system = False

        # Ищем файлы из системных папок или с системным атрибутом.
        if is_system or (in_system_folder and not in_user_folder):
            results.append(file_path)

    return results

def format_windows_search_results(results: List, search_type: str) -> None:
    """Print found files with sizes and Windows attributes."""

    print(f'\nРезультаты поиска: {search_type}')
    print('-' * 50)

    if not results:
        print('Ничего не найдено.')
        return

    paths = []

    for number, item in enumerate(results, 1):
        # Поиск по размеру возвращает словари, остальные — строки.
        file_path = item['path'] if isinstance(item, dict) else item
        paths.append(file_path)

        try:
            size = utils.format_size(os.path.getsize(file_path))
        except OSError:
            size = 'Недоступен'

        try:
            attributes = os.stat(file_path).st_file_attributes
        except (OSError, AttributeError):
            attributes = 0

        flags = []

        if utils.is_hidden_windows_file(file_path):
            flags.append('скрытый')

        if attributes & stat.FILE_ATTRIBUTE_SYSTEM:
            flags.append('системный')

        if attributes & stat.FILE_ATTRIBUTE_READONLY:
            flags.append('только чтение')

        print(f'{number}. {file_path}')
        print(f'   Размер: {size}')

        if flags:
            flags_text = ', '.join(flags)
            print(f'   Атрибуты: {flags_text}')

    print(f'Всего найдено: {len(results)}')

    # Показываем общую статистику атрибутов для области поиска.
    try:
        folders = [os.path.dirname(file_path) for file_path in paths]
        common_folder = os.path.commonpath(folders)
        stats = analysis.get_windows_file_attributes_stats(common_folder)
        print(f'Атрибуты в папке {common_folder} и её подпапках: {stats}')
    except ValueError:
        # Файлы на разных дисках не имеют общего каталога.
        pass

def search_menu_handler(current_path: str) -> bool:
    """Run one search menu action and return whether to continue."""

    # Показываем команды поиска и обрабатываем выбор пользователя.
    print('\nПОИСК ФАЙЛОВ')
    print(f'Текущая папка: {current_path}')
    print('1. По названию')
    print('2. По расширению')
    print('3. По размеру')
    print('4. Системные файлы')
    print('5. Статистика папки')
    print('0. Назад')

    choice = input('Команда: ').strip()

    match choice:
        case '1':
            pattern = input('Шаблон имени (* и ?): ').strip()

            if pattern:
                results = find_files_windows(pattern, current_path)
                format_windows_search_results(results, 'по названию')
            else:
                print('Введите шаблон.')

        case '2':
            value = input('Расширения через запятую: ')
            extensions = [item.strip() for item in value.split(',') if item.strip()]
            results = find_by_windows_extension(extensions, current_path)
            format_windows_search_results(results, 'по расширению')

        case '3':
            try:
                minimum = float(input('Минимальный размер в МБ: '))

                if minimum < 0:
                    raise ValueError

                results = find_large_files_windows(minimum, current_path)
                format_windows_search_results(results, 'по размеру')
            except ValueError:
                print('Введите неотрицательное число.')

        case '4':
            results = find_windows_system_files(current_path)
            format_windows_search_results(results, 'системные файлы')

        case '5':
            analysis.show_windows_directory_stats(current_path)

        case '0':
            return False

        case _:
            print('Неизвестная команда.')

    return True
