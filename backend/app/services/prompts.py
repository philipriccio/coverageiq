"""Prompt templates for TV pilot coverage generation."""

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
- Format: \"Quote\" (p.XX) - brief context

MANDATE CHECKLIST:
- Evaluate each criterion for the Hawco Productions mandate:
- canadian_content: Is the story, setting, or characters Canadian or adaptable to Canadian co-production?
- star_role: Does it have a compelling lead role that would attract A-list Canadian or international talent?
- intl_copro: Is the format, story, or scope suitable for international co-production financing?
- budget_feasible: Is the production scope realistic for a Canadian mid-range budget (e.g., $2-5M/episode)?
"""

TV_PILOT_COVERAGE_PROMPT = """Analyze the following TV pilot script and provide comprehensive coverage. Focus heavily on series sustainability and the series engine.

OUTPUT FORMAT - Return valid JSON with this exact structure:
{
    "logline": "1-2 sentence hook describing the premise + protagonist + stakes",
    "synopsis": "Concise 1-page summary of the pilot's plot and key beats",
    "overall_comments": "3-5 paragraph narrative assessment of the pilot's quality, commercial potential, and standout elements",
    "strengths": ["Strength description with specific evidence"],
    "weaknesses": ["Weakness description with specific evidence"],
    "character_analysis": {
        "protagonist": {
            "name": "Character name",
            "assessment": "Analysis of protagonist's appeal, complexity, and actor bait",
            "series_runway": "How will this character sustain interest over 5+ seasons?"
        },
        "supporting_cast": {
            "assessment": "Analysis of the ensemble",
            "standouts": ["Any standout supporting characters"],
            "concerns": ["Any weak or underdeveloped characters"]
        },
        "character_dynamics": "Analysis of core relationships and how they'll generate ongoing conflict"
    },
    "structure_analysis": {
        "pilot_type": "Premise pilot vs Template pilot",
        "act_breaks": "How the pilot structures its acts",
        "pacing": "Assessment of pacing",
        "cold_open": "Assessment of the teaser/cold open",
        "act_one": "Act 1 analysis",
        "act_two": "Act 2 analysis",
        "act_three": "Act 3 analysis",
        "tag": "Assessment of final scene/tag"
    },
    "series_engine": {
        "engine_description": "What is the repeatable conflict/situation that will generate 50+ episodes?",
        "season_one_stories": "What storylines does the pilot set up for Season 1?",
        "multi_season_potential": "How does the engine expand beyond Season 1?",
        "episode_types": "What types of episodes can this series generate weekly?",
        "franchise_potential": "Spin-off potential, format adaptations, etc.",
        "concerns": "Any concerns about the engine's sustainability?"
    },
    "market_positioning": {
        "genre": "Primary and secondary genres",
        "tone": "Tone description",
        "comparable_series": ["3-5 comparable successful series with brief explanation"],
        "target_network": "Ideal network/platform",
        "target_audience": "Who will watch this?",
        "market_timing": "Is this timely or timeless?",
        "castability": "How castable are the roles?",
        "production_considerations": "Any budget, location, or production concerns?"
    },
    "subscores": {
        "concept": {"score": 0, "rationale": "Rationale"},
        "character": {"score": 0, "rationale": "Rationale"},
        "structure": {"score": 0, "rationale": "Rationale"},
        "dialogue": {"score": 0, "rationale": "Rationale"},
        "market": {"score": 0, "rationale": "Rationale"}
    },
    "mandate_checklist": {
        "canadian_content": {"result": true, "rationale": "Brief rationale"},
        "star_role": {"result": true, "rationale": "Brief rationale"},
        "intl_copro": {"result": true, "rationale": "Brief rationale"},
        "budget_feasible": {"result": true, "rationale": "Brief rationale"}
    },
    "total_score": 0,
    "recommendation": "Pass/Consider/Recommend",
    "recommendation_rationale": "Why this recommendation?",
    "evidence_quotes": [{"quote": "Exact quote from script", "page": 0, "context": "What this demonstrates"}]
}

SCORING RUBRIC:
- CONCEPT: Is the premise fresh, compelling, and series-worthy?
- CHARACTER: Are the characters complex, distinct, and worthy of long-term investment?
- STRUCTURE: Does the pilot structure serve the story?
- DIALOGUE: Is the dialogue sharp and character-specific?
- MARKET: Is this commercially viable with a clear home and audience?

RECOMMENDATION THRESHOLDS:
- RECOMMEND (38-50)
- CONSIDER (25-37)
- PASS (0-24)
"""

QUICK_TV_PILOT_PROMPT = """Provide a quick analysis of this TV pilot script. Focus on the essentials: does the pilot work and does it have series potential?

Return valid JSON with these keys:
logline, synopsis, overall_comments, strengths, weaknesses, character_analysis, structure_analysis, market_positioning, subscores, mandate_checklist, total_score, recommendation, evidence_quotes.

Keep it concise but still return the full schema. Use shorter values where needed.
"""

DEEP_TV_PILOT_PROMPT = """Provide comprehensive deep-dive coverage of this TV pilot script. Be thorough, development-focused, and highly specific.

Return the same JSON schema as standard coverage, including mandate_checklist, but with richer detail in every section.
"""

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
    "procedural": "Focus on procedural mechanics, case variety, and formula sustainability.",
}


def get_prompt_for_depth(depth: str) -> str:
    return {
        "quick": QUICK_TV_PILOT_PROMPT,
        "standard": TV_PILOT_COVERAGE_PROMPT,
        "deep": DEEP_TV_PILOT_PROMPT,
    }.get(depth, TV_PILOT_COVERAGE_PROMPT)


def get_genre_context(genre: str) -> str:
    return GENRE_CONTEXTS.get((genre or "").lower(), "")


def build_prompt_context(
    depth: str = "standard",
    genre: str | None = None,
    comps: list[str] | None = None,
    domain_knowledge_entries: list[str] | None = None,
    example_coverages: list[str] | None = None,
) -> str:
    base_prompt = get_prompt_for_depth(depth)
    sections: list[str] = []

    if genre:
        sections.append(f"GENRE: {genre.upper()}")
        genre_context = get_genre_context(genre)
        if genre_context:
            sections.append(f"GENRE-SPECIFIC NOTES: {genre_context}")

    if comps:
        sections.append(
            "COMPARABLE SERIES: " + ", ".join([comp.strip() for comp in comps if comp and comp.strip()])
        )

    knowledge = [entry.strip() for entry in (domain_knowledge_entries or []) if entry and entry.strip()]
    if knowledge:
        sections.append("DOMAIN EXPERTISE:\n" + "\n\n".join(f"- {entry}" for entry in knowledge))

    examples = [entry.strip() for entry in (example_coverages or []) if entry and entry.strip()]
    if examples:
        rendered_examples = []
        for example in examples[:2]:
            rendered_examples.append(
                "Here is an example of excellent coverage for this genre. Match this quality.\n" + example
            )
        sections.append("EXAMPLE COVERAGE (match this quality):\n\n" + "\n\n---\n\n".join(rendered_examples))

    sections.append("Now analyze the following script...")
    sections.append(base_prompt)
    return "\n\n".join(sections)
