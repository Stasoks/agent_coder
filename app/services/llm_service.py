from __future__ import annotations

import gc
import json
import queue
import re
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Any

import torch
from PySide6.QtCore import QObject, QThread, Signal
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer, BitsAndBytesConfig

from app.core.settings import DEFAULT_MODEL


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
    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self.model_name = model_name
        self.tokenizer = None
        self.model = None

    def load_if_needed(self, progress_callback: Callable[[str], None] | None = None) -> None:
        if self.model is not None and self.tokenizer is not None:
            if progress_callback is not None:
                progress_callback("Model is already loaded.")
            return

        # Clear GPU memory before loading
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()

        if progress_callback is not None:
            progress_callback(f"Loading tokenizer: {self.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        use_cuda = torch.cuda.is_available()

        if use_cuda:
            # Log GPU info
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            if progress_callback is not None:
                progress_callback(f"GPU found: {gpu_name} ({gpu_memory:.1f}GB)")
            # Enable TF32 on supported GPUs for faster matrix math with minimal quality impact.
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True

        dtype = torch.float16 if use_cuda else torch.float32
        device_note = "CUDA" if use_cuda else "CPU"
        if progress_callback is not None:
            progress_callback(f"Loading model weights: {self.model_name} ({device_note}) with 4-BIT quantization")

        # Load model with 4-BIT quantization (extreme compression)
        if use_cuda:
            # 4-bit NFT quantization - максимальное сжатие
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )
            try:
                if progress_callback is not None:
                    progress_callback("[Stage 1/3] Applying 4-BIT NF4 quantization config...")

                if progress_callback is not None:
                    progress_callback("[Stage 2/3] Loading model with extreme compression...")

                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    quantization_config=quantization_config,
                    device_map="auto",
                    low_cpu_mem_usage=True,
                )

                if progress_callback is not None:
                    progress_callback("[Stage 3/3] 4-BIT quantization applied successfully!")

            except RuntimeError as e:
                if progress_callback is not None:
                    progress_callback(f"[ERROR] 4-bit failed: {str(e)[:60]}... Trying 8-bit INT8...")

                torch.cuda.empty_cache()
                gc.collect()

                # Fallback to 8-bit
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                    bnb_8bit_use_double_quant=True,
                    bnb_8bit_compute_dtype=torch.float16,
                )

                try:
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        quantization_config=quantization_config,
                        device_map="auto",
                        low_cpu_mem_usage=True,
                    )
                    if progress_callback is not None:
                        progress_callback("[Fallback] 8-BIT INT8 quantization applied")
                except:
                    if progress_callback is not None:
                        progress_callback("[Last Resort] Loading in float16 without quantization...")

                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float16,
                        device_map="auto",
                        low_cpu_mem_usage=True,
                    )
                    if progress_callback is not None:
                        progress_callback("[WARNING] No quantization applied - float16 mode")

            except Exception as e:
                if progress_callback is not None:
                    progress_callback(f"[CRITICAL] {str(e)[:100]}")
                raise
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=dtype,
                device_map="cpu",
                low_cpu_mem_usage=True,
            )

        # Ensure model is in eval mode
        self.model.eval()

        if progress_callback is not None:
            progress_callback("Model loaded and ready.")

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
    ) -> list[dict[str, str]]:
        if mode == "agent":
            system = (
                "You are a coding agent inside a Lua IDE. "
                "When file operations are needed, return strict JSON with keys: "
                "reply (string), actions (array). "
                "Each action item supports type=write_file with fields path and content, "
                "type=append_file with path and content, "
                "type=replace_in_file with path, old_text, new_text. "
                "If no file operation needed, actions must be an empty array. "
                "Do not include markdown fences around JSON. "
                "Return only one JSON object. "
                "Example: {\"reply\": \"Done\", \"actions\": [{\"type\": \"write_file\", \"path\": \"main.lua\", \"content\": \"print('hi')\"}]}"
            )
        else:
            system = (
                "You are a helpful assistant for Lua development. "
                "Explain clearly, propose robust code, and keep responses concise."
            )

        files_block = ""
        if attached_files:
            chunks = []
            for p, content in attached_files.items():
                chunks.append(f"FILE: {p}\n{content}\n")
            files_block = "\nAttached files:\n" + "\n".join(chunks)

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt + files_block},
        ]

    def _sanitize_actions(self, raw_actions: Any) -> list[dict[str, Any]]:
        if not isinstance(raw_actions, list):
            return []

        allowed = {"write_file", "append_file", "replace_in_file"}
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
        for candidate in self._extract_json_candidates(text):
            try:
                payload = json.loads(candidate)
            except Exception:
                continue

            if not isinstance(payload, dict):
                continue

            if "actions" not in payload and "reply" not in payload:
                continue

            reply = str(payload.get("reply", "")).strip()
            actions = self._sanitize_actions(payload.get("actions", []))
            return (reply or text, actions, "ok")

        return (text, [], "no_json")

    def ask(
        self,
        user_prompt: str,
        mode: str,
        attached_files: dict[str, str],
        progress_callback: Callable[[str], None] | None = None,
        token_callback: Callable[[str], None] | None = None,
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

        messages = self._build_messages(user_prompt=user_prompt, mode=mode, attached_files=attached_files)
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(device)

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
                # Run generation in a thread to allow streaming
                generation_kwargs = {
                    "input_ids": inputs["input_ids"],
                    "attention_mask": inputs.get("attention_mask"),
                    "max_new_tokens": 1024,
                    "streamer": streamer,
                    "do_sample": True,  # Enable sampling for faster generation
                    "temperature": 0.7,  # Slightly random for variety
                    "top_p": 0.95,  # Nucleus sampling
                    "use_cache": True,  # Cache for faster generation
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
                in_json_mode = False
                for text in streamer:
                    if text:  # Only process non-empty tokens
                        full_text += text
                        token_count += 1

                        # For agent mode, detect when we enter JSON (first {)
                        if mode == "agent" and "{" in text and not in_json_mode:
                            in_json_mode = True

                        # Emit token to UI
                        if token_callback is not None:
                            if mode == "assistant" or (mode == "agent" and not in_json_mode):
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
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._llm_service = llm_service
        self._prompt = prompt
        self._mode = mode
        self._attached_files = attached_files

    def run(self) -> None:
        try:
            result = self._llm_service.ask(
                user_prompt=self._prompt,
                mode=self._mode,
                attached_files=self._attached_files,
                progress_callback=self.progress.emit,
                token_callback=self.token_received.emit,
            )
            self.finished_ok.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))
