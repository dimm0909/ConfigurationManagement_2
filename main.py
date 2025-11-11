import argparse
import sys
import requests
import json
import re
import os
from collections import deque
import webbrowser
import tempfile


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
    parser.add_argument('--output', type=str, default="dependency_graph.html",
                        help='Имя файла для сохранения визуализации графа (по умолчанию: dependency_graph.html)')

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


def generate_mermaid_graph(graph, root_package):
    mermaid_code = "graph TD;\n"

    mermaid_code += f"    {root_package}((\"{root_package}\")):::root;\n"

    mermaid_code += "    classDef root fill:#f96,stroke:#333,stroke-width:2px;\n"
    mermaid_code += "    classDef dependency fill:#9cf,stroke:#333;\n"
    mermaid_code += "    classDef cyclic fill:#f96,stroke:#333,stroke-dasharray: 5 5;\n"

    added_edges = set()
    cyclic_deps = detect_cycles(graph)

    for package, dependencies in graph.items():
        if not dependencies:
            mermaid_code += f"    {package}[\"{package}\"]:::dependency;\n"

        for dep in dependencies:
            edge = f"{package}-->{dep}"
            if edge not in added_edges:
                # Проверка на циклическую зависимость
                is_cyclic = (package in cyclic_deps and dep in cyclic_deps[package]) or \
                            (dep in cyclic_deps and package in cyclic_deps[dep])

                if is_cyclic:
                    mermaid_code += f"    {package} -.-> {dep}:::cyclic;\n"
                else:
                    mermaid_code += f"    {package} --> {dep};\n"
                added_edges.add(edge)

    return mermaid_code


def detect_cycles(graph):
    cyclic_deps = {}

    def dfs(package, visited, stack):
        visited.add(package)
        stack.add(package)

        for dep in graph.get(package, []):
            if dep not in visited:
                if dfs(dep, visited, stack):
                    cyclic_deps.setdefault(package, []).append(dep)
                    return True
            elif dep in stack:
                cyclic_deps.setdefault(package, []).append(dep)
                return True

        stack.remove(package)
        return False

    visited = set()
    stack = set()

    for package in graph:
        if package not in visited:
            dfs(package, visited, stack)

    return cyclic_deps


def print_ascii_tree(graph, root, depth=0, prefix="", visited=None):
    if visited is None:
        visited = set()

    if root in visited:
        print(f"{prefix}└── {root} (цикл)")
        return

    visited.add(root)

    if depth == 0:
        print(f"{root}")
    else:
        print(f"{prefix}└── {root}")

    if root in graph and depth < 3:
        deps = graph[root]
        for i, dep in enumerate(deps):
            new_prefix = prefix + ("    " if i == len(deps) - 1 else "|   ")
            print_ascii_tree(graph, dep.lower(), depth + 1, new_prefix, visited.copy())


def create_html_visualization(mermaid_code, output_file):
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Граф зависимостей</title>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .mermaid {{
                text-align: center;
                margin: 20px auto;
                max-width: 100%;
            }}
            pre {{
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
                margin: 20px 0;
            }}
            h1 {{
                color: #333;
                text-align: center;
            }}
            .notes {{
                margin: 20px 0;
                padding: 15px;
                background-color: #e7f3ff;
                border-left: 4px solid #2196F3;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Граф зависимостей Python-пакетов</h1>
            <div class="mermaid">
                {mermaid_code}
            </div>
            <div class="notes">
                <h3>Примечания:</h3>
                <ul>
                    <li>Круглый оранжевый узел - анализируемый пакет</li>
                    <li>Голубые узлы - зависимости</li>
                    <li>Пунктирные линии - циклические зависимости</li>
                </ul>
            </div>
            <h3>Код для Mermaid:</h3>
            <pre>{mermaid_code}</pre>
        </div>
        <script>
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'default',
                securityLevel: 'loose'
            }});
        </script>
    </body>
    </html>
    """

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_template)
        print(f"HTML файл с визуализацией успешно создан: {output_file}")
        return True
    except Exception as e:
        print(f"Ошибка при создании HTML файла: {e}")
        return False


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
    print(f"output_file = {args.output}")

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

    root_package = args.package.lower()
    mermaid_code = generate_mermaid_graph(dependency_graph, root_package)
    print("\nКод графа в формате Mermaid:")
    print(mermaid_code)

    if create_html_visualization(mermaid_code, args.output):
        try:
            webbrowser.open(f'file://{os.path.abspath(args.output)}')
        except:
            pass

    if args.ascii:
        print("\nЗависимости в формате ASCII-дерева:")
        print_ascii_tree(dependency_graph, root_package)

    if args.test:
        print("\nДемонстрация визуализации для трех различных пакетов в тестовом режиме:")
        test_packages = ['A', 'B', 'C']
        for pkg in test_packages:
            print(f"\nПакет {pkg}:")
            test_graph = build_dependency_graph(
                pkg,
                'latest',
                args.max_depth,
                args.test,
                args.repo
            )
            test_mermaid = generate_mermaid_graph(test_graph, pkg.lower())
            print(f"Mermaid код для пакета {pkg}:")
            print(test_mermaid)


if __name__ == "__main__":
    main()