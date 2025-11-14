#!/usr/bin/env python3
"""
Инструмент визуализации графа зависимостей пакетов
Этап 2: Сбор данных (исправленная версия)
"""

import argparse
import sys
import os
import json
import urllib.request
import urllib.error


class DependencyVisualizer:
    def __init__(self):
        self.params = {}

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

            print(f"🔍 Анализ структуры пакета '{package_name}':")
            print(f"   - Получены данные из npm registry")

            # Проверяем основные поля в ответе
            if 'versions' not in package_info:
                print("   ❌ Поле 'versions' отсутствует в ответе")
                return {}

            # Получаем последнюю версию
            latest_version = None
            if 'dist-tags' in package_info and 'latest' in package_info['dist-tags']:
                latest_version = package_info['dist-tags']['latest']
                print(f"   ✅ Последняя версия из dist-tags: {latest_version}")
            else:
                # Если нет latest, берем последнюю версию из versions
                versions = list(package_info.get('versions', {}).keys())
                if not versions:
                    print("   ❌ Версии не найдены")
                    return {}
                latest_version = sorted(versions)[-1]
                print(f"   ✅ Последняя версия (из списка версий): {latest_version}")

            # Получаем информацию о версии
            version_info = package_info['versions'].get(latest_version, {})

            if not version_info:
                print(f"   ❌ Информация о версии {latest_version} не найдена")
                return {}

            print(f"   📋 Поля в информации о версии: {list(version_info.keys())}")

            # Ищем зависимости в различных возможных полях
            dependencies = {}

            # Основное поле dependencies
            if 'dependencies' in version_info:
                dependencies = version_info['dependencies']
                print(f"   ✅ Найдены зависимости в поле 'dependencies': {len(dependencies)} шт.")
            else:
                print("   ❌ Поле 'dependencies' не найдено")

            # Проверяем другие возможные поля с зависимостями
            dependency_fields = ['peerDependencies', 'devDependencies', 'optionalDependencies']
            for field in dependency_fields:
                if field in version_info:
                    print(f"   📦 Найдены зависимости в поле '{field}': {len(version_info[field])} шт.")
                    # Для этапа 2 мы фокусируемся только на основных зависимостях
                    # dependencies.update(version_info[field])  # Раскомментировать если нужны все типы зависимостей

            return dependencies

        except Exception as e:
            print(f"   ❌ Ошибка при получении зависимостей: {e}")
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

        print(f"🔍 Анализ тестового файла:")
        print(f"   - Загружен файл: {file_path}")
        print(f"   - Тип данных: {type(data)}")

        # Ищем информацию о пакете в тестовом файле
        if isinstance(data, dict):
            # Если файл содержит информацию об одном пакете
            if data.get('name') == package_name or 'dependencies' in data:
                deps = data.get('dependencies', {})
                print(f"   ✅ Найдены зависимости в структуре одного пакета: {len(deps)} шт.")
                return deps
            # Если файл содержит информацию о нескольких пакетах
            elif package_name in data:
                package_data = data[package_name]
                if isinstance(package_data, dict) and 'dependencies' in package_data:
                    deps = package_data['dependencies']
                    print(f"   ✅ Найдены зависимости в структуре нескольких пакетов: {len(deps)} шт.")
                    return deps
                elif isinstance(package_data, dict):
                    print(f"   ✅ Найдены прямые зависимости: {len(package_data)} шт.")
                    return package_data
                else:
                    print(f"   ❌ Неподдерживаемый формат данных для пакета '{package_name}'")
        elif isinstance(data, list):
            # Если файл содержит список пакетов
            for package in data:
                if package.get('name') == package_name:
                    deps = package.get('dependencies', {})
                    print(f"   ✅ Найдены зависимости в списке пакетов: {len(deps)} шт.")
                    return deps

        print(f"   ❌ Пакет '{package_name}' не найден в тестовом файле")
        raise Exception(f"Пакет '{package_name}' не найден в тестовом файле")

    def get_direct_dependencies(self, package_name, repo_url, test_mode=False):
        """Получение прямых зависимостей пакета"""
        if test_mode:
            return self.get_dependencies_from_test_file(package_name, repo_url)
        else:
            return self.get_dependencies_from_npm(package_name)

    def print_direct_dependencies(self, package_name, dependencies):
        """Вывод прямых зависимостей на экран"""
        if not dependencies:
            print(f"📭 Пакет '{package_name}' не имеет зависимостей")
            return

        print(f"📦 Прямые зависимости пакета '{package_name}':")
        for dep_name, version in dependencies.items():
            print(f"   - {dep_name}: {version}")

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
            print("=" * 60)

            # Получение прямых зависимостей
            dependencies = self.get_direct_dependencies(
                args.package,
                args.repo,
                args.test_mode
            )

            print("=" * 60)
            # Вывод прямых зависимостей (требование этапа 2)
            self.print_direct_dependencies(args.package, dependencies)

            print(f"\n✅ Этап 2 успешно завершен.")

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            sys.exit(1)


if __name__ == "__main__":
    visualizer = DependencyVisualizer()
    visualizer.run()