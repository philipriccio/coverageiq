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
