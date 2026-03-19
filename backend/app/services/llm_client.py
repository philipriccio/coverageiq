"""OpenAI GPT-4.1 primary client with Claude fallback support."""
import json
import os
from typing import Any, Dict, List, Optional

import httpx


class LLMError(Exception):
    pass


class LLMRateLimitError(LLMError):
    pass


class LLMContentModerationError(LLMError):
    pass


class OpenAIClient:
    MODEL_GPT_4_1 = "gpt-4.1"
    FALLBACK_MODEL = "gpt-4-turbo"
    DEFAULT_MODEL = MODEL_GPT_4_1
    DEFAULT_TEMPERATURE = 0.3
    DEFAULT_MAX_TOKENS = 8000

    def __init__(self, api_key: Optional[str] = None, timeout: float = 120.0):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise LLMError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        self.timeout = timeout
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise LLMError("OpenAI SDK not installed. Run: pip install openai>=1.0.0") from exc
        self._client = AsyncOpenAI(api_key=self.api_key, timeout=timeout)

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        response_format: Optional[Dict[str, str]] = None,
        stream: bool = False,
        timeout_override: Optional[float] = None,
    ) -> Dict[str, Any]:
        del stream
        try:
            kwargs: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format and response_format.get("type") == "json_object":
                kwargs["response_format"] = {"type": "json_object"}
            if timeout_override:
                kwargs["timeout"] = timeout_override
            response = await self._client.chat.completions.create(**kwargs)
            return response.model_dump()
        except Exception as exc:
            message = str(exc).lower()
            if "rate limit" in message or "429" in message:
                raise LLMRateLimitError(str(exc)) from exc
            if "401" in message or "api key" in message:
                raise LLMError(f"Invalid OpenAI API key: {exc}") from exc
            raise LLMError(f"OpenAI request failed: {exc}") from exc

    async def analyze_script(
        self,
        script_text: str,
        prompt: str,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        expect_json: bool = True,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        full_content = f"""{prompt}

---

SCRIPT CONTENT:

{script_text}

---

Provide your analysis based on the instructions above."""

        messages = [
            {"role": "system", "content": "You are an expert script coverage analyst with 20+ years of experience reading screenplays and TV pilots for major studios and production companies. You provide professional, objective, and constructive coverage."},
            {"role": "user", "content": full_content},
        ]
        result = await self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens or self.DEFAULT_MAX_TOKENS,
            response_format={"type": "json_object"} if expect_json else None,
        )
        content = result["choices"][0]["message"]["content"]
        if expect_json:
            try:
                return json.loads(content)
            except json.JSONDecodeError as exc:
                raise LLMError(f"Failed to parse OpenAI JSON response: {exc}\nPreview: {content[:500]}") from exc
        return {"content": content}

    async def analyze_with_chunking(
        self,
        script_text: str,
        prompt: str,
        chunk_size: int = 60000,
        overlap: int = 5000,
        model: str = DEFAULT_MODEL,
    ) -> Dict[str, Any]:
        chunks = []
        start = 0
        while start < len(script_text):
            end = start + chunk_size
            if end < len(script_text):
                newline_pos = script_text.rfind("\n", end - 100, end + 100)
                if newline_pos != -1:
                    end = newline_pos
            chunks.append(script_text[start:end])
            start = end - overlap

        if len(chunks) == 1:
            return await self.analyze_script(chunks[0], prompt, model)

        chunk_results = []
        for i, chunk in enumerate(chunks):
            chunk_prompt = f"{prompt}\n\nNote: This is chunk {i + 1} of {len(chunks)} of the script."
            chunk_results.append(await self.analyze_script(chunk, chunk_prompt, model))

        synthesis_prompt = f"""You have received analysis of a TV pilot script that was split into {len(chunks)} parts.

Synthesize these partial analyses into a single coherent coverage report.

Partial analyses:
{json.dumps(chunk_results, indent=2)}

Provide the final coverage report in the same JSON format as the individual analyses."""
        return await self.analyze_script("SYNTHESIS TASK - See prompt for partial analyses", synthesis_prompt, model, temperature=0.2)


class ClaudeClient:
    MODEL_CLAUDE_SONNET = "claude-sonnet-4-5"
    DEFAULT_MODEL = MODEL_CLAUDE_SONNET
    DEFAULT_TEMPERATURE = 0.3
    DEFAULT_MAX_TOKENS = 8000

    def __init__(self, api_key: Optional[str] = None, timeout: float = 120.0):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise LLMError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable.")
        try:
            import anthropic
        except ImportError as exc:
            raise LLMError("Anthropic SDK not installed. Run: pip install anthropic>=0.40.0") from exc
        self.timeout = timeout
        self._client = anthropic.AsyncAnthropic(api_key=self.api_key, timeout=timeout)

    async def analyze_script(
        self,
        script_text: str,
        prompt: str,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        expect_json: bool = True,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        full_content = f"""{prompt}

---

SCRIPT CONTENT:

{script_text}

---

Provide your analysis based on the instructions above."""
        system_prompt = "You are an expert script coverage analyst with 20+ years of experience reading screenplays and TV pilots for major studios and production companies. You provide professional, objective, and constructive coverage."
        if expect_json:
            system_prompt += "\n\nIMPORTANT: Return valid JSON only."
        try:
            response = await self._client.messages.create(
                model=model,
                max_tokens=max_tokens or self.DEFAULT_MAX_TOKENS,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": full_content}],
            )
            content = response.content[0].text
            if expect_json:
                try:
                    return json.loads(content)
                except json.JSONDecodeError as exc:
                    raise LLMError(f"Failed to parse Claude JSON response: {exc}\nPreview: {content[:500]}") from exc
            return {"content": content}
        except Exception as exc:
            raise LLMError(f"Claude analysis failed: {exc}") from exc

    async def analyze_with_chunking(
        self,
        script_text: str,
        prompt: str,
        chunk_size: int = 60000,
        overlap: int = 5000,
        model: str = DEFAULT_MODEL,
    ) -> Dict[str, Any]:
        chunks = []
        start = 0
        while start < len(script_text):
            end = start + chunk_size
            if end < len(script_text):
                newline_pos = script_text.rfind("\n", end - 100, end + 100)
                if newline_pos != -1:
                    end = newline_pos
            chunks.append(script_text[start:end])
            start = end - overlap
        if len(chunks) == 1:
            return await self.analyze_script(chunks[0], prompt, model)
        chunk_results = []
        for i, chunk in enumerate(chunks):
            chunk_prompt = f"{prompt}\n\nNote: This is chunk {i + 1} of {len(chunks)} of the script."
            chunk_results.append(await self.analyze_script(chunk, chunk_prompt, model))
        synthesis_prompt = f"""You have received analysis of a TV pilot script that was split into {len(chunks)} parts.

Synthesize these partial analyses into a single coherent coverage report.

Partial analyses:
{json.dumps(chunk_results, indent=2)}

Provide the final coverage report in the same JSON format as the individual analyses."""
        return await self.analyze_script("SYNTHESIS TASK - See prompt for partial analyses", synthesis_prompt, model, temperature=0.2)


_openai_client: Optional[OpenAIClient] = None
_claude_client: Optional[ClaudeClient] = None


def get_openai_client() -> OpenAIClient:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient()
    return _openai_client


def get_claude_client() -> ClaudeClient:
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client


def reset_clients():
    global _openai_client, _claude_client
    _openai_client = None
    _claude_client = None
