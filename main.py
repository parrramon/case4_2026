import os, platform
from typing import NoReturn
import analysis, navigation, search, utils

def check_windows_environment() -> bool:
    """Check that the program is running on Windows."""

    # Используем проверку системы из модуля утилит.
    if utils.is_windows_os():
        return True

    print('Программа работает только на Windows.')
    return False

def display_windows_banner() -> None:
    """Display the program title and Windows information."""

    # Показываем название программы, систему и текущий диск.
    print('=' * 50)
    print('ФАЙЛОВЫЙ АРХЕОЛОГ')
    print('=' * 50)
    print(f'Система: {platform.platform()}')
    print(f'Текущий диск: {navigation.get_current_drive()}')

def display_main_menu(current_path: str) -> None:
    """Display the main menu and available Windows drives."""

    # Получаем список дисков через модуль навигации.
    drives = navigation.list_available_drives()

    print('\nГЛАВНОЕ МЕНЮ')
    print(f'Текущая папка: {current_path}')
    drive_text = ', '.join(drives)
    print(f'Доступные диски: {drive_text}')
    print('1. Просмотр папки и переход')
    print('2. Полная статистика папки')
    print('3. Поиск файлов')
    print('4. Количество файлов и размер папки')
    print('5. Сменить диск')
    print('6. Перейти в специальную папку')
    print('0. Выход')

def handle_windows_navigation(command: str, current_path: str) -> str:
    """Handle navigation between Windows folders and drives."""

    match command:
        case '1':
            # Показываем содержимое текущей папки.
            success, items = navigation.list_directory(current_path)

            if not success:
                print('Не удалось открыть папку.')
                return current_path

            navigation.format_directory_output(items, current_path)
            name = input('Имя папки (Enter или .. — вверх): ').strip()

            if not name or name == '..':
                return navigation.move_up(current_path)

            success, new_path = navigation.move_down(current_path, name)

            if success:
                return new_path

            print('Не удалось перейти в папку.')

        case '5':
            # Проверяем, существует ли выбранный диск.
            drives = navigation.list_available_drives()
            drive = input('Введите диск (например, C:): ').strip().upper().rstrip('\\')

            if drive in drives:
                return drive + '\\'

            print('Такой диск недоступен.')

        case '6':
            # Выводим специальные папки пользователя.
            folders = navigation.get_windows_special_folders()

            for name, folder in folders.items():
                print(f'{name}: {folder}')

            selected = input('Название папки: ').strip()

            for name, folder in folders.items():
                if name.lower() == selected.lower():
                    success, message = utils.validate_windows_path(folder)

                    if success and os.path.isdir(folder):
                        return folder

                    print(message or 'Папка недоступна.')
                    return current_path

            print('Специальная папка не найдена.')

    return current_path

def handle_windows_analysis(command: str, current_path: str) -> None:
    """Run the selected Windows directory analysis."""

    if command == '2':
        # Подробную статистику считает модуль аналитика.
        analysis.show_windows_directory_stats(current_path)
        return

    if command == '4':
        # Считаем число файлов и общий размер папки.
        success, count = analysis.count_files(current_path)

        if success:
            print(f'Количество файлов: {count}')
        else:
            print('Не удалось посчитать файлы.')

        success, size = analysis.count_bytes(current_path)

        if success:
            print(f'Общий размер: {utils.format_size(size)}')
        else:
            print('Не удалось посчитать размер.')

def handle_windows_search(command: str, current_path: str) -> None:
    """Open and manage the Windows file search menu."""

    if command == '3':
        # Показываем меню снова, пока пользователь не выберет 0.
        while search.search_menu_handler(current_path):
            pass

def run_windows_command(command: str, current_path: str) -> str:
    """Choose a project module based on the main menu command."""

    # Команды распределяются между модулями проекта.
    match command:
        case '1' | '5' | '6':
            return handle_windows_navigation(command, current_path)

        case '2' | '4':
            handle_windows_analysis(command, current_path)

        case '3':
            handle_windows_search(command, current_path)

        case '0':
            print('Завершение работы.')
            raise SystemExit(0)

        case _:
            print('Неизвестная команда.')

    return current_path

def main() -> NoReturn:
    """Start the file archaeologist program on Windows."""

    # На другой операционной системе программа не запускается.
    if not check_windows_environment():
        raise SystemExit(1)

    display_windows_banner()
    current_path = os.getcwd()

    # Бесконечный цикл завершается только при выходе из программы.
    while True:
        try:
            display_main_menu(current_path)
            command = input('Команда: ').strip()
            current_path = run_windows_command(command, current_path)

        except (KeyboardInterrupt, EOFError):
            print('\nРабота завершена пользователем.')
            raise SystemExit(0)

        except (OSError, RecursionError) as error:
            # Ошибка доступа или слишком глубокой рекурсии не закрывает меню.
            print(f'Ошибка: {error}')

if __name__ == '__main__':
    main()
