"""Quick demonstration of CoverageIQ Day 3 functionality.

This script demonstrates the complete coverage generation pipeline
using the sample TV pilot script.

Usage:
    export MOONSHOT_API_KEY="your-key"
    python demo_coverage.py
"""
import asyncio
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_client import get_moonshot_client
from app.services.prompts import build_full_prompt
from app.services.analysis import AnalysisPipeline


SAMPLE_SCRIPT = """
THE LAST FRONTIER

FADE IN:

EXT. ALASKAN WILDERNESS - DAWN

The vast, snow-covered expanse of the Brooks Range. A red CESSNA 185 
bush plane fighting the wind.

INT. BUSH PLANE - CONTINUOUS

MAGGIE CHEN (35), hard-edged, grips the controls. Her passenger, 
DR. ELIJAH CROSS (40s), looks terrified.

MAGGIE
You gonna be sick, Doc?

ELIJAH
(through gritted teeth)
I'm fine. Just... focused.

MAGGIE
That's what they all say.

EXT. REMOTE VILLAGE - DAY

The plane touches down. Villagers wait - this is KOYUKUK, population 94.

Maggie helps Elijah with his bag. A WOMAN rushes forward with a BABY.

WOMAN
Doctor, please. She's burning.

Elijah looks overwhelmed but follows.

INT. CLINIC - DAY

Elijah examines the baby - HIGH FEVER. He works efficiently.

ELIJAH
She needs antibiotics. I think it's pneumonia.

He administers treatment. The mother watches, grateful.

EXT. KOYUKUK VILLAGE - DAY

MAGGIE
Nearest hospital is 250 miles. You are the specialist now.

ELIJAH
I left Boston for this?

MAGGIE
And now you're here. They need you more than Mass General ever did.

TITLE CARD: THE LAST FRONTIER

FADE OUT.
"""


async def demo():
    """Run the demonstration."""
    print("="*70)
    print("CoverageIQ Day 3 - Coverage Generation Demo")
    print("="*70)
    print(f"Time: {datetime.now()}")
    print()
    
    # Check API key
    if not os.getenv("MOONSHOT_API_KEY"):
        print("⚠ MOONSHOT_API_KEY not set")
        print("Set it with: export MOONSHOT_API_KEY='your-key'")
        print("\nRunning in DEMO MODE (no actual API calls)")
        print()
    
    # Step 1: Show prompt template
    print("STEP 1: Generating TV Pilot Coverage Prompt")
    print("-"*70)
    
    prompt = build_full_prompt(depth="quick", genre="drama")
    print(f"Prompt length: {len(prompt)} characters")
    print(f"\nFirst 800 characters:")
    print(prompt[:800])
    print("\n...")
    print(f"\n✓ Prompt generated for genre: drama, depth: quick")
    print()
    
    # Step 2: Show API client
    print("STEP 2: Moonshot API Client")
    print("-"*70)
    
    try:
        client = get_moonshot_client()
        print(f"✓ Client initialized")
        print(f"  Default model: {client.DEFAULT_MODEL}")
        print(f"  Temperature: {client.DEFAULT_TEMPERATURE}")
        print(f"  Max tokens: {client.DEFAULT_MAX_TOKENS}")
        print()
    except Exception as e:
        print(f"⚠ Client initialization: {e}")
        print()
    
    # Step 3: Show analysis pipeline
    print("STEP 3: Analysis Pipeline")
    print("-"*70)
    
    pipeline = AnalysisPipeline()
    print(f"✓ Pipeline initialized")
    print(f"  Script length: {len(SAMPLE_SCRIPT)} characters")
    print(f"  Estimated tokens: ~{len(SAMPLE_SCRIPT) // 4}")
    print()
    
    # Step 4: Run analysis (if API key available)
    if os.getenv("MOONSHOT_API_KEY"):
        print("STEP 4: Running Analysis")
        print("-"*70)
        print("Analyzing script with Kimi K2.5...")
        print("(This may take 1-2 minutes)")
        print()
        
        try:
            result = await pipeline.analyze_script(
                script_text=SAMPLE_SCRIPT,
                report_id="demo-report-001",
                script_id="demo-script-001",
                genre="drama",
                analysis_depth="quick"
            )
            
            print("✓ Analysis complete!")
            print()
            
            # Display results
            print("RESULTS:")
            print("-"*70)
            print(f"\nLOGLINE:")
            print(f"  {result.get('logline', 'N/A')[:150]}...")
            
            print(f"\nSUBSCORES:")
            subscores = result.get("subscores", {})
            for category in ["concept", "character", "structure", "dialogue", "market"]:
                data = subscores.get(category, {})
                score = data.get("score", 0) if isinstance(data, dict) else data
                print(f"  {category.capitalize():12} {score}/10")
            
            print(f"\nTOTAL SCORE: {result.get('total_score', 0)}/50")
            print(f"RECOMMENDATION: {result.get('recommendation', 'N/A')}")
            
            print(f"\nSTRENGTHS ({len(result.get('strengths', []))}):")
            for i, s in enumerate(result.get('strengths', [])[:3], 1):
                print(f"  {i}. {s[:80]}...")
            
            print(f"\nWEAKNESSES ({len(result.get('weaknesses', []))}):")
            for i, w in enumerate(result.get('weaknesses', [])[:3], 1):
                print(f"  {i}. {w[:80]}...")
            
            # Check for series engine
            series_engine = result.get("series_engine", {})
            if series_engine:
                print(f"\nSERIES ENGINE:")
                desc = series_engine.get("engine_description", "N/A")
                print(f"  {desc[:150]}...")
            
            # Evidence quotes
            quotes = result.get("evidence_quotes", [])
            print(f"\nEVIDENCE QUOTES: {len(quotes)}")
            for q in quotes[:2]:
                print(f"  p.{q.get('page', 'N/A')}: \"{q.get('quote', 'N/A')[:50]}...\"")
            
            # Save full output
            output_file = "demo_coverage_result.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n✓ Full results saved to: {output_file}")
            
        except Exception as e:
            print(f"✗ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("STEP 4: Analysis (SKIPPED - no API key)")
        print("-"*70)
        print("To run actual analysis:")
        print("  1. Get API key from https://platform.moonshot.cn/")
        print("  2. Export MOONSHOT_API_KEY='your-key'")
        print("  3. Run this script again")
        print()
    
    print()
    print("="*70)
    print("Demo Complete")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(demo())