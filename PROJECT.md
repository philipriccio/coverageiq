# CoverageIQ — Project Overview

## 🎯 Vision
AI-powered script coverage tool. Upload a screenplay, get professional-quality coverage (logline, synopsis, analysis, scores, verdict) automatically generated. Think: script reader as a service.

## 👤 For Whom
Development executives, producers, agents who need to read and assess large volumes of scripts quickly.

## 🏗️ Current State (Feb 21, 2026)
**Status:** Prototype/paused
**Blocked:** Needs Anthropic API key from Philip

### What's Built
- Basic script upload and parsing
- Coverage template structure
- Initial Claude integration (needs API key)

### Pending
- Anthropic API key configuration
- Full coverage generation pipeline
- Output formatting (PDF export)
- Testing with real scripts

## 🏁 Competitive Landscape

### ScriptReader.ai — Primary Competitor
**URL:** https://scriptreader.ai  
**Positioning:** Consumer-facing, writer-focused AI script coverage. Budget entry point.

**Their features:**
- $9.99 per script (one-time, per report)
- Free sample: first 3 scenes only
- Director's Cut: exec summary, marketability, Pass/Consider/Recommend, scene-by-scene critique (engagement, dialogue, pacing), character arcs, comps, writer voice analysis
- AI scene improvement credits ($10 / 100 credits)
- Bulk/Reel Deal packages for agents/managers
- PDF upload, confidentiality assured
- 1-2 hour turnaround

**Their weakness:** Writer-focused (helping writers improve). Not built for executives evaluating acquisition. Lacks mandate checklist, network targeting, Canadian content compliance — the things Philip actually needs.

### Greenlight Coverage — Secondary Competitor
**URL:** greenlightcoverage.com  
**Pricing:** $45–$325 per script, monthly plans  
**Features:** 1–10 ratings, logline, synopsis, cast list, comps, AI Q&A, 5-minute turnaround  
**Weakness:** Expensive, generic — not customized for Canadian TV development executives

### Our Differentiation (if we go to market)
- **Canadian mandate compliance** built-in (CanCon, star role, co-pro, budget feasibility)
- **Network targeting** — assessed against specific buyers (CBC, Crave, Netflix Canada, etc.)
- **Executive-first** — designed for development execs and producers, not writers
- **Custom knowledge base** — trainable on your mandate, your comps, your taste
- **CRM integration** — reports live inside your development pipeline (Hawco CRM)

### Features Worth Adding Before Launch
1. **Per-script pricing / paywall** — ScriptReader charges $9.99; we could do $15–25 for exec-quality coverage
2. **Q&A / chat with the coverage** — ask follow-up questions about the script (Greenlight has this)
3. **Writer submission portal** — allow writers to submit directly, exec sees the queue
4. **Comparison mode** — compare two scripts side-by-side
5. **Revision tracking** — resubmit a revised draft, see what changed in the coverage
6. **Network fit scoring** — explicit score for "CBC fit", "Netflix Canada fit" etc.
7. **Export to industry-standard format** — WGA-standard coverage PDF

---

## 📜 History

### Feb 17, 2026 — Initial Prototype
- Created basic structure
- Defined coverage output format matching industry standard
- Paused pending API key

## 🔧 Technical Stack
- **Framework:** TBD (likely Next.js)
- **AI:** Anthropic Claude for analysis
- **PDF:** For script input and coverage output

## ⚠️ Critical Constraints
1. **Needs Anthropic API key** — Can't proceed without it
2. **Script confidentiality** — Scripts are sensitive IP, must not be stored/leaked
3. **Coverage quality** — Must match professional reader quality or it's useless

## 🚫 What NOT to Do
- Don't store uploaded scripts longer than needed
- Don't expose scripts to third parties
- Don't claim coverage is human-written (it's AI-assisted)

---
*Last updated: 2026-02-21 by Mildred*
