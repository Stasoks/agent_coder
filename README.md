# Lua AI Studio (Windows 10/11)

Десктоп-приложение на Python (`PySide6`) для редактирования Lua-кода со встроенным ИИ-чатом.

Реализовано:
- Открытие папки проекта.
- Создание, открытие, просмотр, переименование, удаление файлов и папок в дереве файлов.
- Редактор кода Lua с базовой подсветкой синтаксиса.
- Валидация Lua (базовые статические проверки).
- Встроенный PowerShell-терминал и консоль вывода.
- Чат справа с ИИ.
- Два режима чата: `assistant` и `agent`.
- Debug-режим со вторым окном трассировки этапов выполнения.
- Автоочистка памяти модели при закрытии приложения.

## Возможности ИИ

### Режим `assistant`
- Отвечает на вопросы пользователя.
- Объясняет код из прикрепленных файлов.
- Помогает с идеями и генерацией кода в формате ответа.

### Режим `agent`
- Читает прикрепленные файлы.
- Может возвращать действия по файлам (создание/перезапись/дописание/правка).
- Приложение применяет действия в рамках открытой папки проекта.

Поддерживаемые действия агента:
- `write_file` (`path`, `content`)
- `append_file` (`path`, `content`)
- `replace_in_file` (`path`, `old_text`, `new_text`)

## Стек
- Python 3.11+
- PySide6
- transformers
- torch
- pyinstaller

## Подключение модели Hugging Face

В проекте используется загрузка через `transformers` по аналогии с вашим примером.

Пример (как в коде сервиса):

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-7B-Instruct")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-7B-Instruct")

messages = [{"role": "user", "content": "Who are you?"}]
inputs = tokenizer.apply_chat_template(
		messages,
		add_generation_prompt=True,
		tokenize=True,
		return_dict=True,
		return_tensors="pt",
).to(model.device)

outputs = model.generate(**inputs, max_new_tokens=40)
print(tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:]))
```

По умолчанию модель: `Qwen/Qwen2.5-Coder-7B-Instruct`.
При первом запросе модель загружается в память.

## Структура проекта

```text
agent_coder/
	app/
		core/
			file_ops.py
			settings.py
		services/
			agent_actions.py
			llm_service.py
		ui/
			chat_panel.py
			editor.py
			file_panel.py
			main_window.py
			terminal_panel.py
	main.py
	requirements.txt
	build_exe.bat
```

## Запуск в режиме разработки

```powershell
py -3.11 -m venv .venv311gpu
.venv311gpu\Scripts\activate
pip install -r requirements.txt
pip install --no-cache-dir torch==2.11.0+cu128 --index-url https://download.pytorch.org/whl/cu128
python main.py
```

Проверка, что используется GPU:

```powershell
python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no gpu')"
```

Запуск в debug-режиме (легкая модель + окно логов):

```powershell
python main.py --debug
```

Режим `--debug` использует модель:
- `Qwen/Qwen2.5-Coder-1.5B-Instruct`

Можно вручную выбрать любую модель:

```powershell
python main.py --model Qwen/Qwen2.5-Coder-1.5B-Instruct
```

## Сборка EXE

```powershell
build_exe.bat
```

Скрипт сборки автоматически использует окружение `.venv311gpu` (Python 3.11) и ставит CUDA-сборку `torch==2.11.0+cu128`.

Результат:
- `dist\lua_ai_studio\lua_ai_studio.exe`

Важно:
- Запускайте `exe` только из папки `dist`.
- Файл `build\lua_ai_studio\lua_ai_studio.exe` является промежуточным артефактом PyInstaller и не предназначен для запуска.

## Примечания
- Для локального инференса 7B-модели нужен достаточно мощный ПК (RAM/VRAM).
- Все операции агента ограничены текущей открытой папкой проекта (защита от выхода за root).
- Валидация Lua в этом проекте базовая и не заменяет полноценный парсер/linters.
- В debug-режиме отображаются этапы: загрузка модели, токенизация, генерация, декодирование и применение действий агента.
- Терминал встроен в единое окно консоли (без отдельной строки ввода и кнопки отправки).