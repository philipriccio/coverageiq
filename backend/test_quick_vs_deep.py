"""Test script to isolate Quick vs Deep mode hang issue.

This script tests both Quick and Deep analysis modes to see if the 85% hang
is specific to Deep mode or affects both.

Usage:
    cd /data/.openclaw/workspace/coverageiq/backend
    source venv/bin/activate
    export MOONSHOT_API_KEY="your-api-key"
    python test_quick_vs_deep.py
"""
import asyncio
import json
import os
import sys
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_client import MoonshotClient, LLMError
from app.services.prompts import build_full_prompt
from app.services.analysis import AnalysisPipeline


# Minimal sample script for testing
SAMPLE_SCRIPT = """
THE LAST FRONTIER

FADE IN:

EXT. MARS COLONY - DAY

COMMANDER JACK HARRISON (40s) steps out of the habitat module. 
The red dust swirls around his boots.

JACK
(into radio)
Base, this is Harrison. I'm 
proceeding to Sector 7.

DR. ELENA VOSS (30s, brilliant but cautious) joins him.

ELENA
Jack, the readings are off the 
charts. We shouldn't be out here.

JACK
We've got 48 hours of oxygen. We'll 
make it work.

They march across the desolate landscape.

Suddenly, a GROUND QUAKE shakes the area. A FISSURE opens nearby,
revealing something metallic beneath the surface.

ELENA
What the hell is that?

Jack approaches the fissure, peers down.

JACK
It's not natural. That's a structure.

FADE OUT.
"""


async def test_analysis_mode(mode: str, timeout: int = 300):
    """Test a specific analysis mode.
    
    Args:
        mode: 'quick', 'standard', or 'deep'
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"TESTING {mode.upper()} MODE")
    print(f"{'='*60}")
    
    start_time = datetime.now()
    
    try:
        pipeline = AnalysisPipeline()
        
        print(f"Starting {mode} analysis at {start_time.strftime('%H:%M:%S')}")
        print(f"Script length: {len(SAMPLE_SCRIPT)} characters")
        print(f"Timeout set to: {timeout}s")
        
        # Run analysis with explicit timeout
        results, model_used = await asyncio.wait_for(
            pipeline.analyze_script(
                script_text=SAMPLE_SCRIPT,
                report_id="test-report-id",
                script_id="test-script-id",
                genre="sci-fi",
                comps=["The Martian", "For All Mankind"],
                analysis_depth=mode,
                db=None  # No DB for this test
            ),
            timeout=timeout
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✓ {mode.upper()} analysis completed in {elapsed:.1f}s")
        print(f"  Model used: {model_used}")
        print(f"  Total score: {results.get('total_score', 'N/A')}")
        print(f"  Recommendation: {results.get('recommendation', 'N/A')}")
        print(f"  Strengths found: {len(results.get('strengths', []))}")
        print(f"  Weaknesses found: {len(results.get('weaknesses', []))}")
        
        return True
        
    except asyncio.TimeoutError:
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n✗ {mode.upper()} analysis TIMED OUT after {elapsed:.1f}s")
        return False
        
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n✗ {mode.upper()} analysis FAILED after {elapsed:.1f}s: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run tests for all analysis modes."""
    print("="*60)
    print("QUICK VS DEEP MODE HANG TEST")
    print("="*60)
    print("\nThis test will run both Quick and Deep analysis to identify")
    print("if the 85% hang is specific to Deep mode.")
    
    # Check API key
    if not os.getenv("MOONSHOT_API_KEY"):
        print("\n✗ MOONSHOT_API_KEY not set!")
        print("Please set the environment variable and try again.")
        return 1
    
    print(f"\nMOONSHOT_API_KEY: {'✓ Set (' + os.getenv('MOONSHOT_API_KEY')[:10] + '...)'}" )
    
    results = {}
    
    # Test Quick mode first (should complete quickly)
    print("\n" + "="*60)
    print("PHASE 1: QUICK MODE (Expected: ~30-60s)")
    print("="*60)
    results['quick'] = await test_analysis_mode('quick', timeout=120)
    
    # Test Standard mode
    print("\n" + "="*60)
    print("PHASE 2: STANDARD MODE (Expected: ~60-120s)")
    print("="*60)
    results['standard'] = await test_analysis_mode('standard', timeout=180)
    
    # Test Deep mode last (may hang)
    print("\n" + "="*60)
    print("PHASE 3: DEEP MODE (Expected: ~120-300s, may hang at 85%)")
    print("="*60)
    results['deep'] = await test_analysis_mode('deep', timeout=360)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for mode, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"  {mode.capitalize():12} {status}")
    
    # Diagnosis
    print("\n" + "="*60)
    print("DIAGNOSIS")
    print("="*60)
    
    if results['quick'] and results['standard'] and results['deep']:
        print("✓ All modes completed successfully!")
        print("  The 85% hang issue appears to be resolved.")
    elif results['quick'] and results['standard'] and not results['deep']:
        print("⚠ Quick and Standard work, but Deep fails!")
        print("  This confirms the 85% hang is DEEP-MODE SPECIFIC.")
        print("\nPossible causes:")
        print("  - 20K token generation takes too long")
        print("  - JSON parsing fails on large responses")
        print("  - Memory issue with large response handling")
    elif results['quick'] and not results['standard'] and not results['deep']:
        print("⚠ Only Quick mode works!")
        print("  The hang affects STANDARD and DEEP modes.")
        print("\nPossible causes:")
        print("  - General LLM timeout issue")
        print("  - Response size causing JSON parsing delays")
    else:
        print("✗ All modes failed!")
        print("  There's a general system issue, not mode-specific.")
    
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
