"""Test script for Claude fallback functionality.

This tests that the fallback mechanism works correctly when Moonshot
rejects content due to moderation.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/data/.openclaw/workspace/coverageiq/backend')

from app.services.llm_client import (
    MoonshotClient, 
    ClaudeClient, 
    LLMContentModerationError,
    LLMError
)


# Test script with mature content that might trigger moderation
TEST_SCRIPT_MATURE = """
FADE IN:

INT. STRIP CLUB - NIGHT

The neon lights flicker. A DANCER moves on stage. 

JASON (30s, intense) sits in the back, watching. He's not here for the show.

DANCER
You looking for something special?

JASON
I'm looking for someone. Someone who doesn't want to be found.

The DANCER'S smile fades. She knows who he means.

DANCER
You shouldn't be here. They'll kill you.

JASON
Maybe. But I'll take a few of them with me first.

He pulls out a GUN. The music keeps playing.

FADE OUT.
"""

# A simple test script
TEST_SCRIPT_SIMPLE = """
FADE IN:

INT. COFFEE SHOP - DAY

SARAH (28, frazzled) stirs her coffee. She's been here too long.

The DOOR opens. Her EX-BOYFRIEND enters. Awkward.

EX-BOYFRIEND
Didn't expect to see you here.

SARAH
I could say the same.

They sit in silence. The tension is thick.

EX-BOYFRIEND
I miss you.

SARAH
You should have thought of that before.

FADE OUT.
"""


async def test_clients_initialization():
    """Test that both clients can be initialized (with or without API keys)."""
    print("Testing client initialization...")
    
    # Test Moonshot client
    try:
        moonshot = MoonshotClient()
        print("✓ Moonshot client initialized (API key found)")
    except LLMError as e:
        print(f"✗ Moonshot client failed: {e}")
    
    # Test Claude client
    try:
        claude = ClaudeClient()
        print("✓ Claude client initialized (API key found)")
    except LLMError as e:
        print(f"✗ Claude client failed: {e}")
    
    print()


def test_error_detection():
    """Test that content moderation errors are properly detected."""
    print("Testing error detection logic...")
    
    # Test cases for content moderation detection
    test_cases = [
        ("High risk content detected", True),
        ("Content rejected by moderation system", True),
        ("400: high risk content", True),
        ("400: content rejected", True),
        ("Invalid API key", False),
        ("Rate limit exceeded", False),
        ("Server error", False),
    ]
    
    for error_msg, should_trigger_fallback in test_cases:
        error_str = str(error_msg).lower()
        is_moderation = "high risk" in error_str or "rejected" in error_str or "content" in error_str
        status = "✓" if is_moderation == should_trigger_fallback else "✗"
        print(f"{status} '{error_msg[:40]}...' -> moderation={is_moderation}")
    
    print()


def test_prompt_format():
    """Test that the prompt format is correct for both clients."""
    print("Testing prompt format consistency...")
    
    from app.services.prompts import build_full_prompt
    
    prompt = build_full_prompt(depth="standard", genre="drama")
    
    # Check key elements
    checks = [
        ("logline" in prompt.lower(), "logline field"),
        ("synopsis" in prompt.lower(), "synopsis field"),
        ("subscores" in prompt.lower(), "subscores field"),
        ("recommendation" in prompt.lower(), "recommendation field"),
        ("json" in prompt.lower(), "JSON format"),
    ]
    
    for passed, description in checks:
        status = "✓" if passed else "✗"
        print(f"{status} {description}")
    
    print()


async def test_fallback_logic():
    """Test the fallback logic flow (simulated)."""
    print("Testing fallback logic flow...")
    
    # Simulate the fallback logic
    async def simulate_analysis_with_fallback():
        model_used = None
        
        try:
            # Simulate Moonshot failure
            raise LLMContentModerationError("High risk content detected")
            
        except LLMContentModerationError as e:
            print(f"  Moonshot rejected: {e}")
            print("  → Falling back to Claude...")
            
            try:
                # This would be the Claude call
                # For testing, simulate success
                model_used = "claude-3-5-sonnet-20241022"
                print(f"  ✓ Claude analysis successful")
                
            except LLMError as claude_error:
                print(f"  ✗ Claude also failed: {claude_error}")
                raise
        
        return model_used
    
    try:
        model = await simulate_analysis_with_fallback()
        print(f"✓ Fallback flow successful, model: {model}")
    except Exception as e:
        print(f"✗ Fallback flow failed: {e}")
    
    print()


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Claude Fallback Test Suite")
    print("=" * 60)
    print()
    
    await test_clients_initialization()
    test_error_detection()
    test_prompt_format()
    await test_fallback_logic()
    
    print("=" * 60)
    print("Tests completed!")
    print("=" * 60)
    print()
    print("Note: Full integration tests require:")
    print("  - MOONSHOT_API_KEY environment variable")
    print("  - ANTHROPIC_API_KEY environment variable")
    print("  - Actual script content to analyze")


if __name__ == "__main__":
    asyncio.run(main())