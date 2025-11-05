import argparse
import sys


def parse_arguments():
    parser = argparse.ArgumentParser(description='Инструмент визуализации графа зависимостей Python-пакетов')

    parser.add_argument('--package', type=str, required=True,
                        help='Имя анализируемого пакета')
    parser.add_argument('--repository', type=str, required=True,
                        help='URL-адрес репозитория или путь к файлу тестового репозитория')
    parser.add_argument('--test-mode', action='store_true',
                        help='Режим работы с тестовым репозиторием')
    parser.add_argument('--version', type=str, default='latest',
                        help='Версия пакета (по умолчанию: latest)')
    parser.add_argument('--ascii-tree', action='store_true',
                        help='Режим вывода зависимостей в формате ASCII-дерева')
    parser.add_argument('--max-depth', type=int, default=3,
                        help='Максимальная глубина анализа зависимостей (по умолчанию: 3)')

    try:
        args = parser.parse_args()
        return args
    except SystemExit:
        print("Ошибка: неверные аргументы командной строки")
        sys.exit(1)


def validate_arguments(args):
    errors = []

    if not args.package:
        errors.append("Имя пакета не может быть пустым")
    if not args.repository:
        errors.append("URL репозитория не может быть пустым")
    if args.max_depth < 1:
        errors.append("Максимальная глубина должна быть положительным числом")

    if errors:
        for error in errors:
            print(f"Ошибка валидации: {error}")
        sys.exit(1)


def main():
    args = parse_arguments()
    validate_arguments(args)

    # Вывод параметров в формате ключ-значение
    print("Параметры приложения:")
    print(f"package = {args.package}")
    print(f"repository = {args.repository}")
    print(f"test_mode = {args.test_mode}")
    print(f"version = {args.version}")
    print(f"ascii_tree = {args.ascii_tree}")
    print(f"max_depth = {args.max_depth}")


if __name__ == "__main__":
    main()