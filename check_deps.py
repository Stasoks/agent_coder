"""Check if all dependencies are properly installed."""
import sys
from pathlib import Path

def check_imports():
    """Check all critical imports."""
    modules_to_check = [
        ('torch', 'PyTorch'),
        ('transformers', 'Transformers'),
        ('PySide6', 'PySide6'),
        ('bitsandbytes', 'BitsAndBytes'),
        ('accelerate', 'Accelerate'),
        ('safetensors', 'SafeTensors'),
        ('huggingface_hub', 'HuggingFace Hub'),
        ('triton', 'Triton'),
        ('peft', 'PEFT (optional, but recommended)'),
    ]

    print("=" * 60)
    print("Dependency Check")
    print("=" * 60)
    print()

    failed = []
    for module_name, display_name in modules_to_check:
        try:
            __import__(module_name)
            print(f"✓ {display_name:30} - OK")
        except ImportError as e:
            status = "MISSING" if module_name != 'peft' else "MISSING (optional)"
            print(f"✗ {display_name:30} - {status}")
            if module_name != 'peft':
                failed.append(module_name)

    print()
    print("=" * 60)

    # Check torch/cuda
    try:
        import torch
        if torch.cuda.is_available():
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"CUDA Available: ✓ YES")
        else:
            print("CUDA Available: ✗ NO (CPU mode only)")
    except Exception as e:
        print(f"GPU Check: ✗ ERROR - {e}")

    print()
    if failed:
        print(f"RESULT: ✗ FAILED - Missing: {', '.join(failed)}")
        print()
        print("Install missing packages:")
        print(f"  pip install {' '.join(failed)}")
        return 1
    else:
        print("RESULT: ✓ ALL DEPENDENCIES OK")
        return 0

if __name__ == "__main__":
    sys.exit(check_imports())
