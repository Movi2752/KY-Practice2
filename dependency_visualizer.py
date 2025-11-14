#!/usr/bin/env python3
"""
Инструмент визуализации графа зависимостей пакетов
Этап 3: Основные операции с графом зависимостей (исправленная версия)
"""

import argparse
import sys
import os
import json
import urllib.request
import urllib.error
from collections import deque


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
            help='Режим работы с тестовым репозиторием'
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
                raise Exception(f"Пакет '{package_name}' не найден в npm реестре")
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
            print("=" * 60)

            # Построение графа зависимостей с помощью DFS
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

            # Статистика
            total_packages = len(dependency_graph)
            packages_with_deps = sum(1 for deps in dependency_graph.values() if deps)

            print(f"\n📊 Статистика:")
            print(f"   Всего пакетов в графе: {total_packages}")
            print(f"   Пакетов с зависимостями: {packages_with_deps}")
            print(f"   Циклических зависимостей: {len(cycles)}")

            print(f"\n✅ Этап 3 успешно завершен.")

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            sys.exit(1)


if __name__ == "__main__":
    visualizer = DependencyVisualizer()
    visualizer.run()