"""Prompt templates for TV pilot coverage generation.

These prompts are designed for Kimi K2.5 and optimized for TV pilot analysis.
The key focus is on the SERIES ENGINE - the repeatable conflict/structure that
will sustain a show for 5+ seasons.

All prompts use structured JSON output for consistent parsing.
"""

# Base system context that applies to all TV pilot analysis
TV_PILOT_SYSTEM_CONTEXT = """You are an expert TV development executive with 20+ years of experience at major networks and streaming platforms (HBO, Netflix, FX, AMC). You've read thousands of TV pilots and know what makes a series sustainable.

IMPORTANT: Respond in English only. Do not use any other languages in your analysis.

Your job is to provide professional script coverage that helps producers and writers understand:
1. Does this pilot work as a standalone episode?
2. Does it establish a SERIES ENGINE that can generate 5+ seasons of stories?
3. Are the characters compelling enough to sustain long-term viewing?

TV PILOT STRUCTURE NOTES:
- TV pilots are NOT 3-act films - they have their own structure
- A great pilot must: establish world, introduce core cast, deliver a satisfying episode, AND set up ongoing series potential
- The SERIES ENGINE is critical: what recurring conflicts, situations, or dynamics will fuel multiple seasons?
- Consider: Is this a premise pilot (one-time setup) or a template pilot (episode 0 that sets the weekly pattern)?

EVIDENCE REQUIREMENTS:
- Support all claims with specific quotes from the script
- Quotes should be 1-2 lines maximum
- Always include page references (p.XX format)
- Format: "Quote" (p.XX) - brief context
"""


# Main TV pilot coverage prompt - generates the full structured report
TV_PILOT_COVERAGE_PROMPT = """Analyze the following TV pilot script and provide comprehensive coverage. Focus heavily on series sustainability and the series engine.

OUTPUT FORMAT - Return valid JSON with this exact structure:
{
    "logline": "1-2 sentence hook describing the premise + protagonist + stakes",
    "synopsis": "Concise 1-page summary of the pilot's plot and key beats",
    "overall_comments": "3-5 paragraph narrative assessment of the pilot's quality, commercial potential, and standout elements",
    
    "strengths": [
        "Strength description with specific evidence",
        "Another strength with evidence"
    ],
    
    "weaknesses": [
        "Weakness description with specific evidence", 
        "Another weakness with evidence"
    ],
    
    "character_analysis": {
        "protagonist": {
            "name": "Character name",
            "assessment": "Analysis of protagonist's appeal, complexity, and actor bait",
            "series_runway": "How will this character sustain interest over 5+ seasons? What journey is possible?"
        },
        "supporting_cast": {
            "assessment": "Analysis of the ensemble - depth, diversity of voices, relationship dynamics",
            "standouts": ["Any standout supporting characters"],
            "concerns": ["Any weak or underdeveloped characters"]
        },
        "character_dynamics": "Analysis of core relationships and how they'll generate ongoing conflict"
    },
    
    "structure_analysis": {
        "pilot_type": "Premise pilot vs Template pilot - which is this and is it the right choice?",
        "act_breaks": "How does the pilot structure its acts? Are the breaks effective?",
        "pacing": "Assessment of pacing - does it drag or rush?",
        "cold_open": "Assessment of the teaser/cold open",
        "act_one": "What happens in Act 1, does it establish premise effectively?",
        "act_two": "What happens in Act 2, how does it complicate?",
        "act_three": "What happens in Act 3, does it deliver satisfying conclusion while opening series?",
        "tag": "Assessment of the final scene/tag if present"
    },
    
    "series_engine": {
        "engine_description": "What is the repeatable conflict/situation that will generate 50+ episodes?",
        "season_one_stories": "What storylines does the pilot set up for Season 1?",
        "multi_season_potential": "How does the engine expand beyond Season 1? Seasons 2-5 potential?",
        "episode_types": "What types of episodes can this series generate weekly?",
        "franchise_potential": "Spin-off potential, format adaptations, etc.",
        "concerns": "Any concerns about the engine's sustainability?"
    },
    
    "market_positioning": {
        "genre": "Primary and secondary genres",
        "tone": "Tone description",
        "comparable_series": ["3-5 comparable successful series with brief explanation"],
        "target_network": "Ideal network/platform (HBO, Netflix, FX, broadcast, etc.)",
        "target_audience": "Who will watch this? Demographics and psychographics",
        "market_timing": "Is this timely or timeless? Why now?",
        "castability": "How castable are the roles? Any obvious casting directions?",
        "production_considerations": "Any budget, location, or production concerns?"
    },
    
    "subscores": {
        "concept": {
            "score": 0,
            "rationale": "1-2 sentence rationale for Concept & Premise score"
        },
        "character": {
            "score": 0,
            "rationale": "1-2 sentence rationale for Character & Dialogue score"
        },
        "structure": {
            "score": 0,
            "rationale": "1-2 sentence rationale for Structure & Pacing score"
        },
        "dialogue": {
            "score": 0,
            "rationale": "1-2 sentence rationale for Dialogue score"
        },
        "market": {
            "score": 0,
            "rationale": "1-2 sentence rationale for Market Viability score"
        }
    },
    "total_score": 0,
    "recommendation": "Pass/Consider/Recommend",
    "recommendation_rationale": "Why this recommendation? What would need to change for a higher rating?",
    
    "evidence_quotes": [
        {
            "quote": "Exact quote from script, max 2 lines",
            "page": 0,
            "context": "What this quote demonstrates (strength, weakness, character trait, etc.)"
        }
    ]
}

SCORING RUBRIC (score each /10):
- CONCEPT: Is the premise fresh, compelling, and series-worthy? Does it have a strong hook?
- CHARACTER: Are the characters complex, distinct, and worthy of long-term investment? Is dialogue sharp and character-specific?
- STRUCTURE: Does the pilot structure serve the story? Are act breaks effective? Is pacing appropriate?
- DIALOGUE: Is the dialogue sharp, character-specific, and free of exposition dumps?
- MARKET: Is this commercially viable? Does it have a clear home and audience? Is timing right?

RECOMMENDATION THRESHOLDS (/50 total):
- RECOMMEND (38-50): Strong contender, pursue immediately
- CONSIDER (25-37): Shows promise with reservations  
- PASS (0-24): Not ready for consideration

CRITICAL: Provide specific evidence quotes with page numbers for all major claims. Support your scores with script references.
"""


# Quick analysis prompt for faster, less detailed coverage
QUICK_TV_PILOT_PROMPT = """Provide a quick analysis of this TV pilot script. Focus on the essentials: does the pilot work and does it have series potential?

OUTPUT FORMAT - Return valid JSON:
{
    "logline": "1-2 sentence hook",
    "brief_assessment": "2-3 paragraph quick take on the pilot's strengths and weaknesses",
    
    "strengths": ["2-3 key strengths with evidence"],
    "weaknesses": ["2-3 key concerns with evidence"],
    
    "series_engine": {
        "description": "What drives the series?",
        "sustainability_rating": "High/Medium/Low - can this run 5+ seasons?",
        "concerns": ["Any sustainability concerns"]
    },
    
    "character_assessment": "Quick take on protagonist and supporting cast",
    
    "market_notes": "Where does this belong and who watches it?",
    
    "subscores": {
        "concept": {"score": 0, "note": "Brief note"},
        "character": {"score": 0, "note": "Brief note"},
        "structure": {"score": 0, "note": "Brief note"},
        "dialogue": {"score": 0, "note": "Brief note"},
        "market": {"score": 0, "note": "Brief note"}
    },
    "total_score": 0,
    "recommendation": "Pass/Consider/Recommend",
    "quick_verdict": "One sentence bottom line",
    
    "evidence_quotes": [
        {"quote": "Quote", "page": 0, "context": "Why this matters"}
    ]
}

Same scoring rubric as full analysis. Be concise but specific.
"""


# Deep analysis prompt for more thorough coverage (optional premium feature)
DEEP_TV_PILOT_PROMPT = """Provide comprehensive deep-dive coverage of this TV pilot script. This is for internal development purposes - be thorough and critical.

OUTPUT FORMAT - Return valid JSON with additional deep-dive sections:
{
    "logline": "1-2 sentence hook",
    "synopsis": "Full synopsis",
    "overall_comments": "Extended 5-7 paragraph assessment",
    
    "strengths": ["Detailed strengths with evidence"],
    "weaknesses": ["Detailed weaknesses with evidence"],
    
    "character_analysis": {
        "protagonist": {
            "name": "Name",
            "depth_analysis": "Multi-paragraph analysis of protagonist's psychology, arc, and appeal",
            "dialogue_voice": "How does their dialogue reveal character?",
            "series_runway": "Specific episode ideas for Seasons 1-3",
            "casting_notes": "What type of actor is needed?"
        },
        "supporting_cast": {
            "each_character": [
                {"name": "Name", "role": "Function in story", "strengths": [], "concerns": []}
            ],
            "ensemble_dynamics": "How do they interact and create ongoing tension?",
            "relationship_map": "Map the key relationships"
        },
        "character_arcs": "What arcs does the pilot establish for Season 1?"
    },
    
    "structure_deep_dive": {
        "pilot_type_analysis": "Deep analysis of premise vs template choice",
        "act_by_act": {
            "cold_open": {"content": "What happens", "function": "What it establishes", "effectiveness": "How well it works"},
            "act_one": {"content": "", "function": "", "effectiveness": ""},
            "act_two": {"content": "", "function": "", "effectiveness": ""},
            "act_three": {"content": "", "function": "", "effectiveness": ""},
            "tag": {"content": "", "function": "", "effectiveness": ""}
        },
        "plot_mechanics": "How well does the A-story work? B-story? C-story?",
        "pacing_analysis": "Scene-by-scene pacing assessment",
        "structural_concerns": ["Specific structural issues"]
    },
    
    "series_engine_deep_dive": {
        "engine_description": "Detailed description",
        "story_generation": "How exactly will this generate 100+ episodes?",
        "season_breakdown": {
            "season_one": "Specific storylines and arc",
            "season_two": "Where does it go in S2?",
            "seasons_three_to_five": "Long-term trajectory"
        },
        "episode_formats": "What are the repeatable episode types?",
        "franchise_expansion": "Spin-offs, extensions, format potential",
        "engine_risks": ["What could break the engine?"]
    },
    
    "world_building": {
        "setting_assessment": "How well is the world established?",
        "rules": "Are the rules clear?",
        "expansion_potential": "How can the world grow?"
    },
    
    "market_analysis": {
        "comparables_detailed": [
            {"title": "Show", "similarities": "", "differences": "", "performance": "How it performed"}
        ],
        "positioning": "Where does this fit in the current landscape?",
        "audience_analysis": "Detailed audience breakdown",
        "distribution_strategy": "How should this be released?",
        "commercial_potential": "Revenue potential assessment"
    },
    
    "production_notes": {
        "budget_estimate": "Low/Medium/High with rationale",
        "locations": "Key location requirements",
        "cast_size": "Number of series regulars needed",
        "production_challenges": ["Specific challenges"],
        "cost_saving_opportunities": ["Where to save money"]
    },
    
    "revision_notes": {
        "priority_changes": ["Changes that would most improve the pilot"],
        "development_suggestions": "Broader suggestions for the series",
        "questions": ["Questions the writer should answer"]
    },
    
    "subscores": {
        "concept": {"score": 0, "rationale": "Detailed rationale"},
        "character": {"score": 0, "rationale": "Detailed rationale"},
        "structure": {"score": 0, "rationale": "Detailed rationale"},
        "dialogue": {"score": 0, "rationale": "Detailed rationale"},
        "market": {"score": 0, "rationale": "Detailed rationale"}
    },
    "total_score": 0,
    "recommendation": "Pass/Consider/Recommend",
    "confidence": "High/Medium/Low - how confident are you in this assessment?",
    "final_assessment": "Overall verdict and next steps",
    
    "evidence_quotes": [
        {"quote": "Quote", "page": 0, "context": "Significance"}
    ]
}

Same scoring rubric. Be exhaustive and critical - this is for development.
"""


def get_prompt_for_depth(depth: str) -> str:
    """Get the appropriate prompt for the analysis depth.
    
    Args:
        depth: One of 'quick', 'standard', or 'deep'
        
    Returns:
        The prompt string for the requested depth
    """
    prompts = {
        "quick": QUICK_TV_PILOT_PROMPT,
        "standard": TV_PILOT_COVERAGE_PROMPT,
        "deep": DEEP_TV_PILOT_PROMPT
    }
    
    return prompts.get(depth, TV_PILOT_COVERAGE_PROMPT)


# Genre-specific additions can be appended to base prompts
GENRE_CONTEXTS = {
    "drama": "Focus on emotional authenticity, character complexity, and thematic depth.",
    "comedy": "Focus on comedic engine, joke density, character voices, and rewatchability.",
    "thriller": "Focus on suspense construction, stakes escalation, and hook sustainability.",
    "sci-fi": "Focus on world-building clarity, concept exploration, and sci-fi concept sustainability.",
    "fantasy": "Focus on mythology building, magic system sustainability, and epic scope management.",
    "crime": "Focus on case-of-the-week vs serialized balance, procedural mechanics, and moral complexity.",
    "horror": "Focus on scare sustainability, monster/villain longevity, and dread maintenance.",
    "period": "Focus on historical authenticity, modern relevance, and period production considerations.",
    "docudrama": "Focus on truth vs drama balance, access issues, and rights considerations.",
    "procedural": "Focus on procedural mechanics, case variety, and formula sustainability."
}


def get_genre_context(genre: str) -> str:
    """Get genre-specific analysis context.
    
    Args:
        genre: Genre name
        
    Returns:
        Context string for that genre
    """
    return GENRE_CONTEXTS.get(genre.lower(), "")


# Helper to combine prompts with genre context
def build_full_prompt(depth: str = "standard", genre: str = None) -> str:
    """Build the complete prompt for a coverage request.
    
    Args:
        depth: Analysis depth ('quick', 'standard', 'deep')
        genre: Optional genre for specific context
        
    Returns:
        Complete prompt string
    """
    base_prompt = get_prompt_for_depth(depth)
    
    if genre:
        genre_context = get_genre_context(genre)
        if genre_context:
            base_prompt = f"""GENRE: {genre.upper()}

GENRE-SPECIFIC NOTES: {genre_context}

{base_prompt}"""
    
    return base_prompt