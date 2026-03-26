#!/usr/bin/env python3
"""Test agent with 1.5B model"""
import logging
from pathlib import Path
import tempfile
import shutil

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Add project to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.services.llm_service import LlmService
from app.services.agent_actions import AgentActionExecutor

def test_agent():
    """Test agent functionality"""

    # Create temp directory for testing
    test_dir = Path(tempfile.mkdtemp(prefix="agent_test_"))
    logger.info(f"Test directory: {test_dir}")

    try:
        # Create test files
        main_lua = test_dir / "main.lua"
        main_lua.write_text('''function add(a, b)
    return a + b
end

function multiply(a, b)
    return a - b  -- BUG: should be multiplication!
end

print(add(5, 3))
print(multiply(5, 3))
''')

        logger.info(f"Created test file: {main_lua}")
        logger.info(f"Content:\n{main_lua.read_text()}")

        # Initialize agent
        llm_service = LlmService(
            model_name="Qwen/Qwen2.5-Coder-1.5B-Instruct",
            quantization_mode="4bit"
        )

        executor = AgentActionExecutor(test_dir)

        # Test 1: Read and understand file
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Ask agent to fix the multiplication bug")
        logger.info("="*60)

        prompt = "There's a bug in multiply() function - it does subtraction instead of multiplication. Fix it!"
        attached = {"main.lua": main_lua.read_text()}

        def log_progress(msg):
            logger.info(f"[PROGRESS] {msg}")

        def log_token(token):
            print(token, end='', flush=True)

        result = llm_service.ask(
            user_prompt=prompt,
            mode="agent",
            attached_files=attached,
            progress_callback=log_progress,
            token_callback=log_token,
            workspace_root=test_dir,
        )

        logger.info(f"\n\n[RESULT] Reply: {result.text}")
        logger.info(f"[RESULT] Actions: {len(result.actions)} actions")
        for i, action in enumerate(result.actions):
            logger.info(f"  Action {i}: {action.get('type')} - {action.get('path')}")

        # Execute actions
        logger.info("\n" + "="*60)
        logger.info("EXECUTING ACTIONS")
        logger.info("="*60)

        logs = executor.execute(result.actions)
        for log in logs:
            logger.info(f"  {log}")

        # Check result
        logger.info("\n" + "="*60)
        logger.info("FINAL FILE CONTENT")
        logger.info("="*60)
        logger.info(f"\n{main_lua.read_text()}")

        # Check if bug was fixed
        content = main_lua.read_text()
        if "return a * b" in content:
            logger.info("✅ BUG FIXED! multiply() now uses multiplication")
        else:
            logger.warning("❌ BUG NOT FIXED")

        # Test 2: Create new file
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Ask agent to create a new config file")
        logger.info("="*60)

        prompt2 = "Create a config.lua file with game settings: debug=true, volume=100, fps=60"
        attached2 = {}  # No attached files this time

        result2 = llm_service.ask(
            user_prompt=prompt2,
            mode="agent",
            attached_files=attached2,
            progress_callback=log_progress,
            token_callback=log_token,
            workspace_root=test_dir,
        )

        logger.info(f"\n\n[RESULT] Reply: {result2.text}")
        logger.info(f"[RESULT] Actions: {len(result2.actions)} actions")

        logs2 = executor.execute(result2.actions)
        for log in logs2:
            logger.info(f"  {log}")

        # Check if config was created
        config_file = test_dir / "config.lua"
        if config_file.exists():
            logger.info(f"\n✅ Config file created:\n{config_file.read_text()}")
        else:
            logger.warning("❌ Config file was NOT created")

    finally:
        # Cleanup
        logger.info(f"\nCleaning up {test_dir}")
        shutil.rmtree(test_dir, ignore_errors=True)

if __name__ == "__main__":
    test_agent()
