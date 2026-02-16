"""Moonshot AI (Kimi K2.5) LLM client for CoverageIQ.

This module provides a client for the Moonshot AI API to generate script coverage.
The Kimi K2.5 model is optimized for long-context analysis and creative writing assessment.

API Documentation: https://platform.moonshot.cn/docs
"""
import json
import os
from typing import AsyncGenerator, Dict, List, Optional, Any
import httpx
from datetime import datetime


class LLMError(Exception):
    """Raised when LLM API call fails."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when rate limit is exceeded."""
    pass


class MoonshotClient:
    """Client for Moonshot AI API (Kimi models).
    
    Kimi K2.5 is the default model for CoverageIQ because of its excellent
    long-context capabilities and strong performance on creative writing analysis.
    
    Privacy Note: Script content is sent to Moonshot API for analysis.
    Per Moonshot's terms, data is not retained or used for training when
    using the API (as opposed to the consumer chat interface).
    """
    
    # Moonshot API endpoints
    BASE_URL = "https://api.moonshot.ai/v1"
    
    # Available models
    MODEL_KIMI_K2_5 = "moonshot-v1-128k"  # Kimi K2.5 with 128k context
    MODEL_KIMI_K2 = "moonshot-v1-32k"      # Kimi K2 with 32k context
    
    DEFAULT_MODEL = MODEL_KIMI_K2_5
    DEFAULT_TEMPERATURE = 0.3  # Lower temperature for more consistent analysis
    DEFAULT_MAX_TOKENS = 8000  # Sufficient for detailed coverage
    
    def __init__(self, api_key: Optional[str] = None, timeout: float = 120.0):
        """Initialize the Moonshot client.
        
        Args:
            api_key: Moonshot API key. If None, reads from MOONSHOT_API_KEY env var.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY")
        if not self.api_key:
            raise LLMError(
                "Moonshot API key required. Set MOONSHOT_API_KEY environment variable."
            )
        
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        response_format: Optional[Dict[str, str]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Send a chat completion request to Moonshot API.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            model: Model ID to use
            temperature: Sampling temperature (0-2, lower is more deterministic)
            max_tokens: Maximum tokens to generate
            response_format: Optional format specification (e.g., {"type": "json_object"})
            stream: Whether to stream the response
            
        Returns:
            API response as dictionary
            
        Raises:
            LLMError: If the API call fails
            LLMRateLimitError: If rate limit is exceeded
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        if response_format:
            payload["response_format"] = response_format
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 429:
                    raise LLMRateLimitError("Rate limit exceeded. Please try again.")
                elif response.status_code == 401:
                    raise LLMError("Invalid API key")
                elif response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    raise LLMError(f"API error ({response.status_code}): {error_msg}")
                
                return response.json()
                
            except httpx.TimeoutException:
                raise LLMError(f"Request timeout after {self.timeout}s")
            except httpx.HTTPError as e:
                raise LLMError(f"HTTP error: {str(e)}")
    
    async def analyze_script(
        self,
        script_text: str,
        prompt: str,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        expect_json: bool = True
    ) -> Dict[str, Any]:
        """Analyze script content with a custom prompt.
        
        This is the primary method for generating coverage. It sends the
        script text along with a structured prompt to the LLM.
        
        Args:
            script_text: Full text of the screenplay
            prompt: The analysis prompt (should include instructions and format)
            model: Model to use
            temperature: Temperature for generation
            expect_json: Whether to expect and parse JSON response
            
        Returns:
            Parsed response (JSON dict if expect_json=True, else string)
            
        Raises:
            LLMError: If analysis fails
        """
        # Construct the full message with script context
        # We include the script first, then the prompt with instructions
        full_content = f"""{prompt}

---

SCRIPT CONTENT:

{script_text}

---

Provide your analysis based on the instructions above."""
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert script coverage analyst with 20+ years of experience reading screenplays and TV pilots for major studios and production companies. You provide professional, objective, and constructive coverage."
            },
            {
                "role": "user",
                "content": full_content
            }
        ]
        
        response_format = {"type": "json_object"} if expect_json else None
        
        result = await self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            response_format=response_format
        )
        
        # Extract the generated content
        content = result["choices"][0]["message"]["content"]
        
        if expect_json:
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise LLMError(f"Failed to parse JSON response: {str(e)}\nContent: {content[:500]}")
        
        return {"content": content}
    
    async def analyze_with_chunking(
        self,
        script_text: str,
        prompt: str,
        chunk_size: int = 60000,
        overlap: int = 5000,
        model: str = DEFAULT_MODEL
    ) -> Dict[str, Any]:
        """Analyze a long script by chunking it.
        
        For very long scripts, we split them into chunks, analyze each,
        and then synthesize the results. This ensures we can handle
        scripts of any length within the context window.
        
        Args:
            script_text: Full script text
            prompt: Analysis prompt
            chunk_size: Characters per chunk (default 60k for ~15k tokens)
            overlap: Overlap between chunks to maintain context
            model: Model to use
            
        Returns:
            Synthesized analysis results
        """
        # Simple chunking by character count
        # For production, this should be smarter (scene-aware)
        chunks = []
        start = 0
        while start < len(script_text):
            end = start + chunk_size
            if end < len(script_text):
                # Try to break at a newline
                newline_pos = script_text.rfind('\n', end - 100, end + 100)
                if newline_pos != -1:
                    end = newline_pos
            chunks.append(script_text[start:end])
            start = end - overlap  # Overlap for context
        
        if len(chunks) == 1:
            # Short script - single analysis
            return await self.analyze_script(chunks[0], prompt, model)
        
        # Long script - multi-stage analysis
        print(f"Script split into {len(chunks)} chunks for analysis")
        
        # Analyze each chunk
        chunk_results = []
        for i, chunk in enumerate(chunks):
            print(f"Analyzing chunk {i+1}/{len(chunks)}...")
            chunk_prompt = f"""{prompt}

Note: This is chunk {i+1} of {len(chunks)} of the script. Focus on the content in this section while keeping in mind it's part of a larger work."""
            
            result = await self.analyze_script(chunk, chunk_prompt, model)
            chunk_results.append(result)
        
        # Synthesize results
        synthesis_prompt = f"""You have received analysis of a TV pilot script that was split into {len(chunks)} parts. 

Synthesize these partial analyses into a single coherent coverage report. Resolve any contradictions, identify patterns across the full script, and provide a unified assessment.

Partial analyses:
{json.dumps(chunk_results, indent=2)}

Provide the final coverage report in the same JSON format as the individual analyses."""
        
        return await self.analyze_script(
            "SYNTHESIS TASK - See prompt for partial analyses",
            synthesis_prompt,
            model,
            temperature=0.2  # Lower temp for synthesis
        )
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str = DEFAULT_MODEL) -> float:
        """Estimate the cost of an API call.
        
        Kimi K2.5 pricing (approximate, in USD):
        - Input: ~$0.005 per 1K tokens
        - Output: ~$0.015 per 1K tokens
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model being used
            
        Returns:
            Estimated cost in USD
        """
        # Kimi pricing (as of early 2025)
        input_rate = 0.005  # $ per 1K tokens
        output_rate = 0.015  # $ per 1K tokens
        
        input_cost = (input_tokens / 1000) * input_rate
        output_cost = (output_tokens / 1000) * output_rate
        
        return round(input_cost + output_cost, 4)
    
    def get_usage_stats(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract usage statistics from API response.
        
        Args:
            response: API response dictionary
            
        Returns:
            Dictionary with usage stats including estimated cost
        """
        usage = response.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": self.estimate_cost(prompt_tokens, completion_tokens)
        }


# Singleton instance for application use
_client: Optional[MoonshotClient] = None


def get_moonshot_client() -> MoonshotClient:
    """Get or create the Moonshot client singleton.
    
    Returns:
        MoonshotClient instance
    """
    global _client
    if _client is None:
        _client = MoonshotClient()
    return _client


def reset_client():
    """Reset the singleton client (useful for testing)."""
    global _client
    _client = None