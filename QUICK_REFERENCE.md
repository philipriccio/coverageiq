# CoverageIQ - Quick Reference Card

## 🚀 Quick Start

### Test the App
**URL:** https://02c4e396.coverageiq-frontend.pages.dev

1. Upload a PDF script or paste text
2. Fill in title/genre (optional)
3. Choose analysis depth: Quick / Standard / Deep
4. Click "Generate Coverage Report"
5. Watch progress bar: 0% → 100%
6. Review coverage, export to Google Doc or PDF

---

## 🔗 Important URLs

| Resource | URL |
|----------|-----|
| **Frontend (Production)** | https://02c4e396.coverageiq-frontend.pages.dev |
| **Backend API** | https://coverageiq-backend.onrender.com |
| **API Docs (Swagger)** | https://coverageiq-backend.onrender.com/docs |
| **Health Check** | https://coverageiq-backend.onrender.com/health |
| **GitHub Repo** | https://github.com/philipriccio/coverageiq |
| **Render Dashboard** | https://dashboard.render.com/web/srv-d696u314tr6s73cgpft0 |
| **Cloudflare Pages** | https://dash.cloudflare.com/ |

---

## 💰 Cost Per Analysis

| Mode | Clean Content | Mature Content (HBO) |
|------|---------------|---------------------|
| **Quick** | ~$0.04 | ~$0.24 |
| **Standard** | ~$0.04 | ~$0.24 |
| **Deep** | ~$0.04 | ~$0.24 |

**Why the difference?**
- Clean content: Kimi K2.5 only ($0.04)
- Mature content: Kimi rejects → Claude fallback ($0.04 + $0.20 = $0.24)

---

## 🛠️ Troubleshooting

### "Network Error" when uploading
**Cause:** Backend is cold-starting (Render free tier sleeps after 15min inactivity)  
**Fix:** Wait 50 seconds, try again

### "Coverage analysis failed: high risk"
**Cause:** This error should NOT appear anymore (Claude fallback handles it)  
**Fix:** If you see this, the fallback failed - contact Janet

### "Concurrent operations not permitted"
**Cause:** This error should NOT appear anymore (NullPool fix deployed)  
**Fix:** If you see this, the SQLite fix didn't work - contact Janet

### Progress bar stuck at 0%
**Cause:** Backend crashed or frontend can't reach backend  
**Fix:** 
1. Check https://coverageiq-backend.onrender.com/health
2. If unhealthy, check Render dashboard logs
3. May need to restart service

---

## 📊 Analysis Modes

### Quick (~2 min, ~$0.04)
- Fast turnaround
- Basic coverage: logline, synopsis, scores, strengths/weaknesses
- Good for initial screening

### Standard (~5 min, ~$0.04)
- Recommended for most scripts
- Full coverage: above + character notes, structure analysis, market positioning
- Good for development notes

### Deep (~10 min, ~$0.04-0.24)
- Most comprehensive
- Everything in Standard + deeper series engine analysis
- May trigger Claude fallback on mature content (HBO, Showtime, FX scripts)
- Best for scripts you're seriously considering

---

## 🔐 Credentials & Access

### Stored Locations
- **Render API key:** `/data/.openclaw/workspace/render-credentials.json`
- **Cloudflare token:** `/data/.openclaw/workspace/cloudflare-credentials.json`
- **GitHub token:** `/data/.openclaw/workspace/github-credentials.json`
- **Google Drive credentials:** `/data/.openclaw/workspace/google-drive-credentials.json`

### Environment Variables (Render)
Set in Render dashboard under "Environment" tab:
- `ANTHROPIC_API_KEY` - Claude API key
- `MOONSHOT_API_KEY` - Kimi K2.5 API key
- `DATABASE_URL` - SQLite connection string
- `CORS_ORIGINS` - Allowed frontend URLs
- `PYTHON_VERSION` - 3.11.9

---

## 🚨 Emergency Commands

### Restart Backend
```bash
curl -X POST "https://api.render.com/v1/services/srv-d696u314tr6s73cgpft0/restart" \
  -H "Authorization: Bearer rnd_RUYP6SvkiWbWQP1FcNhQBcg55pvS"
```

### Check Health
```bash
curl https://coverageiq-backend.onrender.com/health | jq
```

### Trigger Manual Deploy
```bash
curl -X POST "https://api.render.com/v1/services/srv-d696u314tr6s73cgpft0/deploys" \
  -H "Authorization: Bearer rnd_RUYP6SvkiWbWQP1FcNhQBcg55pvS"
```

### Check Latest Deploy Status
```bash
curl -s -H "Authorization: Bearer rnd_RUYP6SvkiWbWQP1FcNhQBcg55pvS" \
  "https://api.render.com/v1/services/srv-d696u314tr6s73cgpft0/deploys?limit=1" | \
  jq '.[0].deploy | {status, commit: .commit.message}'
```

---

## 📝 Git Workflow

### Make Changes
```bash
cd /data/.openclaw/workspace/coverageiq
# ... make changes ...
git add .
git commit -m "Description of changes"
git push origin main
```

**Deployment happens automatically** via webhook (no manual deploy needed!)

### View Recent Commits
```bash
cd /data/.openclaw/workspace/coverageiq
git log --oneline -10
```

---

## 📞 Who to Contact

### Technical Issues
**Janet (OpenClaw AI Assistant)**
- Available via Telegram or OpenClaw web chat
- Can diagnose, fix, and redeploy

### Product/Feature Requests
**Philip Riccio**
- Decides priorities and features
- Tests with real scripts from Hawco

---

## 🎯 Testing Checklist (Morning)

Before using for real Hawco scripts:

- [ ] Open https://02c4e396.coverageiq-frontend.pages.dev
- [ ] Upload short test script (5 pages) - Quick mode
- [ ] Verify analysis completes successfully
- [ ] Check coverage quality (scores, analysis depth)
- [ ] Try Google Doc export
- [ ] Try PDF export
- [ ] Upload Hacks pilot - Deep mode
- [ ] Verify Claude fallback works (no "high risk" error)
- [ ] Verify progress bar displays during analysis

---

**Last Updated:** 2026-02-15 23:04 PM EST  
**Status:** ✅ All systems operational
