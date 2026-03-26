# 🚀 Lua AI Studio

**Полнофункциональная IDE для разработки Lua с интегрированным ИИ-ассистентом.**

Пишите код быстрее с помощью встроенного ИИ, который понимает контекст вашего проекта и может автоматически создавать, редактировать и улучшать ваши файлы Lua.

![Status](https://img.shields.io/badge/status-beta-yellow)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Возможности

### 🎯 IDE Функционал
- ✅ **Встроенный редактор кода** с подсветкой синтаксиса Lua
- ✅ **Навигация по файлам** - интуитивное дерево проекта
- ✅ **Управление файлами** - создание, переименование, удаление
- ✅ **Встроенный терминал** (PowerShell)
- ✅ **Валидация Lua кода** -基 базовые проверки синтаксиса
- ✅ **Две цветовые темы** - светлая и тёмная
- ✅ **Отладочный режим** - логирование всех операций в реальном времени

### 🤖 ИИ Помощник

#### 📝 Режим "Ассистент"
Общайтесь с ИИ, получайте советы и объяснения:
- Вопросы о коде и синтаксис Lua
- Объяснение существующего кода
- Генерация кода по описанию
- Real-time потоковый вывод ответов

#### 🔧 Режим "Агент" (Автоматизация)
ИИ сам редактирует ваши файлы:
- **Читает файлы** перед редактированием
- **Создаёт новые файлы** по вашему запросу
- **Редактирует существующий код** с хирургической точностью
- **Добавляет код** в конец файлов
- **Работает безопасно** - не выходит за границы вашей папки проекта

**Пример агента в действии:**
```
Вы: "Исправь баг в main.lua - здоровье игрока должно увеличиваться"

Агент:
1. 📖 Читает main.lua
2. 🔍 Находит ошибку: "health = health - 10"
3. ✏️  Меняет на: "health = health + 10"
4. ✅ Готово!
```

---

## 🎮 Использование

### Быстрый старт

```bash
# 1. Установите зависимости
pip install -r requirements.txt

# 2. Установите PyTorch с поддержкой GPU (CUDA 13.0+)
pip install torch --index-url https://download.pytorch.org/whl/cu130

# 3. Запустите приложение
python main.py
```

### Режимы запуска

**Обычный режим** (сеть оптимальна):
```bash
python main.py
```

**Быстрый тест** (лёгкая 1.5B модель + дебаг консоль):
```bash
python main.py --debug
```

**Выбрать модель вручную**:
```bash
python main.py --model "Qwen/Qwen2.5-Coder-1.5B-Instruct"
python main.py --model "Meta-Llama-3-8B-Instruct"
```

**Квантизация** (для экономии памяти):
```bash
python main.py --quantization 4bit  # максимальное сжатие (4x меньше памяти)
python main.py --quantization 8bit  # сжатие + качество (2x меньше памяти)
python main.py --quantization none  # максимальное качество
```

---

## 📋 Системные требования

| Компонент | Минимум | Рекомендуемо |
|-----------|---------|-------------|
| **ОС** | Windows 10 | Windows 11 |
| **Python** | 3.11+ | 3.11+ |
| **GPU** | RTX 2060 (6GB) | RTX 3060+ (12GB) |
| **RAM** | 8GB | 16GB+ |
| **CUDA** | 12.1+ | 13.0 |

**💡 Совет:** Используйте 1.5B модель для слабых ПК, 7B для полноты функций.

---

## 🏗️ Архитектура

```
Lua AI Studio/
├── app/
│   ├── core/              # 🔧 Backend логика
│   │   ├── file_ops.py    # Работа с файлами
│   │   └── settings.py    # Конфигурация
│   │
│   ├── services/          # 🤖 ИИ и обработка
│   │   ├── llm_service.py # Основное ядро
│   │   └── agent_actions.py # Выполнение действий
│   │
│   └── ui/                # 🎨 Интерфейс
│       ├── main_window.py # Главное окно
│       ├── chat_panel.py  # Чат ИИ
│       ├── editor.py      # Редактор Lua
│       ├── file_panel.py  # Дерево файлов
│       └── terminal_panel.py # Консоль
│
├── main.py                # Точка входа
└── requirements.txt       # Зависимости
```

---

## 🔧 Для разработчиков

### Установка в режиме разработки

```bash
# Клонируйте репো
git clone https://github.com/yourusername/lua-ai-studio.git
cd lua-ai-studio

# Создайте виртуальное окружение
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Установите зависимости
pip install -r requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cu130
```

### Структура кода

**Редактирование интерфейса:**
```python
# app/ui/main_window.py - главное окно
# app/ui/chat_panel.py - чат
# Редактируй классы QWidget, добавляй кнопки в _build_toolbar()
```

**Изменение ИИ логики:**
```python
# app/services/llm_service.py - промпты, парсинг JSON, генерация
# _build_messages() - система промптов
# _parse_agent_output() - парсинг действий агента
```

**Добавление новых действий:**
```python
# app/services/agent_actions.py - добавьте новый if action_type
# Затем обновите _sanitize_actions() в llm_service.py
```

### Тестирование

```bash
# Проверка синтаксиса
python -m py_compile app/services/llm_service.py

# Запуск в дебаг режиме
python main.py --debug --model "Qwen/Qwen2.5-Coder-1.5B-Instruct"
```

### Сборка исполняемого файла

```bash
# Требуется предварительно установить PyInstaller
pip install pyinstaller

# Сборка (автоматически)
python -m PyInstaller --onedir --windowed --add-data "app:app" main.py
```

---

## 🐛 Известные проблемы

- **AI медленный на слабых GPU** → используйте `--quantization 4bit` или 1.5B модель
- **Out of Memory** → уменьшите размер модели или контекста
- **Чат не отвечает** → проверьте логи в дебаг окне (--debug флаг)

---

## 🤝 Как помочь

### Отправка багов
1. Откройте [Issues](https://github.com/yourusername/lua-ai-studio/issues)
2. Опишите проблему с шагами воспроизведения
3. Приложите логи из дебаг режима (`--debug`)

### Предложение фич
- Новые действия агента (например, `rename_file`)
- Улучшения парсера Lua
- Новые цветовые темы
- Поддержка других языков

### Создание PR
```bash
git checkout -b feature/your-feature
git commit -am "Add your feature"
git push origin feature/your-feature
```

Пожалуйста, следуйте PEP 8 и добавляйте тесты для новых фич.

---

## 📚 Примеры использования

### Пример 1: Автоматическое исправление кода

```
🧑 Пользователь: "В main.lua есть баг - функция не возвращает значение"

🤖 Большой язык модели:
{
  "reply": "Нашел проблему - функция использует 'print' вместо 'return'",
  "actions": [
    {
      "type": "read_file",
      "path": "main.lua"
    },
    {
      "type": "replace_in_file",
      "path": "main.lua",
      "old_text": "function getValue()\n  print(42)\nend",
      "new_text": "function getValue()\n  return 42\nend"
    }
  ]
}

✅ Результат: Файл обновлен автоматически
```

### Пример 2: Объяснение кода в режиме ассистента

```
🧑 Пользователь: "Что делает эта функция?" (отправляет файл)

🤖 assistant:
Это функция для проверки, является ли число чётным.
Она использует оператор модуля (%) для получения остатка от деления на 2.
Если остаток равен 0 - число чётное, иначе - нечётное.
```

---

## 📦 Зависимости

- **PySide6** - GUI фреймворк
- **transformers** - загрузка моделей HuggingFace
- **torch** - глубокое обучение (с CUDA поддержкой)
- **bitsandbytes** - квантизация моделей
- **safetensors** - безопасная загрузка весов

---

## 📄 Лицензия

MIT License - смотрите [LICENSE](LICENSE) файл.

---

## 🙏 Благодарности

- [HuggingFace](https://huggingface.co) - модели и библиотеки
- [PyTorch](https://pytorch.org) - фреймворк для ML
- [PySide](https://wiki.qt.io/Qt_for_Python) - Qt для Python

---

## 📞 Контакты

- **GitHub Issues** - для багов и новых идей
- **Discussions** - для вопросов и обсуждений

---

**Последнее обновление:** Март 2026

Приятной разработки! 🎉
