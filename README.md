# ConfigurationManagement_2
* В данной работе реализуется трекинг зависимостей пакета, используя ресурс pypi.org. По умолчанию страница с визуализацией графа формата Mermaid лежит в папке проекта и называется dependency_graph.html.

# Параметры
* --package - имя анализируемого Python-пакета
* --repo - URL-адрес репозитория PyPI или путь к файлу тестового репозитория
* --test - режим работы с тестовым репозиторием (True/False)
* --version - версия пакета для анализа (по умолчанию: latest)
* --ascii - режим вывода зависимостей в формате ASCII-дерева (True/False)
* --max-depth - максимальная глубина анализа зависимостей (по умолчанию: 3)
* --output - имя файла для сохранения графа в формате Mermaid (по умолчанию: dependency_graph.mmd)

# Запуск программы с минимальными параметрами
python dependency_visualizer.py --package requests --repo https://pypi.org --test False

# Запуск в тестовом режиме с использованием файла test_repo.json
python dependency_visualizer.py --package A --repo test_repo.json --test True

# Полный пример запуска с настройками
python dependency_visualizer.py --package pandas --repo https://pypi.org --test False --version 2.0.0 --ascii True --max-depth 4 --output pandas_dependencies.mmd

# Пример вывода для пакета Requests

Построение графа зависимостей для пакета requests...
Запрос информации о пакете requests версии latest из https://pypi.python.org/pypi/requests/json
Запрос информации о пакете urllib3 версии latest из https://pypi.python.org/pypi/urllib3/json
Запрос информации о пакете pysocks версии latest из https://pypi.python.org/pypi/pysocks/json
Запрос информации о пакете zstandard версии latest из https://pypi.python.org/pypi/zstandard/json
Запрос информации о пакете h2 версии latest из https://pypi.python.org/pypi/h2/json
Запрос информации о пакете brotli версии latest из https://pypi.python.org/pypi/brotli/json
Запрос информации о пакете brotlicffi версии latest из https://pypi.python.org/pypi/brotlicffi/json
Запрос информации о пакете idna версии latest из https://pypi.python.org/pypi/idna/json
Запрос информации о пакете mypy версии latest из https://pypi.python.org/pypi/mypy/json
Запрос информации о пакете ruff версии latest из https://pypi.python.org/pypi/ruff/json
Запрос информации о пакете flake8 версии latest из https://pypi.python.org/pypi/flake8/json
Запрос информации о пакете pytest версии latest из https://pypi.python.org/pypi/pytest/json
Запрос информации о пакете chardet версии latest из https://pypi.python.org/pypi/chardet/json
Запрос информации о пакете charset_normalizer версии latest из https://pypi.python.org/pypi/charset_normalizer/json
Запрос информации о пакете certifi версии latest из https://pypi.python.org/pypi/certifi/json

Граф зависимостей:
requests: certifi, charset_normalizer, chardet, idna, pysocks, urllib3
urllib3: brotlicffi, brotli, h2, zstandard, pysocks
pysocks: нет зависимостей
zstandard: cffi
h2: hpack, hyperframe
brotli: нет зависимостей
brotlicffi: cffi
idna: pytest, flake8, ruff, mypy
mypy: pip, tomli, typing_extensions, lxml, psutil, mypy_extensions, setuptools, pathspec, orjson
ruff: нет зависимостей
flake8: mccabe, pyflakes, pycodestyle
pytest: pygments, tomli, iniconfig, exceptiongroup, argcomplete, attrs, hypothesis, xmlschema, colorama, pluggy, mock, packaging, requests, setuptools
chardet: нет зависимостей
charset_normalizer: нет зависимостей
certifi: нет зависимостей

Порядок загрузки зависимостей:
1. brotlicffi
2. tomli
3. pycodestyle
4. lxml
5. h2
6. mypy_extensions
7. pluggy
8. setuptools
9. pytest
10. mypy
11. flake8
12. chardet
13. idna
14. colorama
15. mock
16. ruff
17. orjson
18. urllib3
19. cffi
20. certifi
21. charset_normalizer
22. mccabe
23. argcomplete
24. hypothesis
25. brotli
26. attrs
27. packaging
28. hpack
29. zstandard
30. pathspec
31. hyperframe
32. pip
33. pygments
34. pyflakes
35. iniconfig
36. exceptiongroup
37. typing_extensions
38. xmlschema
39. psutil
40. pysocks
41. requests

Код графа в формате Mermaid:
graph TD;
    requests(("requests")):::root;
    classDef root fill:#f96,stroke:#333,stroke-width:2px;
    classDef dependency fill:#9cf,stroke:#333;
    classDef cyclic fill:#f96,stroke:#333,stroke-dasharray: 5 5;
    requests --> certifi;
    requests --> charset_normalizer;
    requests --> chardet;
    requests -.-> idna:::cyclic;
    requests --> pysocks;
    requests --> urllib3;
    urllib3 --> brotlicffi;
    urllib3 --> brotli;
    urllib3 --> h2;
    urllib3 --> zstandard;
    urllib3 --> pysocks;
    pysocks["pysocks"]:::dependency;
    zstandard --> cffi;
    h2 --> hpack;
    h2 --> hyperframe;
    brotli["brotli"]:::dependency;
    brotlicffi --> cffi;
    idna -.-> pytest:::cyclic;
    idna --> flake8;
    idna --> ruff;
    idna --> mypy;
    mypy --> pip;
    mypy --> tomli;
    mypy --> typing_extensions;
    mypy --> lxml;
    mypy --> psutil;
    mypy --> mypy_extensions;
    mypy --> setuptools;
    mypy --> pathspec;
    mypy --> orjson;
    ruff["ruff"]:::dependency;
    flake8 --> mccabe;
    flake8 --> pyflakes;
    flake8 --> pycodestyle;
    pytest --> pygments;
    pytest --> tomli;
    pytest --> iniconfig;
    pytest --> exceptiongroup;
    pytest --> argcomplete;
    pytest --> attrs;
    pytest --> hypothesis;
    pytest --> xmlschema;
    pytest --> colorama;
    pytest --> pluggy;
    pytest --> mock;
    pytest --> packaging;
    pytest -.-> requests:::cyclic;
    pytest --> setuptools;
    chardet["chardet"]:::dependency;
    charset_normalizer["charset_normalizer"]:::dependency;
    certifi["certifi"]:::dependency;

HTML файл с визуализацией успешно создан: dependency_graph.html

Зависимости в формате ASCII-дерева:
requests
|   └── certifi
|   └── charset_normalizer
|   └── chardet
|   └── idna
|   |   └── pytest
|   |   |   └── pygments
|   |   |   └── tomli
|   |   |   └── iniconfig
|   |   |   └── exceptiongroup
|   |   |   └── argcomplete
|   |   |   └── attrs
|   |   |   └── hypothesis
|   |   |   └── xmlschema
|   |   |   └── colorama
|   |   |   └── pluggy
|   |   |   └── mock
|   |   |   └── packaging
|   |   |   └── requests (цикл)
|   |       └── setuptools
|   |   └── flake8
|   |   |   └── mccabe
|   |   |   └── pyflakes
|   |       └── pycodestyle
|   |   └── ruff
|       └── mypy
|       |   └── pip
|       |   └── tomli
|       |   └── typing_extensions
|       |   └── lxml
|       |   └── psutil
|       |   └── mypy_extensions
|       |   └── setuptools
|       |   └── pathspec
|           └── orjson
|   └── pysocks
    └── urllib3
    |   └── brotlicffi
    |       └── cffi
    |   └── brotli
    |   └── h2
    |   |   └── hpack
    |       └── hyperframe
    |   └── zstandard
    |       └── cffi
        └── pysocks
