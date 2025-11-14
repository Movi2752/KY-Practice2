## Этап 2: Сбор данных

### 1. Использование формата пакетов JavaScript (npm)
```python
def fetch_package_info_from_npm(self, package_name):
    """Получение информации о пакете из npm реестра"""
    url = f"https://registry.npmjs.org/{package_name}"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise Exception(f"Пакет '{package_name}' не найден в npm реестре")
        else:
            raise Exception(f"Ошибка при запросе к npm реестру: {e}")
    except urllib.error.URLError as e:
        raise Exception(f"Ошибка сети: {e}")
    except json.JSONDecodeError as e:
        raise Exception(f"Ошибка парсинга JSON ответа: {e}")
```

### 2. Извлечение информации о прямых зависимостях из репозитория
```python
def get_direct_dependencies(self, package_name, repo_url, test_mode=False):
    """Получение прямых зависимостей пакета"""
    if test_mode:
        return self.get_dependencies_from_test_file(package_name, repo_url)
    else:
        return self.get_dependencies_from_npm(package_name)

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
    
    raise Exception(f"Пакет '{package_name}' не найден в тестовом файле")
```

### 3. Вывод прямых зависимостей на экран (только для этого этапа)
```python
def print_direct_dependencies(self, package_name, dependencies):
    """Вывод прямых зависимостей на экран"""
    if not dependencies:
        print(f"Пакет '{package_name}' не имеет зависимостей")
        return
    
    print(f"Прямые зависимости пакета '{package_name}':")
    for dep_name, version in dependencies.items():
        print(f"  - {dep_name}: {version}")
```

### 4. Запрет на использование менеджеров пакетов и сторонних библиотек
- Используются только стандартные библиотеки Python: `urllib.request`, `json`
- Не используются npm, yarn или другие менеджеры пакетов
- Не используются сторонние библиотеки для HTTP-запросов

## Демонстрация выполнения требований

### Тест 1: Реальный режим - Express (работает)
```bash
python dependency_visualizer.py --package "express" --repo "https://registry.npmjs.org" --output "graph.svg"
```

**Ожидаемый вывод:**
```
🎯 Анализ пакета: express
🔧 Режим: реальный
============================================================
🔍 Анализ структуры пакета 'express':
   - Получены данные из npm registry
   ✅ Последняя версия из dist-tags: 5.1.0
   📋 Поля в информации о версии: ['name', 'version', 'keywords', 'author', 'license', '_id', 'maintainers', 'contributors', 'homepage', 'bugs', 'dist', 'engines', 'funding', 'gitHead', 'scripts', '_npmUser', 'repository', '_npmVersion', 'description', 'directories', '_nodeVersion', 'dependencies', '_hasShrinkwrap', 'devDependencies', '_npmOperationalInternal']
   ✅ Найдены зависимости в поле 'dependencies': 27 шт.
   📦 Найдены зависимости в поле 'devDependencies': 16 шт.
============================================================
📦 Прямые зависимости пакета 'express':
   - qs: ^6.14.0
   - etag: ^1.8.1
   - once: ^1.4.0
   - send: ^1.1.0
   - vary: ^1.1.2
   - debug: ^4.4.0
   - fresh: ^2.0.0
   - cookie: ^0.7.1
   - router: ^2.2.0
   - accepts: ^2.0.0
   - type-is: ^2.0.1
   - parseurl: ^1.3.3
   - statuses: ^2.0.1
   - encodeurl: ^2.0.0
   - mime-types: ^3.0.0
   - proxy-addr: ^2.0.7
   - body-parser: ^2.2.0
   - escape-html: ^1.0.3
   - http-errors: ^2.0.0
   - on-finished: ^2.4.1
   - content-type: ^1.0.5
   - finalhandler: ^2.1.0
   - range-parser: ^1.2.1
   - serve-static: ^2.2.0
   - cookie-signature: ^1.2.1
   - merge-descriptors: ^2.0.0
   - content-disposition: ^1.0.0

✅ Этап 2 успешно завершен.
```

### Тест 2: Тестовый режим - простой JSON файл
```bash
python dependency_visualizer.py --package "A" --repo "test_repo_simple.json" --test-mode --output "graph.svg"
```

**Ожидаемый вывод:**
```
🎯 Анализ пакета: A
🔧 Режим: тестовый
============================================================
🔍 Анализ тестового файла:
   - Загружен файл: test_repo_simple.json
   - Тип данных: <class 'dict'>
   ✅ Найдены зависимости в структуре одного пакета: 3 шт.
============================================================
📦 Прямые зависимости пакета 'A':
   - B: ^1.0.0
   - C: ^2.0.0
   - D: ^3.0.0

✅ Этап 2 успешно завершен.
```

### Тест 3: Тестовый режим - сложная структура с несколькими пакетами
```bash
python dependency_visualizer.py --package "A" --repo "test_repo_complex.json" --test-mode --output "graph.svg"
```

**Ожидаемый вывод:**
```
🎯 Анализ пакета: A
🔧 Режим: тестовый
============================================================
🔍 Анализ тестового файла:
   - Загружен файл: test_repo_complex.json
   - Тип данных: <class 'dict'>
   ✅ Найдены зависимости в структуре нескольких пакетов: 2 шт.
============================================================
📦 Прямые зависимости пакета 'A':
   - B: ^1.0.0
   - C: ^2.0.0

✅ Этап 2 успешно завершен.
```

### Тест 4: Тестовый режим - пакет без зависимостей
```bash
python dependency_visualizer.py --package "simple-package" --repo "test_repo_no_deps.json" --test-mode --output "graph.svg"
```

**Ожидаемый вывод:**
```
🎯 Анализ пакета: simple-package
🔧 Режим: тестовый
============================================================
🔍 Анализ тестового файла:
   - Загружен файл: test_repo_no_deps.json
   - Тип данных: <class 'dict'>
   ✅ Найдены зависимости в структуре одного пакета: 0 шт.
============================================================
📭 Пакет 'simple-package' не имеет зависимостей

✅ Этап 2 успешно завершен.
```

### Тест 5: Ошибка - невалидный JSON файл
```bash
python dependency_visualizer.py --package "A" --repo "test_repo_invalid.json" --test-mode --output "graph.svg"
```

**Ожидаемый вывод:**
```
❌ Ошибка: Ошибка парсинга JSON файла: Expecting ',' delimiter: line 5 column 1 (char 52)
```

### Тест 6: Ошибка - пакет не найден в тестовом файле
```bash
python dependency_visualizer.py --package "Z" --repo "test_repo_complex.json" --test-mode --output "graph.svg"
```

**Ожидаемый вывод:**
```
🎯 Анализ пакета: Z
🔧 Режим: тестовый
============================================================
🔍 Анализ тестового файла:
   - Загружен файл: test_repo_complex.json
   - Тип данных: <class 'dict'>
   ❌ Пакет 'Z' не найден в тестовом файле
❌ Ошибка: Пакет 'Z' не найден в тестовом файле
```