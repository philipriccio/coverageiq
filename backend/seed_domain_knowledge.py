#!/usr/bin/env python3
"""
Seed script: CoverageIQ Domain Knowledge
Benchmark TV pilots + Philip Riccio calibration examples

Run against production DB:
    DATABASE_URL=postgresql+asyncpg://... python seed_domain_knowledge.py

Or run locally:
    cd backend && python seed_domain_knowledge.py
"""

import asyncio
import os
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# ─── DOMAIN KNOWLEDGE ENTRIES ────────────────────────────────────────────────

ENTRIES = [

    # ─── GENERAL FRAMEWORK ───────────────────────────────────────────────────

    {
        "category": "general",
        "content": """SCORING FRAMEWORK — PHILIP RICCIO CALIBRATION

You are calibrated to the taste of Philip Riccio, an experienced Canadian development executive.

SCORE ANCHORS (calibrated to Philip's actual scoring history):
- 1–10: Clear pass. Fundamental problems. Not ready for development.
- 11–20: Pass. Professionally written but not compelling. Generic or lacks series engine.
- 21–28: Pass. Has elements that work but significant problems. Scripts in this range include POV (28), Richard (24), Maniac Pervert (26).
- 29–35: Consider. Enough merit for a conversation. Problems are fixable. Scripts in this range include Sara Knox (33), The Legion (35), Book of Ruth (33).
- 36–42: Strong Consider / Soft Recommend. Genuinely good. Rarely seen. Scripts in this range include Sterling (36), The Great Lakes (37 — still passed).
- 43–50: Recommend. Exceptional. Approaches The Sopranos pilot level. Almost never given.

KEY RULE: The average unproduced Canadian TV pilot scores 20–30. A 35+ means it's meaningfully better than most submissions. A 40+ is exceptional. A 43+ is world-class.

WHAT PHILIP VALUES:
- Originality — does this show need to exist?
- Series engine — what generates 5+ seasons of story?
- Star vehicle — is the lead role something a great actor would want?
- Sharp, character-specific dialogue
- Commercial viability for Canadian broadcasters (CBC, Crave, Showcase, Bell Media, Rogers)
- Clean structure — every scene earns its place

WHAT KILLS A SCRIPT FOR PHILIP:
- Generic premise — "this is just [existing show] in Canada"
- Weak series engine — one premise, no ongoing engine
- Lead character who isn't a star vehicle
- Flat dialogue — characters who sound the same
- Act 3 collapse — most Canadian pilots fall apart in Act 3
- Budget mismatch — the story doesn't fit the Canadian production reality

MANDATE CHECKLIST (Hawco Productions):
- canadian_content: Canadian story/setting or adaptable to Canadian co-production?
- star_role: Lead role attractive to A-list Canadian or international talent?
- intl_copro: Format/story suitable for international co-production?
- budget_feasible: Production scope realistic for $2–5M/episode?
""",
    },

    # ─── PRESTIGE ONE-HOUR DRAMA ─────────────────────────────────────────────

    {
        "category": "drama",
        "content": """BENCHMARK: The Sopranos Pilot ("Pilot", 1999 — David Chase)
CATEGORY: One-Hour Drama (Prestige)
SCORE EQUIVALENT: 49/50 (RECOMMEND — the gold standard)

WHY THIS IS A BENCHMARK:
- The series engine is defined in the first scene: Tony Soprano is a man caught between two families — his mob family and his actual family — and the gap between them is what generates every story.
- Tony is the ultimate star vehicle: complex, violent, funny, vulnerable. A great actor would kill for this role.
- The pilot establishes tone (dark comedy + genuine menace) instantly and never wavers.
- The therapy device is a masterstroke: it gives Tony (and the audience) a space to process events that would otherwise be internalized. It also creates a recurring weekly structure.
- The dialogue is character-specific. Tony sounds like Tony. Carmela sounds like Carmela. Nobody is interchangeable.
- The pilot delivers a complete episode AND sets up a series simultaneously — the ducks leave, Tony has a panic attack, he sees a therapist. Simple premise, infinite engine.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A series engine that is simple enough to state in one sentence but generates infinite variations
- A lead character whose internal contradiction IS the show's engine
- Dialogue where every character sounds distinct and specific

PHILIP'S NOTE: This is the benchmark for one-hour Canadian drama. If you're not sure a drama script should score 40+, ask yourself: does it have a Tony Soprano? Does it have an engine as clean as "mob boss sees a therapist"? If not, recalibrate down.
""",
    },

    {
        "category": "drama",
        "content": """BENCHMARK: Breaking Bad Pilot ("Pilot", 2008 — Vince Gilligan)
CATEGORY: One-Hour Drama (Prestige)
SCORE EQUIVALENT: 48/50 (RECOMMEND — exceptional)

WHY THIS IS A BENCHMARK:
- The premise is a perfect pitch: a meek high school chemistry teacher diagnosed with terminal cancer decides to cook meth to secure his family's future. Every word of that logline earns its place.
- Walter White's transformation arc is the entire series engine. We watch a good man choose to become a bad man, step by step. The pilot gives us the Before state so completely that we know exactly what we're watching him lose.
- The cold open is one of the great pilots cold opens: Walter in tighty-whiteys holding a gun in the desert, RV crashing behind him, sirens in the distance. We have no idea what's happening but we're in.
- Structure is immaculate: the diagnosis scene is the pivot point of the entire series. Everything before it is one man. Everything after is another.
- The pilot delivers on its premise immediately — Walter cooks, Walter kills. No stalling.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A protagonist whose internal change IS the series engine — not a static hero solving external problems
- A premise that can be stated in 10 words and generates 5+ seasons of story
- An opening sequence that creates a question the audience cannot stop wanting answered

SERIES ENGINE: "How far will Walter White go, and what will it cost him?"
""",
    },

    {
        "category": "drama",
        "content": """BENCHMARK: The Wire Pilot ("The Target", 2002 — David Simon)
CATEGORY: One-Hour Drama (Prestige) / Crime Procedural
SCORE EQUIVALENT: 48/50 (RECOMMEND — exceptional)

WHY THIS IS A BENCHMARK:
- The Wire operates on a rare level: it uses the crime procedural form to examine institutional failure in American society. The drug war, the police department, the city government, the schools — each season is a different institution.
- The pilot establishes this ambition immediately: the opening scene (D'Angelo explaining chess to the corner boys) is a masterclass in character, theme, and series engine simultaneously.
- Every character — cops and criminals — is written with equal complexity. No one is purely good or evil. This is what separates it from procedurals.
- The series engine is structural: each case will expose a different failure in the system. It's a show with infinite engine because the system keeps failing.
- The dialogue is specific and authentic. Simon researched this world. It shows.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A premise that operates on both the personal AND systemic level simultaneously
- Characters on both sides of the conflict written with equal depth and specificity
- A world specific enough to feel discovered, not invented

SERIES ENGINE: "An institutional system (police, schools, docks, politics, media) is failing — here's what it looks like from inside."
""",
    },

    {
        "category": "drama",
        "content": """BENCHMARK: Mad Men Pilot ("Smoke Gets in Your Eyes", 2007 — Matthew Weiner)
CATEGORY: One-Hour Drama (Prestige / Period)
SCORE EQUIVALENT: 47/50 (RECOMMEND — exceptional)

WHY THIS IS A BENCHMARK:
- Don Draper is defined entirely through what he conceals. We don't know who he is. That mystery is the series engine.
- The period setting (1960 Madison Avenue ad world) is not decoration — it's the point. The show is about the lies America told itself, and Don Draper IS that lie made flesh.
- The pilot's central dramatic question ("Who is Don Draper?") takes the entire series to answer. That's rare. Most pilots exhaust their mystery in the episode.
- The pilot delivers a complete, self-contained episode (the Lucky Strike campaign) while embedding a mystery that runs 7 seasons.
- The writing trusts the audience. The pilot doesn't explain Don's secret — it plants evidence and lets the audience lean forward.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A protagonist whose mystery is the series engine — not just a personality, but a secret or contradiction that takes seasons to resolve
- A setting that is itself a character with thematic relevance
- The discipline to withhold information and trust the audience

SERIES ENGINE: "Who is Don Draper really, and what has he traded to become this man?"
""",
    },

    {
        "category": "drama",
        "content": """BENCHMARK: Succession Pilot ("Celebration", 2018 — Jesse Armstrong)
CATEGORY: One-Hour Drama (Prestige / Soapy Drama)
SCORE EQUIVALENT: 47/50 (RECOMMEND — exceptional)

WHY THIS IS A BENCHMARK:
- The series engine is pure: when will Logan Roy die, and which child will inherit the empire? Every scene in every episode connects back to this question.
- The pilot establishes Logan's power and his contempt for his children in one birthday dinner. You understand the entire show in the first episode.
- The dialogue is exceptional — fast, overlapping, specific to class and character. "We're not doing anything wrong, we're just winning" is a thesis statement.
- The characters are deeply unlikable but impossible to look away from. That's a specific skill.
- The show is a tragedy structured as a comedy. The pilot establishes both registers simultaneously.
- Every character wants something. Every character is blocked by Logan. That simple structure generates five seasons.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A central power structure that creates conflict among every character at all times
- Characters who are flawed enough to be fascinating but human enough to be tragic
- Dialogue that reveals class, status, and character simultaneously

SERIES ENGINE: "Who gets Waystar Royco when Logan dies — and what will the Roy children do to each other to get it?"
""",
    },

    {
        "category": "drama",
        "content": """BENCHMARK: Six Feet Under Pilot ("Pilot", 2001 — Alan Ball)
CATEGORY: One-Hour Drama (Prestige / Family Drama)
SCORE EQUIVALENT: 46/50 (RECOMMEND — exceptional)

WHY THIS IS A BENCHMARK:
- The series engine is elegant: a family runs a funeral home, so every episode deals with death — and the Fisher family's own inability to process grief.
- The cold open — Nathaniel Fisher Sr. dying while driving — is one of the great pilot cold opens. It gives the show its engine (the family business) and its theme (death) in one sequence.
- The dead character appearing to the living is a masterstroke of form: it gives the show a way to externalize internal states and keep the patriarch present.
- Every Fisher family member has a specific wound, a specific way of avoiding it, and a specific way the funeral home work forces them to confront it. That's clean character architecture.
- The show is dark without being nihilistic. The pilot establishes that death makes life matter — and that the Fishers are too scared to live.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A setting that forces characters to confront the show's central theme week after week
- A family structure where every member's flaw connects to the others
- A formal device (like the ghost) that earns its place thematically, not just visually

SERIES ENGINE: "The Fisher family runs a funeral home — can they handle other people's deaths when they can't handle their own lives?"
""",
    },

    # ─── BROADCAST ONE-HOUR DRAMA ─────────────────────────────────────────────

    {
        "category": "drama",
        "content": """BENCHMARK: The Good Wife Pilot ("Pilot", 2009 — Robert King & Michelle King)
CATEGORY: One-Hour Drama (Broadcast / Procedural Hybrid)
SCORE EQUIVALENT: 44/50 (RECOMMEND — exceptional for broadcast)

WHY THIS IS A BENCHMARK:
- The premise is a perfect engine for broadcast: a disgraced politician's wife returns to law after 13 years to rebuild her own identity. Every episode, she uses the case of the week to process her own humiliation and comeback.
- Alicia Florrick is one of the great broadcast TV characters: intelligent, controlled, furious, and determined not to let anyone see how much she's been damaged. That's a star vehicle.
- The pilot establishes all three levels of the show: (1) the case-of-the-week procedural engine, (2) the serialized arc of Alicia rebuilding her career and life, (3) the political/personal drama of her husband's scandal.
- The pilot works as a standalone episode while setting up years of story. That's the broadcast gold standard.
- The dialogue is sharp and the lead is a star vehicle from page one.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A procedural engine that connects thematically to the protagonist's personal arc
- A lead character whose public face and private reality create constant dramatic tension
- A weekly case structure that generates multiple types of episodes

SERIES ENGINE: "A brilliant woman rebuilds her career and identity after her husband's scandal — one case at a time."
""",
    },

    {
        "category": "drama",
        "content": """BENCHMARK: Yellowstone Pilot ("Daybreak", 2018 — Taylor Sheridan)
CATEGORY: One-Hour Drama (Broadcast / Soapy Drama)
SCORE EQUIVALENT: 43/50 (RECOMMEND — powerful franchise engine)

WHY THIS IS A BENCHMARK:
- Taylor Sheridan builds a show around the oldest American conflict: who owns the land. The Dutton family ranch is caught between developers, a Native reservation, and a national park. That's three enemies generating infinite story.
- John Dutton is a star vehicle: a patriarch who does terrible things to protect what he loves. Kevin Costner wanted this role. That's the test.
- The pilot establishes the stakes immediately: the ranch will be taken if John doesn't fight. Every episode is about that fight.
- Sheridan writes action sequences that reveal character. Violence in Yellowstone means something.
- The franchise engine is proven: three spinoffs, four seasons. The concept scales.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A central conflict that is both timeless (land, legacy, power) and specific (this family, this place)
- A patriarch/matriarch figure who generates conflict for every other character
- A setting that IS a character — the ranch matters as much as the people on it

SERIES ENGINE: "The Dutton family will fight, lie, and kill to keep their Montana ranch — but the walls are closing in from every direction."
""",
    },

    # ─── WORKPLACE COMEDY (HALF-HOUR) ─────────────────────────────────────────

    {
        "category": "comedy",
        "content": """BENCHMARK: The Office (US) Pilot ("Pilot", 2005 — Greg Daniels / Ricky Gervais & Stephen Merchant)
CATEGORY: Workplace Comedy (Half-Hour)
SCORE EQUIVALENT: 46/50 (RECOMMEND — exceptional)

WHY THIS IS A BENCHMARK:
- The mockumentary format is the series engine: the camera is always present, which means every character is always performing their version of themselves for the documentary crew. That gap between performance and reality generates comedy and pathos simultaneously.
- Michael Scott is a case study in great comedic character design: he is desperate for love and respect, oblivious to why he doesn't get it, and occasionally — heartbreakingly — self-aware. That's infinite engine.
- The cold open (Michael pretending to fire Pam) establishes the tone, the character, and the comedic mechanics in four minutes.
- Every character has a specific relationship to the camera (Dwight plays it straight, Jim uses it as a confidant, Michael performs for it). That's sophisticated character architecture.
- The comedy comes from character, not situation. The situation (an office) is as mundane as possible. The comedy is entirely about who these people are.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A comedic setting where the humor comes from character, not just situation
- A central comedic figure whose flaw is specific, consistent, and generates comedy AND pathos
- A format device (mockumentary, canned laughter, narration) that earns its place and generates story

SERIES ENGINE: "A delusional regional manager tries to run a branch that everyone wishes would be shut down."
""",
    },

    {
        "category": "comedy",
        "content": """BENCHMARK: Schitt's Creek Pilot ("Our Cup Runneth Over", 2015 — Eugene Levy & Dan Levy)
CATEGORY: Comedy (Half-Hour) / Canadian
SCORE EQUIVALENT: 44/50 (RECOMMEND — exceptional Canadian comedy)

WHY THIS IS A BENCHMARK:
- The premise is the engine: wealthy family loses everything and must move to the small town they once bought as a joke. Every episode is about people who have never had to try, learning to try.
- The Rose family is all four comedic archetypes perfectly calibrated: Johnny (earnest straight man), Moira (theatrical narcissist), David (privileged millennial cynic), Alexis (vapid socialite with hidden depth). They generate infinite conflict with each other and with the town.
- The show is about kindness — this is rare and hard to execute. Schitt's Creek demonstrates you can make a comedy about people becoming better without being saccharine.
- The Canadian setting (a small-town motel) is specific and real. The show doesn't pretend to be American.
- For Canadian broadcasters: proof that an explicitly Canadian comedy can find massive international audiences when the premise is universal.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A fish-out-of-water premise that forces characters to confront what they've been hiding behind money/status
- An ensemble where every character's flaw creates comedy when in contact with every other character's flaw
- A comedic engine that generates growth — not just jokes, but actual human change

SERIES ENGINE: "A disgraced wealthy family learns to live in the one asset they have left — a small town they once bought as a joke."
PHILIP'S NOTE: The gold standard for what a Canadian half-hour comedy can be. If you're reading a Canadian comedy, this is what 44/50 looks like.
""",
    },

    {
        "category": "comedy",
        "content": """BENCHMARK: Abbott Elementary Pilot ("Pilot", 2021 — Quinta Brunson)
CATEGORY: Workplace Comedy (Half-Hour)
SCORE EQUIVALENT: 45/50 (RECOMMEND — exceptional modern workplace comedy)

WHY THIS IS A BENCHMARK:
- The mockumentary format reinvented for 2021: same mechanics as The Office but applied to an underfunded Philadelphia public school. The setting is specific, authentic, and has a point of view.
- Quinta Brunson's Janine Teagues is the rare comedic protagonist who is genuinely good — optimistic, dedicated, slightly delusional about her ability to fix everything. That's the engine: she will try and fail and try again.
- The ensemble is perfectly calibrated: every teacher is an archetype (the cynic, the veteran, the useless admin) but Brunson gives each one specific, non-generic traits.
- The pilot is funny AND has a moral dimension — it's about what happens to good people working in broken systems. That's a full show.
- The cold open (Janine trying to buy supplies and failing) establishes everything: the character, the setting, the problem, the tone.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- An optimistic protagonist whose optimism is both their superpower and their blind spot
- A setting that is itself a source of conflict (underfunded school = constant obstacle)
- Comedy that has a point of view — it's about something beyond just being funny

SERIES ENGINE: "A dedicated young teacher refuses to give up on her underfunded school despite a broken system, useless administration, and her own occasionally disastrous ideas."
""",
    },

    {
        "category": "comedy",
        "content": """BENCHMARK: Cheers Pilot ("Give Me a Ring Sometime", 1982 — Glen Charles & Les Charles)
CATEGORY: Workplace Comedy (Half-Hour)
SCORE EQUIVALENT: 46/50 (RECOMMEND — foundational sitcom benchmark)

WHY THIS IS A BENCHMARK:
- Cheers invented the template for the workplace sitcom: a location where people have to be together, a will-they-won't-they at the center, and an ensemble of archetypes who generate comedy through their specificity.
- The pilot establishes Sam and Diane in one scene. Their class difference (he's a bar owner, she's an intellectual), their mutual attraction, and their mutual irritation is the entire series engine.
- The bar itself is the series engine: it's a place where everybody knows your name. The setting IS the concept.
- Every character in the pilot is instantly legible: Coach (sweet, slow, lovable), Carla (sharp, caustic, overworked), Cliff and Norm (Greek chorus). No character is redundant.
- The pilot delivers laughs AND sets up 11 seasons of story. That's the broadcast half-hour gold standard.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A setting that IS the concept (the bar is the show's reason to exist)
- A will-they-won't-they engine that survives multiple seasons (Sam/Diane, then Sam/Rebecca)
- An ensemble where every character is an archetype but a SPECIFIC one — not the generic version

SERIES ENGINE: "A former Red Sox pitcher runs a bar in Boston. Everybody knows his name. Nobody knows his whole story."
""",
    },

    # ─── FAMILY COMEDY ────────────────────────────────────────────────────────

    {
        "category": "comedy",
        "content": """BENCHMARK: Arrested Development Pilot ("Pilot", 2003 — Mitchell Hurwitz)
CATEGORY: Family Comedy (Half-Hour)
SCORE EQUIVALENT: 46/50 (RECOMMEND — exceptional, dense, innovative)

WHY THIS IS A BENCHMARK:
- The series engine is pure comedy architecture: a normal son (Michael Bluth) is trapped by his insane, selfish family. The family needs him. He needs to escape. He will never escape.
- Every family member is a specific comedic archetype pushed to the extreme: the narcissistic mother, the oblivious father, the useless brothers, the precocious nephew. But each one is so specifically written they transcend archetype.
- The show is dense — jokes operate on three levels simultaneously (setup, callback, background visual gag). The pilot establishes this density immediately.
- The pilot structure is elegant: Michael tries to leave, can't leave, discovers he has to stay. That's the entire series in one episode.
- The narrator voice is a formal innovation that allows the show to be funnier than dialogue alone.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A comedic engine that is simple (normal person trapped by insane family) but generates infinite variation
- Characters whose flaws are so specific they become iconic, not generic
- A comedic voice/style that is consistent and innovative — the show should sound like nothing else

SERIES ENGINE: "The only competent member of a spectacularly dysfunctional family tries to keep them from destroying each other — and himself."
""",
    },

    {
        "category": "comedy",
        "content": """BENCHMARK: Modern Family Pilot ("Pilot", 2009 — Christopher Lloyd & Steven Levitan)
CATEGORY: Family Comedy (Half-Hour)
SCORE EQUIVALENT: 43/50 (RECOMMEND — network half-hour gold standard)

WHY THIS IS A BENCHMARK:
- The structural innovation: three families, one episode, no frame story needed. The three-family structure means you always have a story to cut to. The pilot proves the engine in 22 minutes.
- The mockumentary format was well-established by 2009, but Modern Family used it to humanize rather than satirize. Every character's confessional is a moment of genuine warmth.
- The ensemble is perfectly balanced: each family has its own specific comedic engine (Jay/Gloria = age gap + class gap; Mitchell/Cam = gay couple navigating parenthood; Phil/Claire = helicopter parent vs. cool dad). They generate comedy independently and together.
- The pilot cold open (Cam presenting Lily like Simba in The Lion King) is a great comedic entrance.
- For Canadian broadcasters: this format (multi-family mockumentary, warm-comedy tone) is extremely adaptable to Canadian settings.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- An ensemble structure that can generate A, B, and C stories independently
- A tone that is warm without being saccharine — comedy that loves its characters
- A format that earns its laugh-track or format device

SERIES ENGINE: "Three generations of one extended family navigate modern life together — and discover they have more in common than they thought."
""",
    },

    # ─── THRILLER ─────────────────────────────────────────────────────────────

    {
        "category": "thriller",
        "content": """BENCHMARK: Fleabag Pilot ("Episode 1", 2016 — Phoebe Waller-Bridge)
CATEGORY: Thriller-Adjacent / Dark Comedy (Half-Hour)
SCORE EQUIVALENT: 48/50 (RECOMMEND — one of the great modern pilots)

WHY THIS IS A BENCHMARK:
- The fourth-wall breaks are not a gimmick — they ARE the series engine. Fleabag talks to us to avoid talking to the people in her life. The form mirrors the character's damage.
- The pilot withholds the central tragedy (the death of her best friend, Boo) while making us feel its weight in every scene. That's exceptional craft.
- Fleabag is the ultimate unreliable narrator: she presents herself as fine, knowingly wrecked, and in control. She is none of these things. The gap between her performance for us and the truth is where the comedy and pain live.
- The pilot is 22 minutes. Every scene advances character, comedy, AND the hidden backstory simultaneously. There is no waste.
- The dialogue is singular. Nobody else writes like this. That's a standard.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A formal device (fourth-wall, voiceover, unusual structure) that is thematically justified — not just stylistically interesting
- A protagonist who is performing for the audience in a way that reveals their damage more than it conceals it
- Dialogue that earns the adjective "singular" — it could only come from this character, this writer

SERIES ENGINE: "A woman deals with the fallout of a tragedy she hasn't admitted yet — by telling us everything except the thing that matters most."
""",
    },

    {
        "category": "thriller",
        "content": """BENCHMARK: 24 Pilot ("Day 1: 12:00 A.M.-1:00 A.M.", 2001 — Joel Surnow & Robert Cochran)
CATEGORY: Thriller (One-Hour)
SCORE EQUIVALENT: 43/50 (RECOMMEND — genre-defining formal innovation)

WHY THIS IS A BENCHMARK:
- The real-time format IS the series engine: each episode is one hour, each season is one day. That constraint generates pressure, stakes, and a specific kind of dread.
- Jack Bauer is a star vehicle: competent, ruthless, principled, and capable of doing terrible things for the right reasons. The moral complexity of the character was new for broadcast action TV.
- The pilot establishes the stakes immediately: assassination attempt on a presidential candidate AND Jack's daughter is missing. Two clocks, running simultaneously.
- The split-screen format is a visual grammar that reinforces the real-time engine.
- For Canadian broadcasters: 24 is the model for a high-concept thriller engine that drives broadcast and international sales.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A formal constraint (real-time, limited location, etc.) that creates pressure rather than just being a gimmick
- Multiple simultaneous storylines that converge — the thriller engine requires parallel tracks
- A lead who is a genuine star vehicle: competent, morally complex, with something to lose

SERIES ENGINE: "CTU agent Jack Bauer has 24 hours to stop a plot — and everything that can go wrong, will."
""",
    },

    {
        "category": "thriller",
        "content": """BENCHMARK: Homeland Pilot ("Pilot", 2011 — Alex Gansa & Howard Gordon)
CATEGORY: Thriller / Spy Drama (One-Hour)
SCORE EQUIVALENT: 44/50 (RECOMMEND — exceptional for the form)

WHY THIS IS A BENCHMARK:
- The central mystery is perfectly constructed: is Nicholas Brody a returning American war hero or a turned terrorist? We don't know. Carrie doesn't know. That uncertainty runs the entire first season.
- Carrie Mathison is one of the great lead characters in recent TV: brilliant, bipolar, obsessive, right for all the wrong reasons. That's a star vehicle.
- The pilot establishes both protagonist and antagonist with equal complexity. We understand why Brody might have been turned. We understand why Carrie might be wrong. Neither is simple.
- The procedural engine (Carrie surveils Brody) allows the show to operate on two levels: thriller mechanics and character study simultaneously.
- The pilot trusts its audience to hold ambiguity across an entire season.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A central mystery that is morally ambiguous — not just "whodunit" but "is anyone right?"
- A protagonist whose personal flaw (Carrie's bipolar disorder) is also their professional superpower
- Enough procedural infrastructure to generate week-to-week story while the serialized mystery develops

SERIES ENGINE: "A CIA analyst with bipolar disorder becomes convinced a returned POW has been turned — and she might be the only one willing to act on what she knows."
""",
    },

    # ─── MYSTERY ──────────────────────────────────────────────────────────────

    {
        "category": "mystery",
        "content": """BENCHMARK: Broadchurch Pilot ("Episode 1", 2013 — Chris Chibnall)
CATEGORY: Mystery / Crime Drama (One-Hour)
SCORE EQUIVALENT: 44/50 (RECOMMEND — British mystery gold standard)

WHY THIS IS A BENCHMARK:
- The premise is a perfect limited-series engine: a child is murdered in a small coastal town. Everybody is a suspect. Everybody has a secret. The investigation will destroy the community.
- The two-detective pairing (the local officer who knows everyone / the outsider who doesn't) is a formal choice that generates conflict and information access simultaneously.
- The pilot establishes that this is not just a whodunit — it's a portrait of a community undone by tragedy. That ambition elevates it above the procedural.
- The cold open (the body on the beach) is efficient and devastating. Nothing is wasted.
- The show trusts the mystery to do its work: no artificial deadline or action setpiece. The dread is social and psychological.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A community that is as much a character as the murder victim
- A mystery that has a social and psychological dimension, not just a plot dimension
- Restraint — let the mystery breathe; don't manufacture artificial excitement

SERIES ENGINE: "A child's murder in a tight-knit coastal town forces the community to reckon with who they actually are."
""",
    },

    {
        "category": "mystery",
        "content": """BENCHMARK: Twin Peaks Pilot ("Pilot", 1990 — David Lynch & Mark Frost)
CATEGORY: Mystery / Surrealist Drama (One-Hour)
SCORE EQUIVALENT: 47/50 (RECOMMEND — genre-defining, formally radical)

WHY THIS IS A BENCHMARK:
- Twin Peaks is the benchmark for a mystery that operates in a different register entirely: the question is not just "who killed Laura Palmer?" but "what is the nature of this town and this evil?"
- The pilot establishes dread through accumulation: the log lady, the traffic light, the music, the way everyone reacts to Laura's death. It's a masterclass in tone.
- Agent Cooper is a star vehicle who is also a formal device: his tape recorder monologues to "Diane" are both character-revealing and a vehicle for Lynch's specific comedic sensibility.
- The show invents its own genre. That's the highest possible standard.
- For Canadian producers: Twin Peaks is the template for ambitious, auteur-driven mystery that can find international audiences.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A tone so specific and consistent that it creates its own world-logic
- A central mystery with both a plot answer AND a metaphysical dimension
- Formal innovation that is in service of the story, not imposed on it

SERIES ENGINE: "FBI Special Agent Dale Cooper investigates the murder of homecoming queen Laura Palmer in a small Pacific Northwest town that is stranger than it appears."
""",
    },

    # ─── PROCEDURAL ───────────────────────────────────────────────────────────

    {
        "category": "procedural",
        "content": """BENCHMARK: Better Call Saul Pilot ("Uno", 2015 — Vince Gilligan & Peter Gould)
CATEGORY: Legal Drama / Crime Procedural (One-Hour)
SCORE EQUIVALENT: 46/50 (RECOMMEND — exceptional, improves on Breaking Bad in some ways)

WHY THIS IS A BENCHMARK:
- The pilot faces an impossible challenge: Jimmy McGill is a character we know becomes Saul Goodman. The show has to make that transformation feel earned and tragic.
- The pilot solves this by showing us who Jimmy is BEFORE the transformation: a struggling public defender who is funny, likeable, and genuinely good in his way. We like him. We know we're watching him lose himself. That dramatic irony is the engine.
- The cold open (Saul after Breaking Bad, working in a Cinnabon, watching old tapes of himself) reframes the entire series: this is a tragedy.
- The show generates two simultaneous pleasures: the legal procedural (Jimmy's cases) and the serialized drama (Jimmy's moral decline).
- The dialogue is exceptional. Jimmy's fast-talking sales patter is character-specific, funny, and revealing simultaneously.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A protagonist whose flaw is visible from the first scene, even if they're charming
- A procedural engine that generates weekly story while the serialized arc advances
- The courage to play tragedy in a comic register — not to soften it, but to make it more devastating

SERIES ENGINE: "A fast-talking, good-hearted small-time lawyer makes choices that will eventually turn him into the man we already know he becomes."
""",
    },

    {
        "category": "procedural",
        "content": """BENCHMARK: True Detective Season 1 Pilot ("The Long Bright Dark", 2014 — Nic Pizzolatto)
CATEGORY: Crime Procedural / Prestige Drama (One-Hour)
SCORE EQUIVALENT: 46/50 (RECOMMEND — exceptional)

WHY THIS IS A BENCHMARK:
- The time-fracture structure (1995 investigation / 2012 interrogation) is not a gimmick — it tells us something terrible happened in the past AND we're watching it unfold simultaneously from two directions.
- Rust Cohle is one of the great TV characters: nihilistic, brilliant, broken, and incapable of shutting off his perception. The dialogue he's given is unlike any character on broadcast TV in 2014.
- The partnership engine (Cohle/Hart — philosopher vs. pragmatist, broken vs. conventional) is classic but executed at an exceptional level.
- The Louisiana setting is specific enough to be its own character. The landscape mirrors the psychological landscape of the show.
- The pilot delivers pure procedural (a body, a ritual killing scene, a detective briefing) while simultaneously operating at a philosophical level.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A structural device (time fracture, double timeline, etc.) that generates dramatic irony
- A partnership dynamic where both characters are wrong in specific, complementary ways
- A dialogue voice for your lead character that is distinct enough to be memorable

SERIES ENGINE: "Two Louisiana detectives investigate a series of ritualistic murders across seventeen years — and the case refuses to stay closed."
""",
    },

    {
        "category": "procedural",
        "content": """BENCHMARK: Grey's Anatomy Pilot ("A Hard Day's Night", 2005 — Shonda Rhimes)
CATEGORY: Medical Procedural / Soap Drama (One-Hour)
SCORE EQUIVALENT: 43/50 (RECOMMEND — exceptional broadcast procedural engine)

WHY THIS IS A BENCHMARK:
- The medical procedural engine is clean: interns rotate through cases, each case mirrors their personal storyline, the hospital is both setting and metaphor.
- Meredith Grey is a star vehicle: smart, emotionally damaged, determined not to ask for help. The show is about her, told through medicine.
- The show runs three engines simultaneously: the case-of-the-week (medical), the personal drama (intern relationships), and the serialized arc (Meredith/Derek). That's textbook broadcast procedural architecture.
- The ensemble is perfectly designed: each intern is an archetype (the ambitious one, the heart-on-sleeve one, the competitive one, the gentle giant) but Rhimes gives each one a specific wound.
- The pilot delivers on its premise immediately: interns in over their heads on their first day. The stakes are clear and the engine is proven.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A procedural case engine that mirrors the protagonist's personal arc thematically
- An ensemble where each member is an archetype BUT has a specific backstory wound
- A serialized romantic/personal engine that can sustain multiple seasons alongside the procedural

SERIES ENGINE: "New surgical interns navigate their most grueling year while falling apart and falling in love at Seattle Grace Hospital."
""",
    },

    # ─── CANADIAN ─────────────────────────────────────────────────────────────

    {
        "category": "canadian",
        "content": """BENCHMARK: Letterkenny Pilot ("MoDeans", 2016 — Jared Keeso)
CATEGORY: Canadian Comedy (Half-Hour)
SCORE EQUIVALENT: 44/50 (RECOMMEND — exceptional Canadian comedy)

WHY THIS IS A BENCHMARK:
- Letterkenny is proof that the most specific setting possible can generate the broadest audience: a single Canadian rural township, six people, a farm supply store.
- The dialogue is the show's entire engine: hyper-specific, rapid-fire, rhythmically distinct. Wayne's voice is so specific that the show has a vocal identity unlike any other Canadian comedy.
- The pilot establishes the world and its rules immediately: this is a show about language, community, and the specific rhythms of rural Canadian life. No explanation is given. You either get it or you don't.
- The ensemble is five archetypes but so specifically written they're icons: Wayne (the king of the town), Daryl (the enthusiastic sidekick), Squirrelly Dan (the linguistic inventor), Katy (the competent woman in a man's world), Stewart (the drug dealer intellectual).
- For Canadian broadcasters: Letterkenny demonstrates that a resolutely Canadian voice can break internationally without compromising what makes it Canadian.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A voice so specific it could come from no other show
- A setting that is not incidental but essential — remove the rural Canada element and the show doesn't exist
- An ensemble whose comedic chemistry is evident from page one

SERIES ENGINE: "In the small town of Letterkenny, Wayne runs a farm supply store, defends his title as toughest guy in town, and everyone argues — a lot, quickly, and brilliantly."
""",
    },

    {
        "category": "canadian",
        "content": """BENCHMARK: Slings & Arrows Pilot ("A Mid-Winter's Night Dream", 2003 — Mark McKinney, Susan Coyne & Bob Martin)
CATEGORY: Canadian Drama/Comedy Hybrid (One-Hour)
SCORE EQUIVALENT: 45/50 (RECOMMEND — exceptional; Canadian and internationally acclaimed)

WHY THIS IS A BENCHMARK:
- Slings & Arrows is the standard for a show that is both authentically Canadian (the New Burbage Theatre Festival is clearly Stratford) and internationally appealing (the Shakespeare context is universal).
- Geoffrey Tennant is a star vehicle: brilliant, traumatized, self-destructive, and unable to stop caring. His conflict with Richard Smith-Jones (the administrator who wants to commercialize the festival) is the entire series engine.
- Each season structure maps to a Shakespeare play: Season 1 is Hamlet, Season 2 is Macbeth, Season 3 is King Lear. That's a three-season arc with a formal architecture. Genius planning.
- The show is funny AND genuinely moving. The ghost of Oliver Welles serves the same function as the ghost in Hamlet: it confronts the protagonist with who he's failing to be.
- The dialogue is sharp, theatre-world specific, and witty without being precious.

WHAT A SCRIPT MUST HAVE TO APPROACH THIS LEVEL:
- A setting that is both specifically Canadian and universally relatable
- A series architecture with a planned end — seasons mapped to a clear thematic progression
- A protagonist whose personal wound IS the series engine

SERIES ENGINE: "A brilliant, troubled director returns to the Canadian theatre festival he fled to find his mentor's ghost waiting for him — and the theatre industry determined to sell Shakespeare."
""",
    },

    # ─── PHILIP'S CALIBRATION EXAMPLES ───────────────────────────────────────

    {
        "category": "calibration",
        "content": """PHILIP RICCIO'S CALIBRATION EXAMPLES — PASS RANGE (24–28/50)

These are scripts Philip Riccio actually read and passed on. They represent competent but not compelling work.

---

POV (28/50 — PASS)
Format: 1-Hour Drama (Cop/Procedural)
What worked: Creative POV-jumping technique gave it a formal twist; two leads sleeping together early in the pilot subverted the will-they-won't-they; good forward momentum; modern premise.
What killed it: The POV gimmick may get old fast — it's a trick, not an engine; resembles existing cop shows without surpassing them; fast-cut flashbacks felt overdone; nothing new underneath the technique; lacks interesting secondary storylines.
Philip's verdict: The formal gimmick does some work but isn't strong enough to carry the show. Standard cop episodic underneath. 28.

---

Richard (24/50 — PASS)
Format: ½ Hour Comedy
Logline: Richard Joseph and his eccentric 27-year-old son try to revitalize a failing stationery shop in a dying strip mall.
What worked: Writer is apparently a successful Indigenous comedian (the voice is there); the end of the teaser was a strong moment; a twist creating bottom for the lead had potential.
What killed it: Sets up as a workplace comedy but the pilot isn't actually that; can't imagine what other episodes would be — no series engine; not that funny — a generic sitcom needs to be REALLY funny and this isn't; structure needs tightening; only an A storyline with other things as random plot points.
Philip's verdict: The premise sounds like a show but the pilot doesn't prove it's a show. 24.

---

Maniac Pervert (26/50 — PASS)
Format: ½ Hour Drama
What worked: Originality in concept; characters had personality; some genuine humour.
What killed it: Not genre-defying; sits awkwardly between categories — not funny enough to be a comedy, not scary enough to be a thriller; the Halifax period piece premise didn't grab; not sure the premise actually works as a sustained series.
Philip's verdict: Interesting voice but the tonal confusion kills it. You can't be both things at once without being exceptional, and this isn't. 26.

---

KEY PATTERN — What a PASS looks like:
A PASS doesn't mean badly written. It means competent work that doesn't rise above competent. When you're tempted to score something 35+, ask yourself: is it genuinely better than POV (28) or Richard (24)? Does it have a clearer series engine? More interesting characters? A stronger voice? If you can't point to specific ways it exceeds these, recalibrate down.
""",
    },

    {
        "category": "calibration",
        "content": """PHILIP RICCIO'S CALIBRATION EXAMPLES — CONSIDER RANGE (29–35/50)

These are scripts Philip Riccio felt were worth a conversation — not picks, but not dismissals.

---

Sara Knox (33/50 — CONSIDER)
Format: 1-Hour Drama (Procedural)
What worked: Premise and lead character are great; Philip was imagining Alison Pill in the role; the kind of procedural always in need; liked the supporting characters; has another level it could reach with a polish.
What killed it: Dialogue fell flat sometimes and felt like it was trying too hard; the humour didn't fit the tone; needs to find the quirk and lightness that fits the premise.
Philip's verdict: This has the bones. The lead character is a star vehicle, the procedural engine is clear. But the execution isn't there yet. You'd take a meeting on this. 33.

---

The Legion (35/50 — CONSIDER)
Format: ½ Hour Comedy
Logline: Dysfunctional members of a rundown local Legion try to boost membership after the president issues an ultimatum.
What worked: Classic sitcom setups and punchlines that are actually funny; solid structure and a clear show premise; genuine understanding of the genre; simple premise (Legion gets a hot tub) generates situation and jokes; characters well drawn — the two leads are like a gender-reversed Sam and Diane from Cheers; strong beginning, middle, and end.
What killed it: Is a legion an interesting or appealing enough setting? The script won Philip over by the end but the premise is off-putting on first read. Title is too generic and needs replacing.
Philip's verdict: When a script wins you over despite your initial resistance, that's a good sign. This works. The engine is simple, the characters are good, and it's actually funny. Worth developing. 35.

---

Book of Ruth (33/50 — PASS)
Format: 1-Hour Drama
Logline: A young Holocaust survivor with visions of the dark future uses her abilities as an assassin to stop evil people before they can act.
What worked: High-concept premise; period setting with a supernatural thriller engine; inherent dramatic stakes.
Philip's verdict: The concept is compelling enough to consider, but the execution needs work. 33.

---

KEY PATTERN — What a CONSIDER looks like:
A CONSIDER means there's a genuine development conversation to have. The problems are fixable. There's a real series there underneath the execution issues. A 33–35 script has a clear engine, compelling lead, and something distinctive — but hasn't fully executed on its promise. When you're scoring something in this range, be specific: what are the two or three things that would need to change for this to become a Recommend?
""",
    },

    {
        "category": "calibration",
        "content": """PHILIP RICCIO'S CALIBRATION EXAMPLES — HIGH RANGE (36–37/50) — STILL PASSED

These examples illustrate something important: a high score doesn't always equal a pick.

---

Lawyers Guns and Money (30/50 — PASS)
Format: 1-Hour Drama
What worked: Strong teaser draws in immediately; Act 1 solid and efficient; good twist on page 34 upping stakes; strong Act 2 finish; lead character is a good star vehicle; potential as solid popcorn show.
What killed it: Very cliché (though also its strength in a way); Act 3 is essentially a reset of Act 1 kidnapping instead of building; page 51 logic hole; Act 4 rushed with conveniences; the father/daughter dynamic is a cliché and the daughter is bland; lead villain too generic; title doesn't fit the show.
Philip's verdict: Doesn't surpass its genre. You've seen this show. The lead is good but everything around the lead is generic. 30.

---

Sterling (36/50 — PASS)
Format: 1-Hour PI Drama
Logline: After his estranged, famous private investigator father dies unexpectedly, a reluctant son with an eidetic memory must step up and solve a kidnapping case to save his father's agency.
What worked: The eidetic memory twist on the PI genre is fresh; the father's death as inciting incident creates both an engine and an emotional through-line; star vehicle potential.
Philip's verdict: High score, still a pass. The execution of a strong premise wasn't quite there. The show as written doesn't deliver on what the logline promises. 36.

---

The Great Lakes (37/50 — PASS)
Format: ½ Hour Comedy
Logline: A charming but broke older brother moves in with his single mom sister and her kids, tries to teach his teenage nephew how to be popular while reluctantly helping out.
What worked: Characters well defined quickly; fast witty dialogue; the brother/sister dynamic works; strong sense of comedy through character.
What killed it: Generic — fails to distinguish itself from every other family comedy; not every joke lands; wouldn't reinvent the wheel.
Philip's verdict: This is a good show. But "good" isn't enough. In a world where Schitt's Creek exists, you need to be more than good. 37 — pass.

---

KEY PATTERN — What separates a 37 PASS from a 38 RECOMMEND:
The Great Lakes (37) and The Legion (35) are both CONSIDER/Pass territory. The difference: The Legion has a more specific setting and a clearer two-lead comedic engine. The Great Lakes is better written but more generic. Specificity beats polish. A 38+ script must have both.

IMPORTANT FOR SCORING: A 37/50 is in Philip's "Pass" category for half-hour comedy. This means a comedy script needs to score 38+ to earn CONSIDER/RECOMMEND. Most scripts that feel like 37 are really 30–33.
""",
    },

    {
        "category": "calibration",
        "content": """PHILIP RICCIO'S TASTE PROFILE — WHAT HE LOOKS FOR

Synthesized from 9 real coverage entries and his stated preferences.

WHAT PHILIP REWARDS:
1. A clear, simple series engine that he can see generating 50 episodes
2. A lead character who is a genuine star vehicle — something a great actor would want
3. Sharp, character-specific dialogue — characters who sound like themselves
4. Structural discipline — every scene earns its place; Act 3 especially
5. Originality — not "original" in the sense of weird, but "does this show need to exist?"
6. The ability to win him over despite initial resistance (The Legion did this)

WHAT PHILIP PENALIZES:
1. Generic premises — shows that are just a Canadian version of something that already exists
2. Weak series engine — a great premise for an episode but not a show
3. Tonal confusion — trying to be two things and being neither
4. Act 3/4 collapse — most Canadian pilots fall apart in the final act
5. Flat secondary characters — a great lead surrounded by types
6. Logic holes — one page 51 logic hole sank Lawyers Guns and Money
7. Titles that don't fit the show

PHILIP'S BENCHMARK QUESTION:
"Can I imagine what Season 2 looks like?" If he can't see episode 8 from reading the pilot, it's a pass.

PHILIP'S CHARACTER QUESTION:
"Can I imagine a specific great actor wanting this role?" If the answer isn't immediate, the character needs work.

PHILIP'S DIALOGUE STANDARD:
Characters should sound like themselves. If you can swap dialogue between characters without it mattering, the dialogue has failed.

FOR CANADIAN BROADCASTERS:
Philip thinks specifically about CBC, Crave, Showcase, Bell Media, Rogers. He asks: which commissioner would champion this show, and why would their network want it?
""",
    },

]

# ─── SEED FUNCTION ────────────────────────────────────────────────────────────

async def seed():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        # Try to load from .env
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DATABASE_URL="):
                        database_url = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL not set. Set it as an environment variable or in backend/.env\n"
            "Example: DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname python seed_domain_knowledge.py"
        )

    # Ensure asyncpg driver
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

    print(f"Connecting to database...")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        from sqlalchemy import text

        # Check existing entries
        result = await session.execute(
            text("SELECT COUNT(*) FROM domain_knowledge")
        )
        existing_count = result.scalar()
        print(f"Existing domain knowledge entries: {existing_count}")

        # Ask before wiping
        if existing_count > 0:
            response = input(f"\nFound {existing_count} existing entries. Wipe and reseed? [y/N] ")
            if response.lower() != "y":
                print("Aborting. Existing entries preserved.")
                return

            await session.execute(text("DELETE FROM domain_knowledge"))
            await session.commit()
            print("Cleared existing entries.")

        # Insert all entries
        inserted = 0
        for entry in ENTRIES:
            entry_id = str(uuid.uuid4())
            now = datetime.utcnow()
            await session.execute(
                text(
                    "INSERT INTO domain_knowledge (id, category, content, created_at, updated_at) "
                    "VALUES (:id, :category, :content, :created_at, :updated_at)"
                ),
                {
                    "id": entry_id,
                    "category": entry["category"],
                    "content": entry["content"],
                    "created_at": now,
                    "updated_at": now,
                },
            )
            inserted += 1
            print(f"  [{inserted}/{len(ENTRIES)}] Inserted: {entry['category']} — {entry['content'][:60].strip()}...")

        await session.commit()
        print(f"\n✅ Done. Inserted {inserted} domain knowledge entries.")
        print("\nCategories:")
        categories = {}
        for e in ENTRIES:
            categories[e["category"]] = categories.get(e["category"], 0) + 1
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count} entries")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
