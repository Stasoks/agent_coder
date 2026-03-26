@echo off
setlocal

if not exist .venv311gpu (
    py -3.11 -m venv .venv311gpu
)

call .venv311gpu\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install --no-cache-dir torch==2.11.0+cu128 --index-url https://download.pytorch.org/whl/cu128

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller --noconfirm --windowed --name lua_ai_studio --collect-all transformers --collect-all tokenizers main.py

if exist build\lua_ai_studio\lua_ai_studio.exe del /f /q build\lua_ai_studio\lua_ai_studio.exe

echo Build complete.
echo Start this file ONLY: dist\lua_ai_studio\lua_ai_studio.exe
endlocal
