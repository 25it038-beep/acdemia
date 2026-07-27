import json
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)


def _make_client(api_key: Optional[str], base_url: str = None):
    if not api_key:
        return None
    import openai
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return openai.AsyncOpenAI(**kwargs)


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

    def _init_clients(self):
        if self.provider == "nvidia":
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
                        if chunk.choices[0].delta.content:
                            yield json.dumps({
                                "role": "assistant",
                                "content": chunk.choices[0].delta.content
                            })
                else:
                    yield json.dumps({
                        "role": "assistant",
                        "content": response.choices[0].message.content
                    })
        except Exception as e:
            logger.error(f"AI chat error ({model}): {e}")
            yield json.dumps({
                "role": "assistant",
                "content": f"I encountered an error: {str(e)}. Please check your API configuration."
            })

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        client = self._get_client("embed")
        if client is None:
            return [[0.0] * settings.EMBEDDING_DIMENSION for _ in texts]
        try:
            response = await client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return [[0.0] * settings.EMBEDDING_DIMENSION for _ in texts]

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
        async for chunk in self.chat(messages, temperature=0.3, max_tokens=max_length * 2, task="chat"):
            data = json.loads(chunk)
            result += data.get("content", "")
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
            return []
        except json.JSONDecodeError:
            logger.error(f"Failed to parse questions: {result[:200]}")
            return []


ai_provider = AIProvider()