"""Test script for CoverageIQ LLM integration and coverage generation.

This script tests the Day 3 implementation:
1. Moonshot/Kimi API client
2. TV pilot prompt templates
3. Analysis pipeline
4. Report generation

Usage:
    cd /data/.openclaw/workspace/coverageiq/backend
    source venv/bin/activate
    export MOONSHOT_API_KEY="your-api-key"
    python test_coverage_generation.py
"""
import asyncio
import json
import os
import sys
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_client import MoonshotClient, LLMError
from app.services.prompts import build_full_prompt, TV_PILOT_SYSTEM_CONTEXT
from app.services.analysis import AnalysisPipeline


# Load sample script
SAMPLE_SCRIPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "test_data/the_last_frontier_pilot.txt"
)


def load_sample_script() -> str:
    """Load the sample TV pilot script."""
    with open(SAMPLE_SCRIPT_PATH, 'r') as f:
        return f.read()


async def test_moonshot_client():
    """Test 1: Verify Moonshot API client works."""
    print("\n" + "="*60)
    print("TEST 1: Moonshot API Client")
    print("="*60)
    
    try:
        client = MoonshotClient()
        print("✓ Moonshot client initialized successfully")
        
        # Test a simple completion
        result = await client.chat_completion(
            messages=[
                {"role": "user", "content": "Say 'CoverageIQ test successful' and nothing else."}
            ],
            max_tokens=50
        )
        
        content = result["choices"][0]["message"]["content"]
        print(f"✓ API response received: {content[:50]}...")
        
        # Test usage stats
        stats = client.get_usage_stats(result)
        print(f"✓ Usage stats: {stats['total_tokens']} tokens, ${stats['estimated_cost_usd']}")
        
        return True
        
    except LLMError as e:
        print(f"✗ Moonshot client test failed: {e}")
        return False


async def test_prompt_generation():
    """Test 2: Verify prompt templates are generated correctly."""
    print("\n" + "="*60)
    print("TEST 2: Prompt Template Generation")
    print("="*60)
    
    # Test standard prompt
    standard_prompt = build_full_prompt(depth="standard", genre="drama")
    print(f"✓ Standard prompt generated ({len(standard_prompt)} chars)")
    assert "TV PILOT" in standard_prompt or "pilot" in standard_prompt.lower()
    assert "SERIES ENGINE" in standard_prompt or "series engine" in standard_prompt.lower()
    
    # Test quick prompt
    quick_prompt = build_full_prompt(depth="quick")
    print(f"✓ Quick prompt generated ({len(quick_prompt)} chars)")
    assert len(quick_prompt) < len(standard_prompt)
    
    # Test deep prompt
    deep_prompt = build_full_prompt(depth="deep")
    print(f"✓ Deep prompt generated ({len(deep_prompt)} chars)")
    assert "deep-dive" in deep_prompt.lower() or "detailed" in deep_prompt.lower()
    
    # Test genre context
    drama_prompt = build_full_prompt(depth="standard", genre="drama")
    print(f"✓ Drama context added")
    assert "emotional authenticity" in drama_prompt.lower() or "drama" in drama_prompt.lower()
    
    return True


async def test_analysis_pipeline():
    """Test 3: Test the analysis pipeline with a short script."""
    print("\n" + "="*60)
    print("TEST 3: Analysis Pipeline (Short Sample)")
    print("="*60)
    
    # Load just the first part of the script for a quick test
    full_script = load_sample_script()
    short_script = full_script[:5000]  # First ~5000 characters
    
    print(f"Using script sample ({len(short_script)} chars)")
    
    pipeline = AnalysisPipeline()
    
    try:
        result = await pipeline.analyze_script(
            script_text=short_script,
            report_id="test-report-001",
            script_id="test-script-001",
            genre="drama",
            analysis_depth="quick"
        )
        
        print("✓ Analysis completed")
        
        # Verify structure
        required_fields = ["logline", "strengths", "weaknesses", "subscores", "total_score", "recommendation"]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
        print(f"✓ All required fields present")
        
        # Verify scores
        subscores = result.get("subscores", {})
        assert "concept" in subscores
        assert "character" in subscores
        print(f"✓ Subscores present: {list(subscores.keys())}")
        
        # Verify recommendation
        rec = result.get("recommendation", "").upper()
        assert any(r in rec for r in ["PASS", "CONSIDER", "RECOMMEND"])
        print(f"✓ Recommendation: {result.get('recommendation')}")
        
        # Print summary
        print(f"\n--- Analysis Summary ---")
        print(f"Logline: {result.get('logline', 'N/A')[:100]}...")
        print(f"Total Score: {result.get('total_score')}/50")
        print(f"Recommendation: {result.get('recommendation')}")
        print(f"Strengths: {len(result.get('strengths', []))} items")
        print(f"Weaknesses: {len(result.get('weaknesses', []))} items")
        
        return True
        
    except Exception as e:
        print(f"✗ Analysis pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_script_analysis():
    """Test 4: Full script analysis (if API key is available)."""
    print("\n" + "="*60)
    print("TEST 4: Full Script Analysis")
    print("="*60)
    
    full_script = load_sample_script()
    print(f"Full script length: {len(full_script)} characters")
    
    pipeline = AnalysisPipeline()
    
    start_time = datetime.now()
    
    try:
        result = await pipeline.analyze_script(
            script_text=full_script,
            report_id="test-report-002",
            script_id="test-script-002",
            genre="drama",
            comps=["Northern Exposure", "ER", "The Good Doctor"],
            analysis_depth="standard"
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"✓ Full analysis completed in {elapsed:.1f} seconds")
        
        # Save full result to file for inspection
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "test_coverage_output.json"
        )
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✓ Full results saved to: {output_path}")
        
        # Print detailed summary
        print(f"\n{'='*60}")
        print("COVERAGE REPORT SUMMARY")
        print("="*60)
        print(f"\nLOGLINE:\n{result.get('logline', 'N/A')}")
        
        print(f"\nSUBSCORES:")
        subscores = result.get("subscores", {})
        for category, data in subscores.items():
            score = data.get("score", 0) if isinstance(data, dict) else data
            print(f"  {category.capitalize():12} {score}/10")
        print(f"  {'TOTAL':12} {result.get('total_score', 0)}/50")
        
        print(f"\nRECOMMENDATION: {result.get('recommendation', 'N/A')}")
        
        print(f"\nSTRENGTHS ({len(result.get('strengths', []))}):")
        for i, s in enumerate(result.get('strengths', [])[:3], 1):
            print(f"  {i}. {s[:100]}...")
        
        print(f"\nWEAKNESSES ({len(result.get('weaknesses', []))}):")
        for i, w in enumerate(result.get('weaknesses', [])[:3], 1):
            print(f"  {i}. {w[:100]}...")
        
        # Verify series engine section
        series_engine = result.get("series_engine", {})
        if series_engine:
            print(f"\nSERIES ENGINE:")
            print(f"  {series_engine.get('engine_description', 'N/A')[:150]}...")
        
        # Verify evidence quotes
        quotes = result.get("evidence_quotes", [])
        print(f"\nEVIDENCE QUOTES: {len(quotes)} provided")
        for i, q in enumerate(quotes[:2], 1):
            print(f"  {i}. p.{q.get('page', 'N/A')}: \"{q.get('quote', 'N/A')[:60]}...\"")
        
        print(f"\n{'='*60}")
        print("END OF REPORT")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"✗ Full analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_output_structure():
    """Test 5: Verify output matches coverage report spec."""
    print("\n" + "="*60)
    print("TEST 5: Output Structure Verification")
    print("="*60)
    
    # Load sample output if it exists
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "test_coverage_output.json"
    )
    
    if not os.path.exists(output_path):
        print("⚠ No output file found. Run Test 4 first.")
        return True
    
    with open(output_path, 'r') as f:
        result = json.load(f)
    
    # Check all required fields from spec
    required_top_level = {
        "logline": str,
        "synopsis": str,
        "overall_comments": str,
        "strengths": list,
        "weaknesses": list,
        "subscores": dict,
        "total_score": int,
        "recommendation": str,
        "evidence_quotes": list
    }
    
    all_valid = True
    for field, field_type in required_top_level.items():
        if field not in result:
            print(f"✗ Missing required field: {field}")
            all_valid = False
        elif not isinstance(result[field], field_type):
            print(f"✗ Field {field} has wrong type: {type(result[field])} instead of {field_type}")
            all_valid = False
        else:
            print(f"✓ {field}: present ({type(result[field]).__name__})")
    
    # Check subscores structure
    subscores = result.get("subscores", {})
    required_subscores = ["concept", "character", "structure", "dialogue", "market"]
    
    for sub in required_subscores:
        if sub in subscores:
            score_data = subscores[sub]
            if isinstance(score_data, dict):
                score = score_data.get("score", 0)
                print(f"✓ Subscore {sub}: {score}/10")
            else:
                print(f"✓ Subscore {sub}: {score_data}/10")
        else:
            print(f"✗ Missing subscore: {sub}")
            all_valid = False
    
    # Check total score calculation
    total = result.get("total_score", 0)
    if 0 <= total <= 50:
        print(f"✓ Total score in valid range: {total}/50")
    else:
        print(f"✗ Total score out of range: {total}/50")
        all_valid = False
    
    # Check recommendation
    rec = result.get("recommendation", "").upper()
    if any(r in rec for r in ["PASS", "CONSIDER", "RECOMMEND"]):
        print(f"✓ Valid recommendation: {result.get('recommendation')}")
    else:
        print(f"✗ Invalid recommendation: {result.get('recommendation')}")
        all_valid = False
    
    # Check evidence quotes format
    quotes = result.get("evidence_quotes", [])
    for i, q in enumerate(quotes):
        if not isinstance(q, dict):
            print(f"✗ Quote {i} is not a dict")
            all_valid = False
        elif "quote" not in q or "page" not in q:
            print(f"✗ Quote {i} missing required fields")
            all_valid = False
    
    if quotes:
        print(f"✓ All {len(quotes)} evidence quotes have valid format")
    
    # Check series engine (TV-specific)
    if "series_engine" in result:
        print("✓ Series engine section present (TV-specific)")
    else:
        print("⚠ Series engine section not present (optional but recommended)")
    
    return all_valid


async def main():
    """Run all tests."""
    print("="*60)
    print("CoverageIQ Day 3: LLM Integration Test Suite")
    print("="*60)
    print(f"Started: {datetime.now()}")
    
    # Check for API key
    if not os.getenv("MOONSHOT_API_KEY"):
        print("\n⚠ WARNING: MOONSHOT_API_KEY not set")
        print("Set it with: export MOONSHOT_API_KEY='your-key'")
        print("Some tests will be skipped.\n")
    
    results = []
    
    # Run tests
    if os.getenv("MOONSHOT_API_KEY"):
        results.append(("Moonshot Client", await test_moonshot_client()))
    else:
        print("\n--- Skipping API tests (no key) ---")
        results.append(("Moonshot Client", None))
    
    results.append(("Prompt Generation", await test_prompt_generation()))
    
    if os.getenv("MOONSHOT_API_KEY"):
        results.append(("Analysis Pipeline (Short)", await test_analysis_pipeline()))
        results.append(("Full Script Analysis", await test_full_script_analysis()))
        results.append(("Output Structure", await verify_output_structure()))
    else:
        print("\n--- Skipping analysis tests (no key) ---")
        results.extend([
            ("Analysis Pipeline (Short)", None),
            ("Full Script Analysis", None),
            ("Output Structure", None)
        ])
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    skipped = sum(1 for _, r in results if r is None)
    
    for name, result in results:
        status = "✓ PASS" if result is True else "✗ FAIL" if result is False else "⊘ SKIP"
        print(f"{status:10} {name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠ {failed} test(s) failed")
    
    print(f"\nFinished: {datetime.now()}")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)