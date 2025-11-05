import argparse
import sys
import requests
import json
import re
from packaging.version import parse as parse_version


def parse_arguments():
    parser = argparse.ArgumentParser(description='Инструмент визуализации графа зависимостей Python-пакетов')

    parser.add_argument('--package', type=str, required=True,
                        help='Имя анализируемого пакета')
    parser.add_argument('--repo', type=str, required=True,
                        help='URL-адрес репозитория или путь к файлу тестового репозитория')
    parser.add_argument('--test', action='store_true',
                        help='Режим работы с тестовым репозиторием')
    parser.add_argument('--version', type=str, default='latest',
                        help='Версия пакета (по умолчанию: latest)')
    parser.add_argument('--ascii', action='store_true',
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
    if not args.repo:
        errors.append("URL репозитория не может быть пустым")
    if args.max_depth < 1:
        errors.append("Максимальная глубина должна быть положительным числом")

    if errors:
        for error in errors:
            print(f"Ошибка валидации: {error}")
        sys.exit(1)


def get_package_info(package_name, version, repository_url):
    if version == 'latest':
        url = f"{repository_url.rstrip('/')}/json"
    else:
        url = f"{repository_url.rstrip('/')}/{version}/json"

    url += "?callback=?"
    print(url)
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных о пакете: {e}")
        sys.exit(1)


def extract_dependencies(metadata):
    dependencies = []

    requires_dist = metadata.get('info', {}).get('requires_dist', [])
    if requires_dist:
        for dep in requires_dist:
            match = re.match(r'^([a-zA-Z0-9\-_\.]+)', dep)
            if match:
                dependencies.append(match.group(1).lower())

    requires = metadata.get('info', {}).get('requires', [])
    if requires:
        dependencies.extend([req.lower() for req in requires])

    return list(set(dependencies))


def main():
    args = parse_arguments()
    validate_arguments(args)

    print("Параметры приложения:")
    print(f"package = {args.package}")
    print(f"repository = {args.repo}")
    print(f"test_mode = {args.test}")
    print(f"version = {args.version}")
    print(f"ascii_tree = {args.ascii}")
    print(f"max_depth = {args.max_depth}")

    if not args.test:
        print(f"\nПолучение информации о пакете {args.package} версии {args.version}...")
        package_data = get_package_info(args.package, args.version, args.repo)
        dependencies = extract_dependencies(package_data)

        print(f"\nПрямые зависимости пакета {args.package}:")
        for dep in dependencies:
            print(f"- {dep}")
    else:
        print("\nРежим тестирования. Прямые зависимости не извлекаются.")


if __name__ == "__main__":
    main()
