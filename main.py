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
    stack = [(package_name.lower(), version, 0)]

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


def get_load_order(graph, start_package):

    all_nodes = set()
    for node, deps in graph.items():
        all_nodes.add(node)
        all_nodes.update(deps)

    in_degree = {node: 0 for node in all_nodes}

    for node in graph:
        for neighbor in graph[node]:
            if neighbor in in_degree:
                in_degree[neighbor] += 1

    queue = deque([node for node, degree in in_degree.items() if degree == 0])
    load_order = []

    in_degree_copy = in_degree.copy()

    while queue:
        node = queue.popleft()
        load_order.append(node)

        if node in graph:
            for neighbor in graph[node]:
                if neighbor in in_degree_copy:
                    in_degree_copy[neighbor] -= 1
                    if in_degree_copy[neighbor] == 0:
                        queue.append(neighbor)

    if len(load_order) != len(all_nodes):
        remaining_nodes = [node for node in all_nodes if node not in load_order]
        load_order.extend(remaining_nodes)

    if start_package in load_order:
        load_order.remove(start_package)
    load_order.append(start_package)

    return load_order


def reverse_dependencies(graph):
    reverse_graph = {}

    for package in graph:
        reverse_graph.setdefault(package, [])
        for dep in graph[package]:
            reverse_graph.setdefault(dep, []).append(package)

    return reverse_graph


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

    print("\nПорядок загрузки зависимостей:")
    load_order = get_load_order(dependency_graph, args.package.lower())
    for i, pkg in enumerate(load_order, 1):
        print(f"{i}. {pkg}")

    if args.test:
        print("\nДемонстрация работы с тестовым репозиторием:")
        print("В тестовом режиме можно проверить корректность определения порядка загрузки")
        print("для известных конфигураций графа зависимостей, включая циклические зависимости.")

        test_graph = {
            'A': ['B', 'C'],
            'B': ['D'],
            'C': ['D', 'E'],
            'D': ['B'],
            'E': ['F'],
            'F': []
        }
        print("\nПример тестового графа с циклической зависимостью:")
        for package, deps in test_graph.items():
            print(f"{package}: {', '.join(deps)}")

        test_load_order = get_load_order(test_graph, 'A')
        print("\nПорядок загрузки для тестового графа:")
        for i, pkg in enumerate(test_load_order, 1):
            print(f"{i}. {pkg}")


if __name__ == "__main__":
    main()