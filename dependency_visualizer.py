#!/usr/bin/env python3
"""
Инструмент визуализации графа зависимостей пакетов
Этап 5: Визуализация графа зависимостей (исправленная версия)
"""

import argparse
import sys
import os
import json
import urllib.request
import urllib.error
from collections import deque
import subprocess
import tempfile


class DependencyVisualizer:
    def __init__(self):
        self.dependency_graph = {}

    def parse_arguments(self):
        """Парсинг аргументов командной строки"""
        parser = argparse.ArgumentParser(
            description='Инструмент визуализации графа зависимостей пакетов'
        )

        parser.add_argument(
            '--package',
            type=str,
            required=True,
            help='Имя анализируемого пакета'
        )

        parser.add_argument(
            '--repo',
            type=str,
            required=True,
            help='URL-адрес репозитория или путь к файлу тестового репозитория'
        )

        parser.add_argument(
            '--test-mode',
            action='store_true',
            help='Режим работы с тестового репозитория'
        )

        parser.add_argument(
            '--output',
            type=str,
            default='dependency_graph.svg',
            help='Имя сгенерированного файла с изображением графа'
        )

        parser.add_argument(
            '--filter',
            type=str,
            default='',
            help='Подстрока для фильтрации пакетов'
        )

        parser.add_argument(
            '--reverse',
            action='store_true',
            help='Режим вывода обратных зависимостей'
        )

        return parser.parse_args()

    def validate_arguments(self, args):
        """Валидация аргументов командной строки"""
        errors = []

        # Проверка имени пакета
        if not args.package or not args.package.strip():
            errors.append("Имя пакета не может быть пустым")

        # Проверка репозитория
        if not args.repo or not args.repo.strip():
            errors.append("Репозиторий не может быть пустым")
        elif args.test_mode:
            # В тестовом режиме проверяем существование файла
            if not os.path.exists(args.repo):
                errors.append(f"Файл репозитория не существует: {args.repo}")
            elif not os.path.isfile(args.repo):
                errors.append(f"Указанный путь не является файлом: {args.repo}")

        # Проверка выходного файла
        if not args.output or not args.output.strip():
            errors.append("Имя выходного файла не может быть пустым")
        else:
            valid_extensions = ['.svg', '.png', '.jpg', '.jpeg']
            if not any(args.output.lower().endswith(ext) for ext in valid_extensions):
                errors.append(f"Неподдерживаемый формат файла. Допустимые: {', '.join(valid_extensions)}")

        return errors

    def fetch_package_info_from_npm(self, package_name):
        """Получение информации о пакете из npm реестра"""
        url = f"https://registry.npmjs.org/{package_name}"

        try:
            # Добавляем User-Agent для избежания блокировки
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'application/json'
                }
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise Exception(f"Пакет '{package_name}' не найден в npm реестру")
            else:
                raise Exception(f"Ошибка HTTP {e.code} при запросе к npm реестру: {e}")
        except urllib.error.URLError as e:
            raise Exception(f"Ошибка сети: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Ошибка парсинга JSON ответа: {e}")
        except Exception as e:
            raise Exception(f"Неожиданная ошибка: {e}")

    def get_dependencies_from_npm(self, package_name):
        """Получение зависимостей пакета из npm реестра"""
        try:
            package_info = self.fetch_package_info_from_npm(package_name)

            # Получаем последнюю версию
            if 'dist-tags' in package_info and 'latest' in package_info['dist-tags']:
                latest_version = package_info['dist-tags']['latest']
            else:
                # Если нет latest, берем последнюю версию из versions
                versions = list(package_info.get('versions', {}).keys())
                if not versions:
                    return {}
                latest_version = sorted(versions)[-1]

            # Получаем зависимости для последней версии
            version_info = package_info['versions'].get(latest_version, {})
            dependencies = version_info.get('dependencies', {})

            return dependencies

        except Exception as e:
            print(f"   ⚠️ Предупреждение: не удалось получить зависимости для '{package_name}': {e}")
            return {}

    def get_dependencies_from_test_file(self, package_name, file_path):
        """Получение зависимостей из тестового файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise Exception(f"Файл '{file_path}' не найден")
        except json.JSONDecodeError as e:
            raise Exception(f"Ошибка парсинга JSON файла: {e}")

        # Ищем информацию о пакете в тестовом файле
        if isinstance(data, dict):
            # Если файл содержит информацию об одном пакете
            if data.get('name') == package_name or 'dependencies' in data:
                return data.get('dependencies', {})
            # Если файл содержит информацию о нескольких пакетах
            elif package_name in data:
                package_data = data[package_name]
                if isinstance(package_data, dict) and 'dependencies' in package_data:
                    return package_data['dependencies']
                elif isinstance(package_data, dict):
                    return package_data
        elif isinstance(data, list):
            # Если файл содержит список пакетов
            for package in data:
                if package.get('name') == package_name:
                    return package.get('dependencies', {})

        return {}

    def get_direct_dependencies(self, package_name, repo_url, test_mode=False):
        """Получение прямых зависимостей пакета"""
        if test_mode:
            return self.get_dependencies_from_test_file(package_name, repo_url)
        else:
            return self.get_dependencies_from_npm(package_name)

    def should_filter_package(self, package_name, filter_substring):
        """Проверка, нужно ли фильтровать пакет"""
        if not filter_substring:
            return False
        return filter_substring.lower() in package_name.lower()

    def build_dependency_graph_dfs(self, start_package, repo_url, test_mode=False, filter_substring=""):
        """Построение графа зависимостей с помощью DFS без рекурсии"""
        # Стек содержит (текущий_пакет, путь_от_корня)
        stack = [(start_package, [])]
        visited = set()
        graph = {}
        cycles = []

        while stack:
            current_package, path = stack.pop()

            # Пропускаем пакеты по фильтру
            if self.should_filter_package(current_package, filter_substring):
                print(f"   🚫 Пакет '{current_package}' отфильтрован")
                graph[current_package] = []
                continue

            # Если пакет уже в графе, пропускаем получение зависимостей
            if current_package not in graph:
                dependencies = self.get_direct_dependencies(current_package, repo_url, test_mode)
                dependency_names = list(dependencies.keys())
                graph[current_package] = dependency_names
                print(f"   📦 {current_package} -> {dependency_names}")

            # Обрабатываем зависимости
            for dep in reversed(graph[current_package]):
                # Проверяем циклическую зависимость
                if dep in path:
                    cycle_start = path.index(dep)
                    cycle = path[cycle_start:] + [current_package, dep]
                    if cycle not in cycles:
                        cycles.append(cycle)
                        print(f"   🔁 Обнаружена циклическая зависимость: {' -> '.join(cycle)}")
                    continue

                # Добавляем в стек для дальнейшего обхода
                if dep not in visited:
                    visited.add(dep)
                    stack.append((dep, path + [current_package]))

        return graph, cycles

    def find_all_paths_to_target(self, start_package, target_package, repo_url, test_mode=False, filter_substring=""):
        """Находит все пути от start_package до target_package"""
        if start_package == target_package:
            return []

        stack = [(start_package, [start_package])]
        paths = []

        while stack:
            current_package, path = stack.pop()

            # Пропускаем пакеты по фильтру
            if self.should_filter_package(current_package, filter_substring):
                continue

            # Получаем зависимости текущего пакета
            dependencies = self.get_direct_dependencies(current_package, repo_url, test_mode)
            dependency_names = list(dependencies.keys())

            for dep in dependency_names:
                # Пропускаем по фильтру
                if self.should_filter_package(dep, filter_substring):
                    continue

                if dep == target_package:
                    # Нашли путь к целевому пакету
                    paths.append(path + [dep])
                elif dep not in path:  # Избегаем циклов
                    stack.append((dep, path + [dep]))

        return paths

    def find_reverse_dependencies(self, target_package, repo_url, test_mode=False, filter_substring=""):
        """Поиск обратных зависимостей с помощью DFS"""
        print(f"🔍 Поиск обратных зависимостей для пакета '{target_package}':")

        # Сначала строим полный граф из всех пакетов в репозитории
        if test_mode:
            # В тестовом режиме получаем все пакеты из файла
            try:
                with open(repo_url, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                print(f"❌ Ошибка загрузки тестового файла: {e}")
                return []

            all_packages = []
            if isinstance(data, dict):
                # Если файл содержит несколько пакетов
                if 'name' in data and 'dependencies' in data:
                    # Один пакет в файле
                    all_packages = [data['name']]
                else:
                    # Несколько пакетов в файле
                    all_packages = list(data.keys())
            elif isinstance(data, list):
                # Список пакетов
                all_packages = [pkg.get('name') for pkg in data if pkg.get('name')]
        else:
            # В реальном режиме ограничимся известными популярными пакетами для демонстрации
            print("   ⚠️ В реальном режиме поиск обратных зависимостей ограничен")
            popular_packages = ["express", "react", "lodash", "axios", "webpack"]
            all_packages = popular_packages

        reverse_deps = []

        # Для каждого пакета проверяем, зависит ли он от target_package
        for package in all_packages:
            if package == target_package:
                continue

            # Пропускаем по фильтру
            if self.should_filter_package(package, filter_substring):
                continue

            # Находим все пути от package до target_package
            paths = self.find_all_paths_to_target(package, target_package, repo_url, test_mode, filter_substring)

            for path in paths:
                if len(path) == 2:
                    # Прямая зависимость
                    reverse_deps.append((package, "прямая"))
                    print(f"   ✅ {package} -> {target_package} (прямая зависимость)")
                else:
                    # Транзитивная зависимость
                    intermediate = path[1]  # Первый промежуточный пакет
                    reverse_deps.append((package, f"транзитивная через {intermediate}"))
                    path_str = " -> ".join(path)
                    print(f"   🔄 {path_str} (транзитивная)")

        return reverse_deps

    def generate_mermaid_diagram(self, graph, start_package):
        """Генерация текстового представления графа на языке Mermaid"""
        mermaid_code = "%% Дерево зависимостей для пакета " + start_package + "\n"
        mermaid_code += "graph TD\n"

        # Добавляем стартовый пакет с особым стилем
        mermaid_code += f"    {start_package.replace('-', '_')}[{start_package}]:::root\n"

        # Добавляем все зависимости
        edges = set()
        nodes = set([start_package.replace('-', '_')])

        for package, dependencies in graph.items():
            package_id = package.replace('-', '_')
            nodes.add(package_id)

            for dep in dependencies:
                if dep in graph:  # Добавляем только если зависимость есть в графе
                    dep_id = dep.replace('-', '_')
                    nodes.add(dep_id)
                    edge = f"    {package_id} --> {dep_id}\n"
                    if edge not in edges:
                        mermaid_code += edge
                        edges.add(edge)

        # Добавляем стили
        mermaid_code += "    \n"
        mermaid_code += "    classDef root fill:#e1f5fe,stroke:#01579b,stroke-width:2px\n"
        mermaid_code += "    classDef leaf fill:#f3e5f5,stroke:#4a148c,stroke-width:1px\n"
        mermaid_code += "    classDef node fill:#e8f5e8,stroke:#1b5e20,stroke-width:1px\n"

        # Применяем стили к листовым узлам (без зависимостей)
        for package, dependencies in graph.items():
            package_id = package.replace('-', '_')
            if not dependencies:
                mermaid_code += f"    class {package_id} leaf\n"
            elif package != start_package:
                mermaid_code += f"    class {package_id} node\n"

        return mermaid_code

    def save_svg_from_mermaid(self, mermaid_code, output_file):
        """Сохранение SVG из Mermaid кода"""
        try:
            # Создаем временный файл с Mermaid кодом
            with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, encoding='utf-8') as f:
                f.write(mermaid_code)
                mermaid_file = f.name

            print(f"📁 Создан временный файл: {mermaid_file}")

            # Пробуем разные способы генерации SVG

            # Способ 1: Docker mermaid-cli
            try:
                print("🚀 Попытка генерации через Docker mermaid-cli...")
                result = subprocess.run([
                    'docker', 'run', '--rm', '-v', f'{os.path.dirname(mermaid_file)}:/data',
                    'minlag/mermaid-cli', '-i', f'/data/{os.path.basename(mermaid_file)}',
                    '-o', f'/data/{os.path.basename(output_file)}',
                    '--backgroundColor', 'white'
                ], capture_output=True, text=True, timeout=60)

                if result.returncode == 0:
                    # Копируем сгенерированный файл из временной директории
                    temp_svg = os.path.join(os.path.dirname(mermaid_file), os.path.basename(output_file))
                    if os.path.exists(temp_svg):
                        import shutil
                        shutil.copy(temp_svg, output_file)
                        print(f"✅ SVG файл успешно создан: {output_file}")
                        os.unlink(mermaid_file)
                        return True
                else:
                    print(f"❌ Ошибка Docker: {result.stderr}")
            except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                print(f"❌ Docker не доступен: {e}")

            # Способ 2: Локальный mermaid-cli
            try:
                print("🚀 Попытка генерации через локальный mermaid-cli...")
                result = subprocess.run([
                    'npx', '-p', '@mermaid-js/mermaid-cli', 'mmdc',
                    '-i', mermaid_file, '-o', output_file,
                    '--backgroundColor', 'white'
                ], capture_output=True, text=True, timeout=60)

                if result.returncode == 0:
                    print(f"✅ SVG файл успешно создан: {output_file}")
                    os.unlink(mermaid_file)
                    return True
                else:
                    print(f"❌ Ошибка mermaid-cli: {result.stderr}")
            except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                print(f"❌ mermaid-cli не доступен: {e}")

            # Способ 3: Сохраняем только Mermaid код
            print("💡 Генерация SVG не удалась, сохраняю Mermaid код...")
            mermaid_output = output_file.replace('.svg', '.mmd')
            with open(mermaid_output, 'w', encoding='utf-8') as f:
                f.write(mermaid_code)
            print(f"✅ Mermaid код сохранен в: {mermaid_output}")
            print("📋 Инструкции для ручной конвертации:")
            print("   1. Установите Docker: https://docs.docker.com/get-docker/")
            print(
                "   2. Запустите: docker run --rm -v $(pwd):/data minlag/mermaid-cli -i /data/input.mmd -o /data/output.svg")
            print("   3. Или установите mermaid-cli: npm install -g @mermaid-js/mermaid-cli")
            print("   4. Запустите: npx mmdc -i input.mmd -o output.svg")

            os.unlink(mermaid_file)
            return False

        except Exception as e:
            print(f"❌ Неожиданная ошибка при создании SVG: {e}")
            # Сохраняем Mermaid код как запасной вариант
            mermaid_output = output_file.replace('.svg', '.mmd')
            with open(mermaid_output, 'w', encoding='utf-8') as f:
                f.write(mermaid_code)
            print(f"✅ Mermaid код сохранен в: {mermaid_output}")
            return False

    def compare_with_npm(self, package_name, our_graph):
        """Сравнение с выводом штатных инструментов npm"""
        print(f"\n🔍 Сравнение с npm для пакета '{package_name}':")

        try:
            # Получаем зависимости через npm (только прямые)
            npm_dependencies = self.get_direct_dependencies(package_name, "https://registry.npmjs.org", False)
            npm_dep_names = set(npm_dependencies.keys())

            # Наши прямые зависимости
            our_direct_deps = set(our_graph.get(package_name, []))

            print("   Прямые зависимости:")
            print(f"   - npm: {len(npm_dep_names)} пакетов")
            print(f"   - Наш инструмент: {len(our_direct_deps)} пакетов")

            # Находим различия
            only_in_npm = npm_dep_names - our_direct_deps
            only_in_our = our_direct_deps - npm_dep_names

            if only_in_npm:
                print(f"   ❌ Только в npm: {list(only_in_npm)}")
            if only_in_our:
                print(f"   ❌ Только в нашем инструменте: {list(only_in_our)}")

            if not only_in_npm and not only_in_our:
                print("   ✅ Прямые зависимости совпадают")

            # Объяснение возможных расхождений
            if only_in_npm or only_in_our:
                print("\n   📝 Возможные причины расхождений:")
                print("   - Разные версии пакетов")
                print("   - npm учитывает peerDependencies и devDependencies")
                print("   - Кэширование данных в npm registry")
                print("   - Временные сетевые проблемы")
                print("   - Разная логика обработки опциональных зависимостей")

        except Exception as e:
            print(f"   ⚠️ Не удалось выполнить сравнение: {e}")

    def print_dependency_graph(self, graph, start_package):
        """Вывод графа зависимостей"""
        if not graph:
            print(f"📭 Граф зависимостей для пакета '{start_package}' пуст")
            return

        print(f"🌳 Полный граф зависимостей для пакета '{start_package}':")
        for package, dependencies in graph.items():
            if dependencies:
                print(f"   {package} -> {dependencies}")
            else:
                print(f"   {package} -> (нет зависимостей)")

    def print_reverse_dependencies(self, target_package, reverse_deps):
        """Вывод обратных зависимостей"""
        if not reverse_deps:
            print(f"📭 Пакет '{target_package}' не имеет обратных зависимостей")
            return

        print(f"🔄 Обратные зависимости пакета '{target_package}':")
        for package, dep_type in reverse_deps:
            print(f"   - {package} ({dep_type})")

    def run(self):
        """Основной метод запуска приложения"""
        try:
            # Парсинг аргументов
            args = self.parse_arguments()

            # Валидация аргументов
            errors = self.validate_arguments(args)
            if errors:
                print("❌ Ошибки валидации:")
                for error in errors:
                    print(f"   - {error}")
                sys.exit(1)

            print(f"🎯 Анализ пакета: {args.package}")
            print(f"🔧 Режим: {'тестовый' if args.test_mode else 'реальный'}")
            if args.filter:
                print(f"🚫 Фильтр: '{args.filter}'")
            if args.reverse:
                print(f"🔄 Режим: обратные зависимости")
            print("=" * 60)

            if args.reverse:
                # Режим обратных зависимостей
                reverse_deps = self.find_reverse_dependencies(
                    args.package,
                    args.repo,
                    args.test_mode,
                    args.filter
                )

                print("=" * 60)
                self.print_reverse_dependencies(args.package, reverse_deps)

            else:
                # Обычный режим построения графа зависимостей
                print("🔍 Построение графа зависимостей (DFS без рекурсии):")
                dependency_graph, cycles = self.build_dependency_graph_dfs(
                    args.package,
                    args.repo,
                    args.test_mode,
                    args.filter
                )

                print("=" * 60)

                # Вывод информации о циклических зависимостях
                if cycles:
                    print(f"⚠️ Обнаружено циклических зависимостей: {len(cycles)}")
                    for i, cycle in enumerate(cycles, 1):
                        print(f"   {i}. {' -> '.join(cycle)}")
                    print()
                else:
                    print("✅ Циклические зависимости не обнаружены")
                    print()

                # Вывод полного графа зависимостей
                self.print_dependency_graph(dependency_graph, args.package)

                # Генерация Mermaid диаграммы
                print(f"\n📊 Генерация визуализации...")
                mermaid_code = self.generate_mermaid_diagram(dependency_graph, args.package)

                print("📝 Mermaid код:")
                print("-" * 40)
                print(mermaid_code)
                print("-" * 40)

                # Сохранение SVG
                svg_generated = self.save_svg_from_mermaid(mermaid_code, args.output)

                # Сравнение с npm (только в реальном режиме)
                if not args.test_mode and not args.filter and svg_generated:
                    self.compare_with_npm(args.package, dependency_graph)

                # Статистика
                total_packages = len(dependency_graph)
                packages_with_deps = sum(1 for deps in dependency_graph.values() if deps)

                print(f"\n📊 Статистика:")
                print(f"   Всего пакетов в графе: {total_packages}")
                print(f"   Пакетов с зависимостями: {packages_with_deps}")
                print(f"   Циклических зависимостей: {len(cycles)}")

            print(f"\n✅ Этап 5 успешно завершен.")

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            sys.exit(1)


if __name__ == "__main__":
    visualizer = DependencyVisualizer()
    visualizer.run()