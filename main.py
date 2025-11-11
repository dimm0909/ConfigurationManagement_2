import argparse
import sys
import requests
import json
import re
import os
from collections import deque


def parse_arguments():
    parser = argparse.ArgumentParser(description='Инструмент визуализации графа зависимостей Python-пакетов')

    parser.add_argument('--package', type=str, required=True,
                        help='Имя анализируемого пакета')
    parser.add_argument('--repo', type=str, required=True,
                        help='URL-адрес репозитория или путь к файлу тестового репозитория')
    parser.add_argument('--test', type=str, default="False",
                        help='Режим работы с тестовым репозиторием (True/False)')
    parser.add_argument('--version', type=str, default="latest",
                        help='Версия пакета (по умолчанию: latest)')
    parser.add_argument('--ascii', type=str, default="False",
                        help='Режим вывода зависимостей в формате ASCII-дерева (True/False)')
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

    args.test = args.test.lower() == 'true'
    args.ascii = args.ascii.lower() == 'true'
    return args


def get_package_info(package_name, version='latest', repository_url='https://pypi.org/pypi'):
    if version == 'latest':
        url = f"{repository_url}/{package_name}/json"
    else:
        url = f"{repository_url}/{package_name}/{version}/json"

    try:
        print(f"Запрос информации о пакете {package_name} версии {version} из {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных о пакете {package_name}: {e}")
        return None


def extract_dependencies(metadata):
    if not metadata:
        return []

    dependencies = []
    info = metadata.get('info', {})

    requires_dist = info.get('requires_dist', [])
    if requires_dist:
        for dep in requires_dist:
            match = re.match(r'^([a-zA-Z0-9\-_\.]+)', dep)
            if match:
                dep_name = match.group(1).lower()
                package_name = info.get('name', '').lower()
                if dep_name != package_name and not dep_name.startswith('_'):
                    dependencies.append(dep_name)

    requires = info.get('requires', [])
    if requires:
        for req in requires:
            req_name = re.split('[<>=;]', req)[0].strip().lower()
            if req_name:
                dependencies.append(req_name)

    return list(set(dependencies))


def get_test_dependencies(package_name, test_file_path):
    try:
        if not os.path.exists(test_file_path):
            print(f"Тестовый файл {test_file_path} не найден.")
            return []

        with open(test_file_path, 'r') as f:
            test_data = json.load(f)

        # Поиск пакета с учетом регистра
        package_key = package_name.upper()
        if package_key in test_data:
            return test_data[package_key]

        return []
    except json.JSONDecodeError as e:
        print(f"Ошибка при разборе JSON в тестовом файле: {e}")
        return []
    except Exception as e:
        print(f"Ошибка при чтении тестового файла: {e}")
        return []


def build_dependency_graph(package_name, version='latest', max_depth=3, test_mode=False, repo_url=None):
    graph = {}
    visited = set()
    stack = [(package_name.lower(), version, 0)]  # (package_name, version, depth)

    while stack:
        current_pkg, current_ver, depth = stack.pop()

        if depth > max_depth:
            continue

        if current_pkg in visited:
            continue

        visited.add(current_pkg)

        if test_mode:
            dependencies = get_test_dependencies(current_pkg, repo_url)
        else:
            package_data = get_package_info(current_pkg, current_ver, repo_url)
            dependencies = extract_dependencies(package_data) if package_data else []

        graph[current_pkg] = dependencies

        for dep in dependencies:
            dep_clean = dep.lower()
            if dep_clean not in visited:
                stack.append((dep_clean, 'latest', depth + 1))

    return graph


def main():
    args = parse_arguments()
    args = validate_arguments(args)

    print("Параметры приложения:")
    print(f"package = {args.package}")
    print(f"repository = {args.repo}")
    print(f"test_mode = {args.test}")
    print(f"version = {args.version}")
    print(f"ascii_tree = {args.ascii}")
    print(f"max_depth = {args.max_depth}")

    print(f"\nПостроение графа зависимостей для пакета {args.package}...")

    repository_url = args.repo
    if not args.test and not repository_url.startswith(('http://', 'https://')):
        repository_url = f"https://{repository_url}"

    dependency_graph = build_dependency_graph(
        args.package,
        args.version,
        args.max_depth,
        args.test,
        repository_url
    )

    print("\nГраф зависимостей:")
    for package, deps in dependency_graph.items():
        print(f"{package}: {', '.join(deps) if deps else 'нет зависимостей'}")

    print("\nПроверка на циклические зависимости...")
    visited = set()
    stack = set()
    cyclic_deps = []

    def has_cycle(package):
        if package in stack:
            cyclic_deps.append(package)
            return True
        if package in visited:
            return False

        visited.add(package)
        stack.add(package)

        for dep in dependency_graph.get(package, []):
            if has_cycle(dep):
                return True

        stack.remove(package)
        return False

    for package in dependency_graph:
        if has_cycle(package):
            print(f"Обнаружены циклические зависимости, включающие пакет: {package}")

    if not cyclic_deps:
        print("Циклические зависимости не обнаружены.")

    if args.test:
        print("\nДемонстрация работы с тестовым репозиторием:")
        print("Тестовый режим позволяет анализировать предопределенные графы зависимостей")
        print("где пакеты обозначены большими латинскими буквами (A, B, C и т.д.)")
        print("Это позволяет протестировать алгоритмы обработки циклических зависимостей")
        print("и проверить корректность работы при различных конфигурациях графа.")


if __name__ == "__main__":
    main()