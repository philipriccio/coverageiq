"""Moonshot AI (Kimi K2.5) and Anthropic (Claude) LLM clients for CoverageIQ.

This module provides clients for the Moonshot AI API and Anthropic Claude API to generate script coverage.
Moonshot is the primary client (cheaper), with Claude as a fallback for content moderation rejections.

API Documentation:
- Moonshot: https://platform.moonshot.cn/docs
- Anthropic: https://docs.anthropic.com/
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


class LLMContentModerationError(LLMError):
    """Raised when content is rejected by moderation (for fallback triggering)."""
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
        stream: bool = False,
        timeout_override: Optional[float] = None
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
            LLMContentModerationError: If content is rejected by moderation (for fallback)
        """
        import time
        start_time = time.time()
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        if response_format:
            payload["response_format"] = response_format
        
        # Use explicit timeout configuration for all phases
        # Adjust timeout based on max_tokens - larger responses need more time
        # Rough estimate: ~3 seconds per 1000 tokens minimum, with 60s base
        calculated_timeout = timeout_override or max(self.timeout, 60.0 + (max_tokens / 1000.0 * 3.0))
        timeout_config = httpx.Timeout(
            connect=30.0,          # Time to establish connection
            read=calculated_timeout, # Time to read response - scales with expected output
            write=60.0,            # Time to send request (increased for large prompts)
            pool=30.0              # Time to get connection from pool
        )
        print(f"[Moonshot] Using timeout: {calculated_timeout:.1f}s for {max_tokens} max_tokens")
        
        print(f"[Moonshot] Sending request to {model} (max_tokens: {max_tokens})...")
        print(f"[Moonshot] Request payload size: {len(str(payload))} chars")
        
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                
                elapsed = time.time() - start_time
                print(f"[Moonshot] Response received in {elapsed:.1f}s")
                
                if response.status_code == 429:
                    raise LLMRateLimitError("Rate limit exceeded. Please try again.")
                elif response.status_code == 401:
                    raise LLMError("Invalid API key")
                elif response.status_code == 400:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    # Check for content moderation rejection
                    error_str = str(error_msg).lower()
                    if "high risk" in error_str or "rejected" in error_str or "content" in error_str:
                        raise LLMContentModerationError(f"Content rejected by moderation: {error_msg}")
                    raise LLMError(f"API error ({response.status_code}): {error_msg}")
                elif response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    raise LLMError(f"API error ({response.status_code}): {error_msg}")
                
                return response.json()
                
            except httpx.TimeoutException as e:
                elapsed = time.time() - start_time
                raise LLMError(f"Request timeout after {elapsed:.1f}s (timeout: {calculated_timeout:.1f}s, max_tokens: {max_tokens}): {str(e)}")
            except httpx.ConnectError as e:
                raise LLMError(f"Connection error: {str(e)}. Check network connectivity.")
            except httpx.HTTPError as e:
                raise LLMError(f"HTTP error: {str(e)}")
    
    async def analyze_script(
        self,
        script_text: str,
        prompt: str,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        expect_json: bool = True,
        max_tokens: Optional[int] = None
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
            max_tokens: Maximum tokens to generate (defaults to DEFAULT_MAX_TOKENS)
            
        Returns:
            Parsed response (JSON dict if expect_json=True, else string)
            
        Raises:
            LLMError: If analysis fails
            LLMContentModerationError: If content is rejected by moderation
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
        
        # Use provided max_tokens or default
        token_limit = max_tokens if max_tokens is not None else self.DEFAULT_MAX_TOKENS
        
        print(f"[Moonshot] DEBUG: About to call chat_completion...")
        result = await self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=token_limit,
            response_format=response_format
        )
        
        print(f"[Moonshot] DEBUG: chat_completion returned")
        # Extract the generated content
        content = result["choices"][0]["message"]["content"]
        
        # Log token usage for debugging
        usage = result.get("usage", {})
        completion_tokens = usage.get("completion_tokens", 0)
        print(f"[Moonshot] Response tokens used: {completion_tokens}/{token_limit}")
        
        if expect_json:
            print(f"[Moonshot] DEBUG: About to parse JSON (content length: {len(content)} chars)...")
            try:
                parsed = json.loads(content)
                print(f"[Moonshot] JSON parsed successfully")
                return parsed
            except json.JSONDecodeError as e:
                # Check if response was likely truncated
                if completion_tokens >= token_limit * 0.95:
                    raise LLMError(
                        f"JSON response appears truncated (used {completion_tokens}/{token_limit} tokens). "
                        f"Parse error: {str(e)}. Consider increasing max_tokens for this analysis depth."
                        f"\nContent preview: {content[:500]}..."
                    )
                raise LLMError(
                    f"Failed to parse JSON response: {str(e)}\n"
                    f"Content preview: {content[:500]}..."
                )
        
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


class ClaudeClient:
    """Client for Anthropic Claude API.
    
    Claude is used as a fallback when Moonshot rejects content due to
    content moderation (e.g., mature themes, HBO-style scripts).
    
    Model: claude-sonnet-4-5
    
    Privacy Note: Script content is sent to Anthropic API for analysis.
    Per Anthropic's terms, data is not retained or used for training
    when using the API with appropriate settings.
    """
    
    # Anthropic model
    MODEL_CLAUDE_SONNET = "claude-sonnet-4-5"
    DEFAULT_MODEL = MODEL_CLAUDE_SONNET
    
    DEFAULT_TEMPERATURE = 0.3  # Same as Moonshot for consistency
    DEFAULT_MAX_TOKENS = 8000  # Same as Moonshot
    
    def __init__(self, api_key: Optional[str] = None, timeout: float = 120.0):
        """Initialize the Claude client.
        
        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise LLMError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable."
            )
        
        self.timeout = timeout
        
        # Initialize the official Anthropic client
        try:
            import anthropic
            self._client = anthropic.AsyncAnthropic(
                api_key=self.api_key,
                timeout=timeout
            )
        except ImportError:
            raise LLMError(
                "Anthropic SDK not installed. Run: pip install anthropic>=0.40.0"
            )
    
    async def analyze_script(
        self,
        script_text: str,
        prompt: str,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        expect_json: bool = True,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Analyze script content with a custom prompt.
        
        This mirrors the Moonshot client's interface for drop-in replacement.
        
        Args:
            script_text: Full text of the screenplay
            prompt: The analysis prompt (should include instructions and format)
            model: Model to use
            temperature: Temperature for generation
            expect_json: Whether to expect and parse JSON response
            max_tokens: Maximum tokens to generate (defaults to DEFAULT_MAX_TOKENS)
            
        Returns:
            Parsed response (JSON dict if expect_json=True, else string)
            
        Raises:
            LLMError: If analysis fails
        """
        import anthropic
        import time
        
        start_time = time.time()
        
        # Construct the full content (same format as Moonshot)
        full_content = f"""{prompt}

---

SCRIPT CONTENT:

{script_text}

---

Provide your analysis based on the instructions above."""
        
        system_prompt = "You are an expert script coverage analyst with 20+ years of experience reading screenplays and TV pilots for major studios and production companies. You provide professional, objective, and constructive coverage."
        
        # Use provided max_tokens or default
        token_limit = max_tokens if max_tokens is not None else self.DEFAULT_MAX_TOKENS
        
        print(f"[Claude] Sending request to {model} (max_tokens: {token_limit})...")
        
        try:
            # Add JSON instruction to system prompt if expecting JSON
            if expect_json:
                system_prompt += "\n\nIMPORTANT: Your response must be valid JSON only. Do not include any markdown formatting, code blocks, or explanatory text outside the JSON structure."
            
            response = await self._client.messages.create(
                model=model,
                max_tokens=token_limit,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": full_content
                    }
                ]
            )
            
            elapsed = time.time() - start_time
            print(f"[Claude] Response received in {elapsed:.1f}s")
            
            # Extract usage info for debugging
            usage = response.usage if hasattr(response, 'usage') else None
            if usage:
                output_tokens = getattr(usage, 'output_tokens', 0)
                print(f"[Claude] Response tokens used: {output_tokens}/{token_limit}")
            
            # Extract the generated content
            content = response.content[0].text
            
            if expect_json:
                # Try to extract JSON from the response (in case there's markdown)
                try:
                    # First, try direct parsing
                    parsed = json.loads(content)
                    print(f"[Claude] JSON parsed successfully")
                    return parsed
                except json.JSONDecodeError as e:
                    # Try to extract JSON from markdown code blocks
                    import re
                    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
                    if json_match:
                        try:
                            parsed = json.loads(json_match.group(1))
                            print(f"[Claude] JSON parsed from markdown block")
                            return parsed
                        except json.JSONDecodeError:
                            pass
                    # Try to find JSON between curly braces
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        try:
                            parsed = json.loads(json_match.group(0))
                            print(f"[Claude] JSON parsed from curly braces")
                            return parsed
                        except json.JSONDecodeError:
                            pass
                    
                    # Check if response was likely truncated
                    if usage and output_tokens >= token_limit * 0.95:
                        raise LLMError(
                            f"JSON response appears truncated (used {output_tokens}/{token_limit} tokens). "
                            f"Parse error: {str(e)}. Consider increasing max_tokens for this analysis depth."
                        )
                    raise LLMError(
                        f"Failed to parse JSON response: {str(e)}\n"
                        f"Content preview: {content[:500]}..."
                    )
            
            return {"content": content}
            
        except anthropic.APITimeoutError as e:
            elapsed = time.time() - start_time
            raise LLMError(f"Claude request timed out after {elapsed:.1f}s (timeout: {self.timeout}s). The script may be too long or the API is experiencing delays.")
        except anthropic.APIStatusError as e:
            elapsed = time.time() - start_time
            if e.status_code == 429:
                raise LLMRateLimitError(f"Anthropic rate limit exceeded: {str(e)}")
            elif e.status_code == 401:
                raise LLMError(f"Invalid Anthropic API key: {str(e)}")
            else:
                raise LLMError(f"Anthropic API error ({e.status_code}) after {elapsed:.1f}s: {str(e)}")
        except anthropic.APIError as e:
            elapsed = time.time() - start_time
            raise LLMError(f"Anthropic API error (after {elapsed:.1f}s): {str(e)}")
        except Exception as e:
            elapsed = time.time() - start_time
            raise LLMError(f"Claude analysis failed after {elapsed:.1f}s: {str(e)}")
    
    async def analyze_with_chunking(
        self,
        script_text: str,
        prompt: str,
        chunk_size: int = 60000,
        overlap: int = 5000,
        model: str = DEFAULT_MODEL
    ) -> Dict[str, Any]:
        """Analyze a long script by chunking it.
        
        Mirrors the Moonshot chunking behavior for consistency.
        
        Args:
            script_text: Full script text
            prompt: Analysis prompt
            chunk_size: Characters per chunk (default 60k for ~15k tokens)
            overlap: Overlap between chunks to maintain context
            model: Model to use
            
        Returns:
            Synthesized analysis results
        """
        # Simple chunking by character count (same as Moonshot)
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
        
        Claude 3.5 Sonnet pricing (as of early 2025):
        - Input: $3 per 1M tokens ($0.003 per 1K)
        - Output: $15 per 1M tokens ($0.015 per 1K)
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model being used
            
        Returns:
            Estimated cost in USD
        """
        # Claude Sonnet pricing
        input_rate = 0.003  # $ per 1K tokens
        output_rate = 0.015  # $ per 1K tokens
        
        input_cost = (input_tokens / 1000) * input_rate
        output_cost = (output_tokens / 1000) * output_rate
        
        return round(input_cost + output_cost, 4)


# Singleton instances for application use
_moonshot_client: Optional[MoonshotClient] = None
_claude_client: Optional[ClaudeClient] = None


def get_moonshot_client() -> MoonshotClient:
    """Get or create the Moonshot client singleton.
    
    Returns:
        MoonshotClient instance
    """
    global _moonshot_client
    if _moonshot_client is None:
        _moonshot_client = MoonshotClient()
    return _moonshot_client


def get_claude_client() -> ClaudeClient:
    """Get or create the Claude client singleton.
    
    Returns:
        ClaudeClient instance
    """
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client


def reset_clients():
    """Reset the singleton clients (useful for testing)."""
    global _moonshot_client, _claude_client
    _moonshot_client = None
    _claude_client = None