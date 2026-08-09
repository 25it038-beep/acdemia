import json
import logging
import re
import time
from typing import Optional, List, Dict, Any, AsyncGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)

THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

# Default per-task models for backup providers (used when the primary fails)
FALLBACK_MODELS: Dict[str, Dict[str, str]] = {
    "cloudflare": {
        "chat": "@cf/qwen/qwen3-30b-a3b-fp8",
        "stem": "@cf/qwen/qwen3-30b-a3b-fp8",
        "coding": "@cf/qwen/qwen2.5-coder-32b-instruct",
        "vision": "@cf/meta/llama-3.2-11b-vision-instruct",
        "embed": "@cf/qwen/qwen3-embedding-0.6b",
    },
    "nvidia": {
        "chat": "meta/llama-3.3-70b-instruct",
        "stem": "deepseek-ai/deepseek-r1",
        "coding": "meta/llama-3.3-70b-instruct",
        "vision": "meta/llama-3.3-70b-instruct",
        "embed": "nvidia/embed-qa-4",
    },
    "openrouter": {
        "chat": "meta-llama/llama-3.3-70b-instruct:free",
        "stem": "meta-llama/llama-3.3-70b-instruct:free",
        "coding": "qwen/qwen-2.5-coder-32b-instruct:free",
        "vision": "meta-llama/llama-3.3-70b-instruct:free",
    },
    "openai": {
        "chat": "gpt-4o-mini",
        "stem": "gpt-4o-mini",
        "coding": "gpt-4o-mini",
        "vision": "gpt-4o-mini",
    },
    "gemini": {
        "chat": "gemini-2.0-flash",
        "stem": "gemini-2.0-flash",
        "coding": "gemini-2.0-flash",
        "vision": "gemini-2.0-flash",
    },
}

# Fallback order after the configured primary provider
FALLBACK_ORDER = ["groq", "nvidia", "openrouter", "openai", "cloudflare", "gemini"]

# Cooldown (seconds) before retrying a provider that failed
PROVIDER_COOLDOWN = 300


def _strip_think(text: str) -> str:
    """Remove reasoning blocks some Groq models wrap their answers in."""
    if not text:
        return text
    stripped = THINK_BLOCK_RE.sub("", text).strip()
    if "<think" in stripped:
        # Block was truncated (no closing tag) — keep whatever follows the opening tag
        idx = stripped.find("<think")
        return stripped[idx + len("<think"):].strip()
    return stripped


class EmptyResponseError(Exception):
    """Raised when a provider returns success but no usable content."""


def _make_client(api_key: Optional[str], base_url: str = None):
    if not api_key:
        return None
    import openai
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return openai.AsyncOpenAI(**kwargs)


def _normalize_content(content) -> str:
    """Workers AI may return content as a list of parts; flatten to text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        if content and all(isinstance(p, dict) for p in content):
            if any("text" in p for p in content):
                parts = []
                for p in content:
                    text = p.get("text")
                    if text is not None:
                        parts.append(text if isinstance(text, str) else str(text))
                return "".join(parts)
            return json.dumps(content)
        return "".join(str(p) for p in content)
    return str(content)


class AIProvider:
    """Unified AI provider with automatic fallback across configured providers.

    The provider named by ``AI_PROVIDER`` is tried first; if it errors (quota,
    outage, ...), the request is retried with the next configured provider.
    """

    def __init__(self):
        self.provider = settings.AI_PROVIDER

        # Ordered list of usable providers: {name, client, models}
        self._providers: List[Dict[str, Any]] = []
        # Provider name -> timestamp until which it is skipped after a failure
        self._dead_providers: Dict[str, float] = {}

        self._init_providers()

    def _cloudflare_base_url(self) -> Optional[str]:
        """OpenAI-compatible base URL for Cloudflare Workers AI."""
        if not settings.CLOUDFLARE_ACCOUNT_ID:
            return None
        return (
            settings.CLOUDFLARE_BASE_URL
            or f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/ai/v1"
        )

    def _provider_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Build the client + model table for one provider, or None if unconfigured."""
        if name == "groq":
            if not settings.GROQ_API_KEY:
                return None
            client = _make_client(settings.GROQ_API_KEY, settings.GROQ_BASE_URL)
            models = {
                "chat": settings.CHAT_MODEL,
                "stem": settings.STEM_MODEL,
                "coding": settings.CODING_MODEL,
                "vision": settings.VISION_MODEL,
                "embed": settings.EMBEDDING_MODEL,
            }
        elif name == "cloudflare":
            cf_base = self._cloudflare_base_url()
            if not settings.CLOUDFLARE_API_KEY or not cf_base:
                return None
            client = _make_client(settings.CLOUDFLARE_API_KEY, cf_base)
            models = dict(FALLBACK_MODELS["cloudflare"])
        elif name == "nvidia":
            if not (settings.NVIDIA_API_KEY or settings.NVIDIA_CODING_API_KEY
                    or settings.NVIDIA_VISION_API_KEY):
                return None
            client = _make_client(
                settings.NVIDIA_API_KEY
                or settings.NVIDIA_CODING_API_KEY
                or settings.NVIDIA_VISION_API_KEY,
                settings.NVIDIA_BASE_URL,
            )
            models = dict(FALLBACK_MODELS["nvidia"])
        elif name == "openrouter":
            if not settings.OPENROUTER_API_KEY:
                return None
            client = _make_client(settings.OPENROUTER_API_KEY, "https://openrouter.ai/api/v1")
            models = dict(FALLBACK_MODELS["openrouter"])
        elif name == "openai":
            if not settings.OPENAI_API_KEY:
                return None
            client = _make_client(settings.OPENAI_API_KEY)
            models = dict(FALLBACK_MODELS["openai"])
        elif name == "gemini":
            if not settings.GEMINI_API_KEY:
                return None
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            client = None  # handled via genai SDK
            models = dict(FALLBACK_MODELS["gemini"])
        else:
            return None
        return {"name": name, "client": client, "models": models}

    def _init_providers(self):
        providers = []
        seen = set()
        for name in [settings.AI_PROVIDER, *FALLBACK_ORDER]:
            if name in seen:
                continue
            seen.add(name)
            cfg = self._provider_config(name)
            if cfg:
                providers.append(cfg)
        self._providers = providers
        if not providers:
            logger.warning("No AI API keys configured. AI features will be unavailable.")

    def _live_providers(self) -> List[Dict[str, Any]]:
        now = time.time()
        return [
            p for p in self._providers
            if p["name"] not in self._dead_providers or self._dead_providers[p["name"]] <= now
        ]

    def _mark_dead(self, name: str):
        logger.error(f"AI provider '{name}' failed — cooling down for {PROVIDER_COOLDOWN}s")
        self._dead_providers[name] = time.time() + PROVIDER_COOLDOWN

    def _get_client(self, task: str = "chat"):
        for provider in self._providers:
            if provider["name"] == settings.AI_PROVIDER:
                return provider["client"]
        return self._providers[0]["client"] if self._providers else None

    def _get_model(self, task: str = "chat"):
        for provider in self._providers:
            if provider["name"] == settings.AI_PROVIDER:
                return provider["models"].get(task) or provider["models"]["chat"]
        if not self._providers:
            return settings.CHAT_MODEL
        return self._providers[0]["models"].get(task) or self._providers[0]["models"]["chat"]

    async def _chat_provider(
        self,
        provider: Dict[str, Any],
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        stream: bool,
        task: str,
    ) -> AsyncGenerator[str, None]:
        client = provider["client"]
        model = provider["models"].get(task) or provider["models"]["chat"]

        if provider["name"] == "gemini":
            import google.generativeai as genai
            genai_model = genai.GenerativeModel(model)
            chat_session = genai_model.start_chat()
            response = await chat_session.send_message_async(messages[-1]["content"])
            yield json.dumps({
                "role": "assistant",
                "content": _strip_think(_normalize_content(response.text)),
            })
            return

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )
        if stream:
            saw_content = False
            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    saw_content = True
                    yield json.dumps({
                        "role": "assistant",
                        "content": _strip_think(_normalize_content(content)),
                    })
            if not saw_content:
                raise EmptyResponseError(
                    f"stream ended without content (model {model})"
                )
        else:
            content = _strip_think(_normalize_content(response.choices[0].message.content))
            if not content:
                raise EmptyResponseError(
                    f"empty response (model {model}, finish_reason={response.choices[0].finish_reason})"
                )
            yield json.dumps({"role": "assistant", "content": content})

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
        task: str = "chat",
    ) -> AsyncGenerator[str, None]:
        providers = self._live_providers()
        if not providers:
            yield json.dumps({
                "role": "assistant",
                "content": "I'm running in offline mode. Please configure an AI provider API key to enable AI features."
            })
            return

        errors = []
        for provider in providers:
            try:
                async for chunk in self._chat_provider(
                    provider, messages, temperature, max_tokens, stream, task
                ):
                    yield chunk
                return  # stream finished without error
            except Exception as e:
                errors.append(f"{provider['name']}: {e}")
                logger.error(f"AI chat error ({provider['name']} / "
                             f"{provider['models'].get(task, 'chat')}): {e}")
                self._mark_dead(provider["name"])

        yield json.dumps({
            "role": "assistant",
            "content": f"All AI providers failed: {'; '.join(errors)}"
        })

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        dim = settings.EMBEDDING_DIMENSION
        if getattr(self, "_embeddings_failed", False):
            return [[0.0] * dim for _ in texts]
        import asyncio as _asyncio

        for provider in self._live_providers():
            embed_model = provider["models"].get("embed")
            client = provider["client"]
            if not embed_model or client is None:
                continue
            try:
                batches = [texts[i:i + 128] for i in range(0, len(texts), 128)]
                results = await _asyncio.gather(*[
                    client.embeddings.create(model=embed_model, input=batch)
                    for batch in batches
                ])
                vectors = []
                for res in results:
                    vectors.extend(item.embedding for item in res.data)
                return vectors
            except Exception as e:
                logger.error(f"Embedding error ({provider['name']} / {embed_model}): {e}")
                self._mark_dead(provider["name"])
        # Every configured provider failed — short-circuit all future calls
        self._embeddings_failed = True
        return [[0.0] * dim for _ in texts]

    async def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        text = ""
        try:
            if file_type == "pdf":
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            elif file_type in ("docx", "doc"):
                from docx import Document
                doc = Document(file_path)
                text = "\n".join(p.text for p in doc.paragraphs)
            elif file_type in ("pptx", "ppt"):
                from pptx import Presentation
                prs = Presentation(file_path)
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if shape.has_text_frame:
                            text += shape.text + "\n"
            elif file_type in ("xlsx", "xls"):
                import openpyxl
                wb = openpyxl.load_workbook(file_path, data_only=True)
                for sheet in wb.sheetnames:
                    ws = wb[sheet]
                    for row in ws.iter_rows(values_only=True):
                        text += " | ".join(str(cell) if cell else "" for cell in row) + "\n"
            elif file_type == "csv":
                import csv
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    text = "\n".join(" | ".join(row) for row in reader)
            elif file_type in ("txt", "md"):
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            elif file_type in ("png", "jpg", "jpeg", "gif", "bmp", "webp"):
                text = "[Image file — no text content extracted]"
            elif file_type in ("mp4", "avi", "mov", "mkv", "webm"):
                text = "[Video file — no text content extracted]"
            elif file_type in ("mp3", "wav", "ogg", "m4a", "flac"):
                text = "[Audio file — no text content extracted]"
            elif file_type == "html":
                from bs4 import BeautifulSoup
                with open(file_path, "r", encoding="utf-8") as f:
                    soup = BeautifulSoup(f.read(), "lxml")
                    text = soup.get_text(separator="\n")
            elif file_type == "epub":
                import ebooklib
                from ebooklib import epub
                from bs4 import BeautifulSoup
                book = epub.read_epub(file_path)
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        soup = BeautifulSoup(item.get_content(), "lxml")
                        text += soup.get_text() + "\n"
            else:
                text = "Unsupported file type for text extraction."
        except Exception as e:
            logger.error(f"Text extraction error for {file_type}: {e}")
            text = f"Error extracting text: {str(e)}"
        return text

    async def generate_summary(self, content: str, summary_type: str = "short_notes", max_length: int = 500) -> Dict[str, Any]:
        prompts = {
            "short_notes": "Generate concise short notes from the following content. Include key points, definitions, and important concepts.",
            "cheat_sheet": "Create a one-page cheat sheet covering the essential formulas, concepts, and key points.",
            "flashcards": "Generate flashcards in Q&A format from the content.",
            "mind_map": "Create a hierarchical mind map structure from the content.",
            "formula_sheet": "Extract all formulas, equations, and mathematical expressions.",
            "revision_notes": "Create comprehensive revision notes organized by topics and subtopics.",
            "important_questions": "Generate a list of important exam questions based on the content.",
            "one_page_summary": "Summarize the entire content into a single page.",
        }
        prompt = prompts.get(summary_type, prompts["short_notes"])
        messages = [
            {"role": "system", "content": f"You are an expert educator and summarizer. {prompt} Format the output in markdown. Keep it under {max_length} words."},
            {"role": "user", "content": f"Content to summarize:\n\n{content[:10000]}"},
        ]
        result = ""
        # qwen reasoning models spend tokens on thinking — give a generous budget and retry once if truncated
        for _ in range(2):
            result = ""
            async for chunk in self.chat(messages, temperature=0.3, max_tokens=max(2048, max_length * 4), task="chat"):
                data = json.loads(chunk)
                result += data.get("content", "")
            if result.strip():
                break
        return {
            "title": summary_type.replace("_", " ").title(),
            "content": result,
            "summary_type": summary_type,
            "format": "markdown",
        }

    async def generate_questions(
        self, content: str, question_type: str = "mcq", count: int = 10, difficulty: str = "medium"
    ) -> List[Dict[str, Any]]:
        prompt = f"""
Generate {count} {question_type} questions at {difficulty} difficulty based on the content.
For each question provide:
- question_text
- question_type
- options (array of choices for MCQ)
- correct_answer
- explanation
- difficulty (1-5)
- marks

Format as JSON array.
"""
        messages = [
            {"role": "system", "content": "You are an expert exam question generator. Always respond with valid JSON only."},
            {"role": "user", "content": f"{prompt}\n\nContent:\n{content[:8000]}"},
        ]
        result = ""
        # Use STEM model for question generation (stronger reasoning)
        async for chunk in self.chat(messages, temperature=0.4, task="stem"):
            data = json.loads(chunk)
            result += data.get("content", "")
        try:
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()
            questions = json.loads(result)
            if isinstance(questions, list):
                return questions[:count]
            if isinstance(questions, dict):
                return [questions]
            return []
        except json.JSONDecodeError:
            # Last resort: extract the first JSON array in the response
            try:
                start, end = result.index("["), result.rindex("]")
                questions = json.loads(result[start:end + 1])
                return questions if isinstance(questions, list) else []
            except (ValueError, json.JSONDecodeError):
                logger.error(f"Failed to parse questions: {result[:200]}")
                return []


ai_provider = AIProvider()