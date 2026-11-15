import os
import platform
import sys
from typing import NoReturn
import utils
import navigation
import analysis
import search

def check_windows_environment() -> bool:
    """Check whether the program is running on Windows."""

    if utils.is_windows_os():
        return True

    print('Ошибка: программа предназначена только для Windows.')
    return False

def display_windows_banner() -> None:
    """Display the application title and Windows information."""

    print('=' * 50)
    print('ФАЙЛОВЫЙ АРХЕОЛОГ')
    print('=' * 50)
    print(f"Система: {platform.platform()}")
    print(f"Текущий диск: {navigation.get_current_drive()}")

def display_main_menu(current_path: str) -> None:
    """Display the main menu and available Windows drives."""

    drives = navigation.list_available_drives()

    print('\nГЛАВНОЕ МЕНЮ')
    print(f"Текущий путь: {current_path}")
    print(f"Диски: {', '.join(drives)}")
    print('1. Открыть папку / перейти вверх')
    print('2. Статистика текущей папки')
    print('3. Поиск файлов')
    print('4. Количество файлов и общий размер')
    print('5. Сменить диск')
    print('6. Перейти в специальную папку')
    print('0. Выход')

def handle_windows_navigation(command: str,
                              current_path: str) -> str:
    """Handle Windows directory and drive navigation."""

    match command:
        case '1':
            # '..' означает переход в родительскую папку.
            success, items = navigation.list_directory(current_path)
            if success:
                navigation.format_directory_output(items, current_path)
            else:
                print('Не удалось прочитать папку.')

            name = input("Имя папки или '..' (Enter — назад): ").strip()
            if name == '..':
                return navigation.move_up(current_path)
            if not name:
                return current_path

            success, new_path = navigation.move_down(current_path, name)
            if success:
                return new_path

            print('Не удалось открыть папку.')

        case '5':
            drives = navigation.list_available_drives()
            drive = input('Введите диск (например, C:): ').strip()
            drive = drive.upper().rstrip('\\')
            if drive in [item.upper().rstrip('\\') for item in drives]:
                return drive + '\\'
            print('Такой диск недоступен.')

        case '6':
            folders = navigation.get_windows_special_folders()
            for name, folder in folders.items():
                print(f"{name}: {folder}")

            name = input('Название папки: ').strip()
            folder = next((value for key, value in folders.items()
                           if key.lower() == name.lower()), None)

            if folder:
                valid, message = utils.validate_windows_path(folder)
                if valid and os.path.isdir(folder):
                    return folder
                print(message or 'Папка недоступна.')
            else:
                print('Такой специальной папки нет.')

    return current_path

def handle_windows_analysis(command: str,
                            current_path: str) -> None:
    """Run the selected Windows directory analysis."""

    match command:
        case '2':
            # Полная статистика из модуля аналитика.
            analysis.show_windows_directory_stats(current_path)
        case '4':
            # Считаем файлы и их суммарный размер отдельно.
            files_ok, count = analysis.count_files(current_path)
            bytes_ok, size = analysis.count_bytes(current_path)

            if files_ok:
                print(f"Файлов: {count}")
            else:
                print('Не удалось посчитать файлы.')

            if bytes_ok:
                print(f"Размер: {utils.format_size(size)}")
            else:
                print('Не удалось посчитать размер.')

def handle_windows_search(command: str,
                          current_path: str) -> None:
    """Open the Windows file search menu."""

    if command == '3':
        search.search_menu_handler(current_path)

def run_windows_command(command: str, current_path: str) -> str:
    """Route the menu command to the correct project module."""

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
    """Start the Windows file archaeologist application."""

    if not check_windows_environment():
        raise SystemExit(1)

    display_windows_banner()
    current_path = os.getcwd()

    # Главный цикл работает до выбора команды выхода.
    while True:
        try:
            display_main_menu(current_path)
            command = input('Команда: ').strip()
            current_path = run_windows_command(command, current_path)
        except (KeyboardInterrupt, EOFError):
            print('\nРабота завершена пользователем.')
            raise SystemExit(0)
        except (OSError, PermissionError) as error:
            # Ошибка доступа не должна закрывать всю программу.
            print(f"Ошибка Windows: {error}")

if __name__ == '__main__':
    main()
