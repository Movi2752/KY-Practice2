## Этап 1

### 1. Источник параметров - опции командной строки
```python
def parse_arguments(self):
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description='Инструмент визуализации графа зависимостей пакетов'
    )
    
    parser.add_argument('--package', type=str, required=True, help='Имя анализируемого пакета')
    parser.add_argument('--repo', type=str, required=True, help='URL-адрес репозитория или путь к файлу тестового репозитория')
    parser.add_argument('--test-mode', action='store_true', help='Режим работы с тестовым репозиторием')
    parser.add_argument('--output', type=str, default='dependency_graph.svg', help='Имя сгенерированного файла с изображением графа')
    parser.add_argument('--filter', type=str, default='', help='Подстрока для фильтрации пакетов')
    
    return parser.parse_args()
```

### 2. Все требуемые параметры присутствуют
- `--package` - имя анализируемого пакета
- `--repo` - URL или путь к файлу
- `--test-mode` - режим тестового репозитория
- `--output` - имя файла с изображением
- `--filter` - подстрока для фильтрации

### 3. Вывод параметров в формате ключ-значение
```python
def print_parameters(self, args):
    """Вывод параметров в формате ключ-значение"""
    print("=== Параметры конфигурации ===")
    print(f"package: {args.package}")
    print(f"repo: {args.repo}")
    print(f"test-mode: {args.test_mode}")
    print(f"output: {args.output}")
    print(f"filter: {args.filter}")
    print("===============================")
```

### 4. Обработка ошибок для всех параметров
```python
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
```

## Демонстрация выполнения требований

Создам тестовый файл для демонстрации:
```bash
echo '{"A": {"dependencies": {"B": "^1.0.0", "C": "^2.0.0"}}}' > test_repo.json
```

### Тест 1: Успешный запуск с валидными параметрами
```bash
python dependency_visualizer.py --package "react" --repo "https://registry.npmjs.org" --output "graph.svg" --filter "test"
```

**Ожидаемый вывод:**
```
=== Параметры конфигурации ===
package: react
repo: https://registry.npmjs.org
test-mode: False
output: graph.svg
filter: test
===============================
Этап 1 успешно завершен. Параметры валидны.
```

### Тест 2: Успешный запуск в тестовом режиме
```bash
python dependency_visualizer.py --package "A" --repo "test_repo.json" --test-mode --output "graph.svg" --filter "dev"
```

**Ожидаемый вывод:**
```
=== Параметры конфигурации ===
package: A
repo: test_repo.json
test-mode: True
output: graph.svg
filter: dev
===============================
Этап 1 успешно завершен. Параметры валидны.
```

### Тест 3: Ошибка - пустое имя пакета
```bash
python dependency_visualizer.py --package "" --repo "https://registry.npmjs.org" --output "graph.svg"
```

**Ожидаемый вывод:**
```
Ошибки валидации:
  - Имя пакета не может быть пустым
```

### Тест 4: Ошибка - пустой репозиторий
```bash
python dependency_visualizer.py --package "react" --repo "" --output "graph.svg"
```

**Ожидаемый вывод:**
```
Ошибки валидации:
  - Репозиторий не может быть пустым
```

### Тест 5: Ошибка - файл не существует в тестовом режиме
```bash
python dependency_visualizer.py --package "A" --repo "nonexistent.json" --test-mode --output "graph.svg"
```

**Ожидаемый вывод:**
```
Ошибки валидации:
  - Файл репозитория не существует: nonexistent.json
```

### Тест 6: Ошибка - неподдерживаемый формат файла
```bash
python dependency_visualizer.py --package "react" --repo "https://registry.npmjs.org" --output "graph.txt"
```

**Ожидаемый вывод:**
```
Ошибки валидации:
  - Неподдерживаемый формат файла. Допустимые: .svg, .png, .jpg, .jpeg
```

### Тест 7: Ошибка - путь не является файлом в тестовом режиме
```bash
mkdir test_dir
python dependency_visualizer.py --package "A" --repo "test_dir" --test-mode --output "graph.svg"
```

**Ожидаемый вывод:**
```
Ошибки валидации:
  - Указанный путь не является файлом: test_dir
```