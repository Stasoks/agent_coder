# Lua AI Studio - Run Instructions

## ✅ Improvements Applied

### 1. **GPU Acceleration Fixed**
- Model now loads directly to GPU (CUDA) for maximum performance
- Automatic fallback to distribution if GPU memory is full
- Detailed GPU info logging (name, memory)
- TF32 optimization enabled for faster inference

### 2. **Real-time Token Streaming**
- Tokens now display in real-time as they're generated
- Separate handling for agent mode (shows reply tokens, not action tokens)
- Smooth streaming with proper threading

### 3. **Enhanced Debug Console**
- Color-coded log categories (INIT, CHAT, LOAD, GEN, PARSE, AGENT, ERROR, PERF, TOKEN)
- Timestamp for each message
- Performance metrics tracking (tokens/s, generation time)
- Statistics dashboard with averages and totals
- GPU information logging

### 4. **Improved UI Design**
- Modern dark and light themes with better colors
- Enhanced button styling and hover effects
- Better scrollbar behavior
- Improved toolbar with separators
- Smoother animations and transitions
- Better focus states

---

## 🚀 How to Run

### Option 1: Use Pre-Built Executable (Recommended)
```powershell
.\dist\lua_ai_studio\lua_ai_studio.exe
```
**Advantages:**
- No setup required
- Single standalone file
- All dependencies included
- Fastest startup

### Option 2: Run with Debug Console
```powershell
.venv311gpu\Scripts\python.exe main.py --debug --model "Qwen/Qwen2.5-Coder-1.5B-Instruct"
```
**Use this if:**
- You want to see debug information
- You want to use a custom model
- You're developing/testing

### Option 3: Activate venv First (Alternative)
```powershell
.venv311gpu\Scripts\Activate.ps1
python main.py --debug --model "Qwen/Qwen2.5-Coder-1.5B-Instruct"
```

---

## 🎯 Key Features

### GPU Support
- Loads full model on GPU for fast inference
- Automatic memory management
- Shows GPU info in debug console

### Real-time Streaming
- Watch tokens appear as they're generated
- Agent mode shows only the AI's reply, not internal actions
- Smooth streaming without UI blocking

### Debug Mode
- Run with `--debug` flag to see detailed console
- Performance metrics
- Token counts and generation speed
- Category-based color-coded logs

### Theme Switching
- Use toolbar buttons to switch between light/dark themes
- Themes persist during session
- Both themes optimized for clarity

---

## 📊 Performance Notes

### Expected Generation Speeds
- **With GPU (RTX 4090+)**: 50-200+ tok/s
- **With GPU (RTX 3060+)**: 30-80 tok/s
- **With GPU (RTX 2060+)**: 10-30 tok/s
- **With CPU**: 1-5 tok/s (not recommended)

### Optimization Tips
1. Keep "Do Sample" enabled for faster generation
2. Use appropriate `max_new_tokens` (1024 is default)
3. Monitor GPU memory with debug console
4. Use float16 (enabled by default) for speed

---

## 🐛 Troubleshooting

### "CUDA available: False" in debug console
- GPU/CUDA not installed or not detected
- Install: `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118`

### Very slow generation (1-2 tok/s)
- Model is running on CPU
- Check GPU availability in debug console
- Restart the application
- Check GPU VRAM with `nvidia-smi`

### "Tensor.item() cannot be called on meta tensors"
- This is now fixed! Model properly loaded to GPU
- If you see this, try restarting

### Application crashes on startup
- Update CUDA: `nvidia-smi` and check driver version
- Clear GPU cache: Restart computer
- Run from source with debug mode to see error

---

## 📝 Debug Console Features

### Categories
- **INIT** (Blue) - Application initialization
- **CHAT** (Orange) - Chat messages and prompts
- **LOAD** (Light Blue) - Model loading
- **GEN** (Teal) - Generation progress
- **PARSE** (Green) - JSON parsing results
- **AGENT** (Gold) - Agent mode actions
- **ERROR** (Red) - Errors and warnings
- **PERF** (Pink) - Performance metrics
- **TOKEN** (Sky Blue) - Token counts

### Statistics
- Click "Show Stats" button to see aggregated metrics
- Total tokens generated across all prompts
- Generation time statistics (avg, min, max)
- Number of generations performed

---

## 💡 Tips for Best Experience

1. **First Run**: Allow time for model to download and cache
2. **GPU Memory**: Monitor with debug console
3. **Streaming**: Agent mode shows reply tokens in real-time
4. **Performance**: Use shorter prompts for faster response
5. **Theme**: Dark theme recommended for extended use

---

## 🔧 Command-line Options

```bash
python main.py --help
python main.py --debug                    # With debug console
python main.py --model MODEL_NAME          # Use specific model
python main.py --debug --model MODEL_NAME  # Both options
```

---

Enjoy the improved Lua AI Studio! 🎉
