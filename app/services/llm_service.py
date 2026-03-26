from __future__ import annotations

import gc
import json
import logging
import queue
import re
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Any

import torch
from PySide6.QtCore import QObject, QThread, Signal
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer, BitsAndBytesConfig

from app.core.settings import DEFAULT_MODEL

# Try to import gptqmodel for AWQ support
try:
    from gptqmodel import GPTQModel
    HAS_GPTQMODEL = True
except ImportError:
    HAS_GPTQMODEL = False

# Setup logging to file
log_file = Path.cwd() / "model_load.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LogCategory(Enum):
    """Log categories for structured logging."""
    INIT = "INIT"
    CHAT = "CHAT"
    LOAD = "LOAD"
    GEN = "GEN"
    PARSE = "PARSE"
    AGENT = "AGENT"
    ERROR = "ERROR"


@dataclass(slots=True)
class ChatResult:
    text: str
    actions: list[dict[str, Any]]


@dataclass(slots=True)
class LogInfo:
    """Structured log information."""
    category: LogCategory
    message: str
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.perf_counter()


class LlmService:
    def __init__(self, model_name: str = DEFAULT_MODEL, quantization_mode: str = "4bit") -> None:
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.quantization_mode = quantization_mode  # "4bit", "8bit", "none"

    def load_if_needed(self, progress_callback: Callable[[str], None] | None = None) -> None:
        if self.model is not None and self.tokenizer is not None:
            msg = "Model is already loaded."
            logger.info(msg)
            if progress_callback is not None:
                progress_callback(msg)
            return

        try:
            # Clear GPU memory before loading
            logger.info("Clearing GPU cache and memory...")
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.reset_peak_memory_stats()
                logger.info("GPU cache cleared")

            msg = f"Loading tokenizer: {self.model_name}"
            logger.info(msg)
            if progress_callback is not None:
                progress_callback(msg)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            logger.info("Tokenizer loaded successfully")

            use_cuda = torch.cuda.is_available()

            if use_cuda:
                # Log GPU info
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                gpu_props = torch.cuda.get_device_properties(0)
                gpu_info = f"GPU: {gpu_name} ({gpu_memory:.1f}GB), Compute Capability: {gpu_props.major}.{gpu_props.minor}"
                logger.info(gpu_info)
                if progress_callback is not None:
                    progress_callback(gpu_info)

                # Enable TF32 on supported GPUs
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                logger.info("TF32 enabled on GPU")

            dtype = torch.float16 if use_cuda else torch.float32
            device_note = "CUDA" if use_cuda else "CPU"
            quant_msg = f"with {self.quantization_mode.upper()} quantization" if use_cuda and self.quantization_mode != "none" else ""

            msg = f"Loading model weights: {self.model_name} ({device_note}) {quant_msg}"
            logger.info(msg)
            if progress_callback is not None:
                progress_callback(msg)

            # Load model with appropriate quantization
            if use_cuda and self.quantization_mode != "none":
                try:
                    logger.info(f"Creating {self.quantization_mode}-bit quantization config...")

                    if self.quantization_mode == "4bit":
                        quantization_config = BitsAndBytesConfig(
                            load_in_4bit=True,
                            bnb_4bit_use_double_quant=True,
                            bnb_4bit_quant_type="nf4",
                            bnb_4bit_compute_dtype=torch.float16,
                        )
                        if progress_callback is not None:
                            progress_callback("[4-BIT] Loading with NF4 quantization...")
                    else:  # 8bit
                        quantization_config = BitsAndBytesConfig(
                            load_in_8bit=True,
                            bnb_8bit_use_double_quant=True,
                            bnb_8bit_compute_dtype=torch.float16,
                        )
                        if progress_callback is not None:
                            progress_callback("[8-BIT] Loading with INT8 quantization...")

                    logger.info(f"Starting model load with {self.quantization_mode}-bit quantization...")

                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        quantization_config=quantization_config,
                        device_map="auto",
                        low_cpu_mem_usage=True,
                    )

                    logger.info(f"{self.quantization_mode.upper()} quantization applied successfully!")
                    if progress_callback is not None:
                        progress_callback(f"[SUCCESS] {self.quantization_mode.upper()} quantization applied!")

                except RuntimeError as cuda_error:
                    logger.error(f"CUDA/Runtime Error during quantization load: {str(cuda_error)}", exc_info=True)
                    msg = f"[ERROR] GPU error during quantization: {str(cuda_error)[:60]}..."
                    if progress_callback is not None:
                        progress_callback(msg)

                    torch.cuda.empty_cache()
                    torch.cuda.reset_peak_memory_stats()
                    gc.collect()
                    logger.info("Falling back to float16 mode...")

                    # Fallback: load without quantization
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        torch_dtype=dtype,
                        device_map="auto",
                        low_cpu_mem_usage=True,
                    )
                    logger.info("Model loaded in float16 (no quantization)")
                    if progress_callback is not None:
                        progress_callback("[WARNING] Loaded in float16 (quantization failed)")

                except Exception as e:
                    logger.error(f"Unexpected error during quantization load: {str(e)}", exc_info=True)
                    msg = f"[CRITICAL] {str(e)[:80]}"
                    if progress_callback is not None:
                        progress_callback(msg)
                    raise
            else:
                # Load without quantization
                device_map = "cpu" if not use_cuda else "auto"
                logger.info(f"Loading model without quantization (device_map={device_map})...")

                # Check if this is an AWQ model (pre-quantized)
                is_awq = "awq" in self.model_name.lower()

                if is_awq and HAS_GPTQMODEL:
                    logger.info("Detected AWQ model - loading with GPTQModel for proper GPU placement...")
                    try:
                        self.model = GPTQModel.from_pretrained(
                            self.model_name,
                            device="cuda:0" if use_cuda else "cpu",
                            use_safetensors=True,
                        )
                        logger.info("AWQ model loaded successfully on GPU")
                        if progress_callback is not None:
                            progress_callback("[AWQ] Model loaded on GPU!")
                    except Exception as e:
                        logger.warning(f"GPTQModel failed for AWQ: {str(e)}, falling back to AutoModel...")
                        self.model = AutoModelForCausalLM.from_pretrained(
                            self.model_name,
                            torch_dtype=dtype,
                            device_map=device_map,
                            low_cpu_mem_usage=True,
                        )
                else:
                    # Regular quantized or non-quantized model
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        torch_dtype=dtype,
                        device_map=device_map,
                        low_cpu_mem_usage=True,
                    )
                logger.info("Model loaded successfully")

            # Ensure model is in eval mode
            self.model.eval()
            logger.info("Model set to eval mode")

            msg = "Model loaded and ready."
            logger.info(msg)
            if progress_callback is not None:
                progress_callback(msg)

        except Exception as e:
            logger.critical(f"FATAL ERROR in load_if_needed: {str(e)}", exc_info=True)
            msg = f"[FATAL] Model loading failed. Check model_load.log for details: {str(e)[:100]}"
            if progress_callback is not None:
                progress_callback(msg)
            raise

    def shutdown(self, progress_callback: Callable[[str], None] | None = None) -> None:
        if progress_callback is not None:
            progress_callback("Releasing model resources...")
        self.model = None
        self.tokenizer = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        if progress_callback is not None:
            progress_callback("Model resources released.")

    def _build_messages(
        self,
        user_prompt: str,
        mode: str,
        attached_files: dict[str, str],
        workspace_root: Path | None = None,
    ) -> list[dict[str, str]]:
        if mode == "agent":
            system = (
                "# CODING AGENT - PRECISE FILE EDITING INSTRUCTIONS\n\n"
                "You are an intelligent Lua coding agent. Your task is to analyze code, understand patterns, and edit files precisely.\n\n"

                "## CRITICAL RULES (MUST FOLLOW EXACTLY):\n"
                "1. **ALWAYS START BY READING** - Use read_file FIRST to see current content before ANY edit\n"
                "2. **EXACT TEXT MATCHING** - For replace_in_file, old_text MUST match exactly (character-by-character, including spaces/tabs)\n"
                "3. **SURGICAL EDITS ONLY** - Replace minimal code, preserve everything else\n"
                "4. **WRITE ONLY NEW FILES** - Use write_file ONLY for files that don't exist (never overwrite existing!)\n"
                "5. **VERIFY EXISTENCE** - Always check if file exists before modifying\n\n"

                "## RESPONSE FORMAT (JSON ONLY - NO OTHER TEXT):\n"
                '{"reply": "Brief message", "actions": [...]}\n\n'

                "## ACTION TYPES (WITH EXACT EXAMPLES):\n\n"

                "### 1. READ FILE (diagnose before editing)\n"
                '{"type": "read_file", "path": "main.lua"}\n'
                "Use this FIRST to see what's inside before modifying!\n\n"

                "### 2. WRITE NEW FILE (only if it doesn't exist)\n"
                '{"type": "write_file", "path": "config.lua", "content": "return {\\n  debug = true\\n}"}\n'
                "NEVER use this for existing files - use replace_in_file instead!\n\n"

                "### 3. REPLACE IN EXISTING FILE (for edits)\n"
                '{"type": "replace_in_file", "path": "main.lua", "old_text": "local x = 5", "new_text": "local x = 10"}\n'
                "Important:\n"
                "  - old_text must be EXACT (including indentation)\n"
                "  - Can be single line or multiple lines\n"
                "  - Only replaces FIRST occurrence\n\n"

                "### 4. APPEND TO FILE (add at end)\n"
                '{"type": "append_file", "path": "main.lua", "content": "\\nprint(\'Done!\')"}\n'
                "Use only when adding new code at the end without modifying existing code.\n\n"

                "## WORKFLOW EXAMPLE:\n"
                "User: 'Fix the bug in main.lua that causes player health to not increase'\n"
                "1. Read: {\"type\": \"read_file\", \"path\": \"main.lua\"}\n"
                "2. Analyze the content (provided in Attached files)\n"
                "3. Find buggy code: 'health = health - 10'\n"
                "4. Replace: {\"type\": \"replace_in_file\", \"path\": \"main.lua\", \"old_text\": \"health = health - 10\", \"new_text\": \"health = health + 10\"}\n"
                "5. Reply: 'Fixed health bug: changed subtraction to addition'\n\n"

                "## IMPORTANT REMINDERS:\n"
                "- If you need to see file content before editing, ALWAYS use read_file first\n"
                "- Test old_text string by checking it appears in Attached files\n"
                "- Preserve indentation exactly when replacing\n"
                "- Don't create new files unless explicitly asked\n"
                "- Return JSON only - no markdown, no explanations outside JSON\n"
                "- Each action must have 'type' and 'path' keys minimum\n\n"

                "Now respond with ONLY JSON for the user's request."
            )
        else:
            system = (
                "You are a helpful Lua programming assistant. "
                "Explain code clearly, provide best practices, keep responses concise and helpful."
            )

        files_block = ""

        # Add available workspace files
        if workspace_root and mode == "agent":
            try:
                lua_files = list(workspace_root.glob("**/*.lua"))
                txt_files = list(workspace_root.glob("**/*.txt"))
                py_files = list(workspace_root.glob("**/*.py"))
                all_files = sorted(set(lua_files + txt_files + py_files))

                if all_files:
                    file_list = "\n".join([f"  • {f.relative_to(workspace_root)}" for f in all_files[:30]])
                    files_block += f"\n\n## WORKSPACE FILES:\n{file_list}"
                    if len(all_files) > 30:
                        files_block += f"\n  ... and {len(all_files) - 30} more files"
            except Exception as e:
                logger.warning(f"Could not list workspace files: {e}")

        # Add attached file contents
        if attached_files:
            chunks = []
            for p, content in attached_files.items():
                # Limit content display to prevent huge contexts
                lines = content.split('\n')
                if len(lines) > 100:
                    chunks.append(f"FILE: {p} ({len(lines)} lines)\n{chr(10).join(lines[:50])}\n... ({len(lines) - 50} more lines)")
                else:
                    chunks.append(f"FILE: {p}\n{content}")
            files_block += "\n\n## ATTACHED FILE CONTENTS:\n" + "\n".join(chunks)

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt + files_block},
        ]

    def _sanitize_actions(self, raw_actions: Any) -> list[dict[str, Any]]:
        if not isinstance(raw_actions, list):
            return []

        allowed = {"write_file", "append_file", "replace_in_file", "read_file"}
        cleaned: list[dict[str, Any]] = []
        for action in raw_actions:
            if not isinstance(action, dict):
                continue
            action_type = str(action.get("type", "")).strip().lower()
            path = str(action.get("path", "")).strip()
            if action_type not in allowed or not path:
                continue
            cleaned.append(action)
        return cleaned

    def _extract_json_candidates(self, text: str) -> list[str]:
        candidates: list[str] = []
        stripped = text.strip()
        if stripped:
            candidates.append(stripped)

        # Try fenced code blocks first.
        fence_pattern = re.compile(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)
        for match in fence_pattern.finditer(text):
            candidates.append(match.group(1).strip())

        # Extract balanced JSON objects from noisy text.
        starts = [i for i, ch in enumerate(text) if ch == "{"]
        for start in starts:
            depth = 0
            for idx in range(start, len(text)):
                ch = text[idx]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidates.append(text[start : idx + 1].strip())
                        break

        # Preserve order while removing duplicates.
        seen: set[str] = set()
        deduped: list[str] = []
        for item in candidates:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return deduped

    def _parse_agent_output(self, text: str) -> tuple[str, list[dict[str, Any]], str]:
        logger.info(f"Parsing agent output ({len(text)} chars): {text[:200]}...")

        candidates = self._extract_json_candidates(text)
        logger.info(f"Found {len(candidates)} JSON candidates")

        for idx, candidate in enumerate(candidates):
            logger.debug(f"Trying candidate {idx}: {candidate[:100]}...")
            try:
                payload = json.loads(candidate)
                logger.info(f"✓ JSON parsed successfully from candidate {idx}")
            except json.JSONDecodeError as e:
                logger.debug(f"✗ JSON parse failed for candidate {idx}: {e}")
                continue

            if not isinstance(payload, dict):
                logger.warning(f"Candidate {idx} is not a dict: {type(payload)}")
                continue

            if "actions" not in payload and "reply" not in payload:
                logger.warning(f"Candidate {idx} missing required keys (actions or reply)")
                continue

            reply = str(payload.get("reply", "")).strip()
            actions = self._sanitize_actions(payload.get("actions", []))
            logger.info(f"✓ Agent output: reply={len(reply)} chars, actions={len(actions)} items")
            for i, action in enumerate(actions):
                logger.info(f"  Action {i}: {action.get('type')} on {action.get('path')}")
            return (reply or text, actions, "ok")

        logger.warning(f"No valid JSON found in agent output")
        return (text, [], "no_json")

    def ask(
        self,
        user_prompt: str,
        mode: str,
        attached_files: dict[str, str],
        progress_callback: Callable[[str], None] | None = None,
        token_callback: Callable[[str], None] | None = None,
        workspace_root: Path | None = None,
    ) -> ChatResult:
        started = time.perf_counter()
        if progress_callback is not None:
            progress_callback("Preparing model...")
        self.load_if_needed(progress_callback=progress_callback)

        # Get device and log it
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if progress_callback is not None:
            device_name = "GPU (CUDA)" if device.type == "cuda" else "CPU"
            progress_callback(f"Using device: {device_name}")

        if progress_callback is not None:
            progress_callback("Building prompt and chat template...")

        messages = self._build_messages(user_prompt=user_prompt, mode=mode, attached_files=attached_files, workspace_root=workspace_root)

        # Try to use chat template, fallback to manual formatting if not available
        try:
            inputs = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            ).to(device)
        except ValueError as e:
            if "chat_template" in str(e):
                logger.warning(f"Chat template not available: {str(e)}, using manual formatting...")
                if progress_callback is not None:
                    progress_callback("Chat template not found - using manual formatting...")

                # Manual formatting fallback
                prompt_text = ""
                for msg in messages:
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    if role == "system":
                        prompt_text += f"System: {content}\n\n"
                    elif role == "user":
                        prompt_text += f"User: {content}\n"
                    elif role == "assistant":
                        prompt_text += f"Assistant: {content}\n"

                prompt_text += "Assistant: "
                inputs = self.tokenizer(prompt_text, return_tensors="pt", return_dict=True).to(device)
            else:
                raise

        # Log input token statistics
        input_tokens = inputs["input_ids"].shape[-1]
        if progress_callback is not None:
            progress_callback(f"Generating response tokens... (input: {input_tokens} tokens)")

        # Use streaming for real-time token output
        streamer = TextIteratorStreamer(self.tokenizer, skip_special_tokens=True)

        full_text = ""
        start_gen = time.perf_counter()

        try:
            with torch.inference_mode():
                # Different generation params for agent vs assistant
                if mode == "agent":
                    # Agent: use greedy decoding for precise JSON output
                    generation_kwargs = {
                        "input_ids": inputs["input_ids"],
                        "attention_mask": inputs.get("attention_mask"),
                        "max_new_tokens": 2048,
                        "streamer": streamer,
                        "do_sample": False,  # Greedy decoding for consistency
                        "use_cache": True,
                    }
                else:
                    # Assistant: use sampling for variety
                    generation_kwargs = {
                        "input_ids": inputs["input_ids"],
                        "attention_mask": inputs.get("attention_mask"),
                        "max_new_tokens": 2048,
                        "streamer": streamer,
                        "do_sample": True,
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "use_cache": True,
                    }

                # Remove None values
                generation_kwargs = {k: v for k, v in generation_kwargs.items() if v is not None}

                thread = threading.Thread(
                    target=self.model.generate,
                    kwargs=generation_kwargs,
                )
                thread.daemon = True
                thread.start()

                # Collect tokens from streamer
                token_count = 0
                for text in streamer:
                    if text:  # Only process non-empty tokens
                        full_text += text
                        token_count += 1

                        # In agent mode: emit tokens only if they're before JSON
                        # After JSON parsing, we'll emit the reply part separately
                        if mode == "agent":
                            # Don't emit raw JSON, it will be parsed and reply extracted
                            if "{" not in full_text or token_callback is None:
                                # Haven't hit JSON yet, safe to stream
                                if "{" not in text:
                                    if token_callback is not None:
                                        token_callback(text)
                        else:
                            # Assistant mode: stream everything
                            if token_callback is not None:
                                token_callback(text)

                thread.join(timeout=300)  # Wait max 5 minutes

        except Exception as e:
            if progress_callback is not None:
                progress_callback(f"Generation error: {str(e)}")
            raise

        gen_time = time.perf_counter() - start_gen
        tokens_per_sec = token_count / max(gen_time, 0.1) if gen_time > 0 else 0

        if progress_callback is not None:
            progress_callback(
                f"Generated {token_count} tokens in {gen_time:.2f}s ({tokens_per_sec:.1f} tok/s)"
            )

        text = full_text.strip()

        elapsed = time.perf_counter() - started

        if mode != "agent":
            if progress_callback is not None:
                progress_callback(f"Done in {elapsed:.1f}s")
            return ChatResult(text=text, actions=[])

        if progress_callback is not None:
            progress_callback("Parsing agent JSON actions...")

        reply, actions, parse_status = self._parse_agent_output(text)

        # Stream the reply part to token_callback (if in agent mode)
        if reply and token_callback is not None:
            # Emit the reply text in chunks for smooth streaming
            for char in reply:
                token_callback(char)

        if progress_callback is not None:
            if parse_status == "no_json":
                progress_callback("Agent response had no valid JSON actions.")
            elif not actions:
                progress_callback("Agent JSON parsed, but actions list is empty.")
            progress_callback(f"Done in {elapsed:.1f}s")

        return ChatResult(text=reply, actions=actions)


class ChatWorker(QThread):
    finished_ok = Signal(object)
    failed = Signal(str)
    progress = Signal(str)
    token_received = Signal(str)  # New signal for token streaming

    def __init__(
        self,
        llm_service: LlmService,
        prompt: str,
        mode: str,
        attached_files: dict[str, str],
        workspace_root: Path | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._llm_service = llm_service
        self._prompt = prompt
        self._mode = mode
        self._attached_files = attached_files
        self._workspace_root = workspace_root

    def run(self) -> None:
        try:
            logger.info(f"ChatWorker started: mode={self._mode}, prompt_len={len(self._prompt)}")
            result = self._llm_service.ask(
                user_prompt=self._prompt,
                mode=self._mode,
                attached_files=self._attached_files,
                progress_callback=self.progress.emit,
                token_callback=self.token_received.emit,
                workspace_root=self._workspace_root,
            )
            logger.info("ChatWorker completed successfully")
            self.finished_ok.emit(result)
        except Exception as exc:
            logger.error(f"ChatWorker failed with exception: {str(exc)}", exc_info=True)
            self.failed.emit(str(exc))
