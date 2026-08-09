import json
import logging
import re
from typing import Optional, List, Dict, Any, AsyncGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)

THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _strip_think(text: str) -> str:
    """Remove reasoning blocks some Groq models wrap their answers in."""
    if not text:
        return text
    stripped = THINK_BLOCK_RE.sub("", text).strip()
    if "<think" in stripped:
        # Block was truncated (no closing tag) — the final answer is lost anyway
        return ""
    return stripped


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
    """Unified AI provider with per-task model selection on NVIDIA NIM."""

    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.base_url = settings.NVIDIA_BASE_URL

        # Per-task clients
        self._chat_client = None
        self._coding_client = None
        self._vision_client = None
        self._embed_client = None

        self._init_clients()

    def _cloudflare_base_url(self) -> Optional[str]:
        """OpenAI-compatible base URL for Cloudflare Workers AI."""
        if not settings.CLOUDFLARE_ACCOUNT_ID:
            return None
        return (
            settings.CLOUDFLARE_BASE_URL
            or f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/ai/v1"
        )

    def _init_clients(self):
        if self.provider == "groq":
            client = _make_client(settings.GROQ_API_KEY, settings.GROQ_BASE_URL)
            self._chat_client = client
            self._coding_client = client
            self._vision_client = client
            self._embed_client = client
            if client is None:
                logger.warning("Groq provider selected but GROQ_API_KEY missing.")
        elif self.provider == "cloudflare":
            cf_base = self._cloudflare_base_url()
            client = _make_client(settings.CLOUDFLARE_API_KEY, cf_base) if cf_base else None
            self._chat_client = client
            self._coding_client = client
            self._vision_client = client
            self._embed_client = client
            if client is None:
                logger.warning("Cloudflare provider selected but API key or account ID missing.")
        elif self.provider == "nvidia":
            self._chat_client = _make_client(settings.NVIDIA_API_KEY, self.base_url)
            self._coding_client = _make_client(
                settings.NVIDIA_CODING_API_KEY or settings.NVIDIA_API_KEY,
                self.base_url,
            )
            self._vision_client = _make_client(
                settings.NVIDIA_VISION_API_KEY or settings.NVIDIA_API_KEY,
                self.base_url,
            )
            self._embed_client = _make_client(
                settings.NVIDIA_EMBED_API_KEY or settings.NVIDIA_API_KEY,
                self.base_url,
            )
        elif self.provider == "openrouter" and settings.OPENROUTER_API_KEY:
            client = _make_client(settings.OPENROUTER_API_KEY, "https://openrouter.ai/api/v1")
            self._chat_client = client
            self._coding_client = client
            self._vision_client = client
            self._embed_client = client
        elif self.provider == "openai" and settings.OPENAI_API_KEY:
            client = _make_client(settings.OPENAI_API_KEY)
            self._chat_client = client
            self._coding_client = client
            self._vision_client = client
            self._embed_client = client
        elif self.provider == "gemini" and settings.GEMINI_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._gemini_configured = True
        else:
            logger.warning("No AI API keys configured. Using mock responses.")

    def _get_client(self, task: str = "chat"):
        mapping = {
            "chat": self._chat_client,
            "coding": self._coding_client,
            "vision": self._vision_client,
            "embed": self._embed_client,
        }
        return mapping.get(task, self._chat_client)

    def _get_model(self, task: str = "chat"):
        mapping = {
            "chat": settings.CHAT_MODEL,
            "stem": settings.STEM_MODEL,
            "coding": settings.CODING_MODEL,
            "vision": settings.VISION_MODEL,
        }
        return mapping.get(task, settings.CHAT_MODEL)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
        task: str = "chat",
    ) -> AsyncGenerator[str, None]:
        client = self._get_client(task)
        model = self._get_model(task)

        if client is None:
            yield json.dumps({
                "role": "assistant",
                "content": "I'm running in offline mode. Please configure an AI provider API key to enable AI features."
            })
            return

        try:
            if self.provider == "gemini":
                import google.generativeai as genai
                genai_model = genai.GenerativeModel(model)
                chat_session = genai_model.start_chat()
                response = await chat_session.send_message_async(messages[-1]["content"])
                yield json.dumps({"role": "assistant", "content": response.text})
            else:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                )
                if stream:
                    async for chunk in response:
                        content = chunk.choices[0].delta.content
                        if content:
                            yield json.dumps({
                                "role": "assistant",
                                "content": _strip_think(_normalize_content(content)),
                            })
                else:
                    yield json.dumps({
                        "role": "assistant",
                        "content": _strip_think(_normalize_content(response.choices[0].message.content)),
                    })
        except Exception as e:
            logger.error(f"AI chat error ({model}): {e}")
            yield json.dumps({
                "role": "assistant",
                "content": f"I encountered an error: {str(e)}. Please check your API configuration."
            })

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        client = self._get_client("embed")
        dim = settings.EMBEDDING_DIMENSION
        if client is None or getattr(self, "_embeddings_failed", False):
            return [[0.0] * dim for _ in texts]
        try:
            import asyncio as _asyncio
            batches = [texts[i:i + 128] for i in range(0, len(texts), 128)]
            results = await _asyncio.gather(*[
                client.embeddings.create(model=settings.EMBEDDING_MODEL, input=batch)
                for batch in batches
            ])
            vectors = []
            for res in results:
                vectors.extend(item.embedding for item in res.data)
            return vectors
        except Exception as e:
            # One failure means the provider has no embeddings support — stop
            # hammering it and short-circuit all future calls.
            logger.error(f"Embedding error ({settings.EMBEDDING_MODEL}): {e}")
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