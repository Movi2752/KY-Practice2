#!/usr/bin/env python3
"""
Инструмент визуализации графа зависимостей пакетов
Этап 1: Минимальный прототип с конфигурацией
"""

import argparse
import sys
import os


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

    def print_parameters(self, args):
        """Вывод параметров в формате ключ-значение"""
        print("=== Параметры конфигурации ===")
        print(f"package: {args.package}")
        print(f"repo: {args.repo}")
        print(f"test-mode: {args.test_mode}")
        print(f"output: {args.output}")
        print(f"filter: {args.filter}")
        print("===============================")

    def run(self):
        """Основной метод запуска приложения"""
        try:
            # Парсинг аргументов
            args = self.parse_arguments()

            # Валидация аргументов
            errors = self.validate_arguments(args)
            if errors:
                print("Ошибки валидации:")
                for error in errors:
                    print(f"  - {error}")
                sys.exit(1)

            # Вывод параметров
            self.print_parameters(args)

            print("Этап 1 успешно завершен. Параметры валидны.")

        except Exception as e:
            print(f"Критическая ошибка: {e}")
            sys.exit(1)


if __name__ == "__main__":
    visualizer = DependencyVisualizer()
    visualizer.run()