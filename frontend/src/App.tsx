import { useCallback, useEffect, useRef, useState, useMemo } from 'react'
import axios from 'axios'
import './App.css'
import { ProgressBar } from './components/ProgressBar'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const isAdminRoute = window.location.pathname === '/admin'

type Recommendation = 'Pass' | 'Consider' | 'Recommend'

interface EvidenceQuote {
  quote: string
  page: number
  context?: string
}

interface MandateChecklistItem {
  result: boolean
  rationale: string
}

interface CoverageReport {
  report_id: string
  script_id: string
  script_title?: string
  genre?: string
  comps?: string[]
  analysis_depth: string
  status: string
  created_at: string
  completed_at?: string
  subscores?: Record<string, { score?: number } | number>
  mandate_checklist?: Record<string, MandateChecklistItem>
  total_score?: number
  recommendation?: Recommendation
  logline?: string
  synopsis?: string
  overall_comments?: string
  strengths: string[]
  weaknesses: string[]
  character_notes?: string
  structure_analysis?: string
  market_positioning?: string
  evidence_quotes: EvidenceQuote[]
  model_used: string
  is_flagged_example?: boolean
}

interface JobStatus {
  job_id: string
  report_id: string | null
  status: 'queued' | 'processing' | 'completed' | 'failed'
  progress: number
  error_message?: string
}

interface HistoryItem {
  id: string
  title?: string
  genre?: string
  analysis_depth: string
  recommendation?: Recommendation
  total_score?: number
  created_at: string
  model_used: string
}

interface KnowledgeEntry {
  id: string
  category: string
  content: string
  created_at: string
  updated_at: string
}

// ─── Corkboard / Pinned Card UI (matching Hawco CRM) ─────────────────────────

const pinnedCardColors = [
  'bg-amber-50 border-amber-200',
  'bg-orange-50 border-orange-200',
  'bg-yellow-50 border-yellow-200',
  'bg-stone-50 border-stone-200',
  'bg-amber-100/60 border-amber-300',
  'bg-orange-100/60 border-orange-300',
]

function PinnedCard({
  children,
  title,
  colorIndex = 0,
  className = '',
}: {
  children: React.ReactNode
  title: string
  colorIndex?: number
  className?: string
}) {
  const colorClass = pinnedCardColors[colorIndex % pinnedCardColors.length]
  return (
    <div
      className={`${colorClass} rounded-xl p-5 shadow-sm border-2 relative transition-all duration-200 hover:shadow-md ${className}`}
    >
      {/* Pin effect */}
      <div className="absolute -top-1.5 left-6 w-3 h-3 rounded-full bg-red-700/40 shadow-sm" />
      <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2 text-sm uppercase tracking-wide">
        {title}
      </h3>
      {children}
    </div>
  )
}

// ─── Verdict / Recommendation badge ──────────────────────────────────────────

const verdictStampColors: Record<string, string> = {
  Pass: 'bg-red-100 text-red-700 border-red-300 shadow-red-200/80',
  Consider: 'bg-yellow-100 text-yellow-700 border-yellow-300 shadow-yellow-200/80',
  Recommend: 'bg-green-100 text-green-700 border-green-300 shadow-green-200/80',
}

function VerdictStamp({ recommendation }: { recommendation?: string }) {
  const rec = recommendation || 'Pass'
  const colors = verdictStampColors[rec] || verdictStampColors['Pass']
  return (
    <div
      className={`px-5 py-3 rounded-2xl border-2 text-center min-w-[180px] shadow-lg rotate-1 ${colors}`}
    >
      <div className="text-[10px] font-black tracking-[0.35em] uppercase opacity-70 mb-1">Verdict</div>
      <div className="text-2xl font-black tracking-wide">{rec.toUpperCase()}</div>
    </div>
  )
}

// ─── Score bar row ────────────────────────────────────────────────────────────

function ScoreRow({ label, score, notes }: { label: string; score: number | null | undefined; notes?: string | null }) {
  return (
    <div className="flex items-center gap-4">
      <div className="w-28 flex-shrink-0">
        <span className="text-sm font-medium text-slate-700">{label}</span>
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-3">
          <div className="flex-1 h-3 bg-slate-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-amber-500 rounded-full transition-all"
              style={{ width: score != null ? `${(score / 10) * 100}%` : '0%' }}
            />
          </div>
          {score != null && (
            <span className="text-sm font-bold text-slate-700 w-12 text-right">{score}/10</span>
          )}
        </div>
        {notes && <p className="text-sm text-slate-600 mt-1 italic">{notes}</p>}
      </div>
    </div>
  )
}

// ─── Mandate item (display-only, not togglable) ────────────────────────────

function MandateItem({ checked, label, rationale }: { checked: boolean; label: string; rationale?: string }) {
  return (
    <div
      className={`flex items-start gap-3 p-3 rounded-lg border ${
        checked ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
      }`}
    >
      <div
        className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
          checked ? 'bg-green-500 text-white' : 'bg-red-400 text-white'
        }`}
      >
        {checked ? (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
          </svg>
        )}
      </div>
      <div>
        <span className={`font-medium ${checked ? 'text-green-800' : 'text-red-700'}`}>{label}</span>
        {rationale && <p className="text-sm text-slate-600 mt-0.5">{rationale}</p>}
      </div>
    </div>
  )
}

// ─── Score key label map ──────────────────────────────────────────────────────

const scoreKeyLabels: Record<string, string> = {
  concept: 'Concept',
  characters: 'Characters',
  structure: 'Structure',
  dialogue: 'Dialogue',
  market_fit: 'Market Fit',
  // fallback: raw key will be title-cased below
}

function labelForKey(key: string): string {
  return scoreKeyLabels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

// ─── Main Report Viewer ────────────────────────────────────────────────────

function ReportViewer({
  report,
  onBack,
  onExportPDF,
  onExportGoogleDoc,
  onFlagExample,
  exporting,
  flagging,
}: {
  report: CoverageReport
  onBack: () => void
  onExportPDF: () => void
  onExportGoogleDoc: () => void
  onFlagExample: () => void
  exporting: { pdf: boolean; googleDoc: boolean }
  flagging: boolean
}) {
  const subscoreEntries = Object.entries(report.subscores || {}).map(([key, value]) => ({
    key,
    score: typeof value === 'number' ? value : (value as { score?: number }).score ?? 0,
  }))

  const mandateChecklistEntries = [
    { key: 'canadian_content', label: 'Canadian Content' },
    { key: 'star_role', label: 'Star Role' },
    { key: 'intl_copro', label: "Int'l Co-Pro Friendly" },
    { key: 'budget_feasible', label: 'Budget Feasible' },
  ]
    .map(({ key, label }) => ({ key, label, item: report.mandate_checklist?.[key] }))
    .filter(({ item }) => item) as Array<{ key: string; label: string; item: MandateChecklistItem }>

  const renderParagraphs = (value?: string) =>
    value
      ?.split('\n')
      .filter(Boolean)
      .map((line, i) => (
        <p key={i} className="text-slate-700 text-sm leading-relaxed mb-1">
          {line}
        </p>
      ))

  const totalScore = report.total_score ?? null

  return (
    <div
      className="min-h-screen bg-amber-50/80 p-6"
      style={{
        backgroundImage: `
          radial-gradient(circle at 20% 20%, rgba(139, 69, 19, 0.03) 1px, transparent 1px),
          radial-gradient(circle at 80% 80%, rgba(139, 69, 19, 0.03) 1px, transparent 1px),
          linear-gradient(45deg, transparent 49%, rgba(139, 69, 19, 0.02) 50%, transparent 51%),
          linear-gradient(-45deg, transparent 49%, rgba(139, 69, 19, 0.02) 50%, transparent 51%)
        `,
        backgroundSize: '20px 20px, 20px 20px, 40px 40px, 40px 40px',
      }}
    >
      {/* Back button */}
      <div className="mb-6">
        <button
          type="button"
          onClick={onBack}
          className="text-amber-700 hover:text-amber-800 flex items-center gap-1 font-medium text-sm"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Reports
        </button>
      </div>

      {/* Header Zone */}
      <div className="mb-8">
        <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-amber-200/50 p-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-700 via-amber-600 to-amber-700" />

          <div className="flex items-start justify-between">
            <div className="flex-1">
              {/* Header label */}
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-bold tracking-widest text-amber-700 uppercase">
                  CoverageIQ
                </span>
                <span className="text-amber-400">|</span>
                <span className="text-xs font-bold tracking-widest text-amber-600 uppercase">
                  Script Assessment
                </span>
              </div>

              <h1 className="text-3xl font-bold text-slate-900 mb-2">
                {report.script_title || 'Untitled Script'}
              </h1>

              <div className="flex items-center gap-3 flex-wrap">
                {report.genre && (
                  <span className="px-3 py-1.5 bg-amber-50 text-amber-900 rounded-full text-sm font-medium border border-amber-200">
                    {report.genre}
                  </span>
                )}
                <span className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-full text-sm font-medium border border-slate-200">
                  {report.analysis_depth}
                </span>
                <span className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-full text-sm font-medium border border-slate-200">
                  {new Date(report.created_at).toLocaleDateString('en-US', {
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </span>
                <span className="px-3 py-1.5 bg-stone-100 text-stone-700 rounded-full text-sm font-medium border border-stone-200">
                  {report.model_used}
                </span>
              </div>
            </div>

            {/* Verdict stamp + actions */}
            <div className="flex flex-col items-end gap-3 ml-6">
              <VerdictStamp recommendation={report.recommendation} />

              <button
                type="button"
                onClick={onFlagExample}
                disabled={flagging || report.is_flagged_example}
                className="inline-flex items-center gap-2 px-4 py-2 bg-amber-50 text-amber-700 rounded-lg hover:bg-amber-100 transition-colors text-sm font-medium border border-amber-200 disabled:opacity-60"
              >
                {report.is_flagged_example ? '★ Saved as example' : flagging ? 'Saving…' : '★ Flag as example'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column */}
        <div className="lg:col-span-5 space-y-6">
          {/* Logline */}
          {report.logline && (
            <PinnedCard title="Logline" colorIndex={0}>
              <p className="text-slate-800 font-medium leading-relaxed italic">{report.logline}</p>
            </PinnedCard>
          )}

          {/* Synopsis */}
          {report.synopsis && (
            <PinnedCard title="Synopsis" colorIndex={1}>
              <div className="space-y-1">{renderParagraphs(report.synopsis)}</div>
            </PinnedCard>
          )}

          {/* Script Details */}
          <PinnedCard title="Script Details" colorIndex={1}>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-slate-500">Title</span>
                <span className="text-slate-800 font-medium">{report.script_title || 'Untitled'}</span>
              </div>
              {report.genre && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Genre</span>
                  <span className="text-slate-800">{report.genre}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-slate-500">Depth</span>
                <span className="text-slate-800">{report.analysis_depth}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Model</span>
                <span className="text-slate-800">{report.model_used}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Date</span>
                <span className="text-slate-800">
                  {new Date(report.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </PinnedCard>

          {/* Comps */}
          {report.comps && report.comps.length > 0 && (
            <PinnedCard title="Comparable Shows" colorIndex={2}>
              <div className="flex flex-wrap gap-2">
                {report.comps.map((comp) => (
                  <span
                    key={comp}
                    className="px-3 py-1 rounded-full bg-white/80 border border-amber-200 text-sm text-amber-900 font-medium"
                  >
                    {comp}
                  </span>
                ))}
              </div>
            </PinnedCard>
          )}

          {/* Analyst Comments */}
          <PinnedCard title="Analyst Comments" colorIndex={3}>
            {report.strengths?.length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-semibold text-green-700 uppercase tracking-wide mb-2">
                  Strengths
                </p>
                <ul className="space-y-1">
                  {report.strengths.map((s, i) => (
                    <li key={i} className="text-slate-700 text-sm flex gap-2">
                      <span className="text-green-600 font-bold mt-0.5">✓</span>
                      <span>{s}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {report.weaknesses?.length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-semibold text-red-700 uppercase tracking-wide mb-2">
                  Weaknesses
                </p>
                <ul className="space-y-1">
                  {report.weaknesses.map((w, i) => (
                    <li key={i} className="text-slate-700 text-sm flex gap-2">
                      <span className="text-red-500 font-bold mt-0.5">•</span>
                      <span>{w}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {report.overall_comments && (
              <div>
                <p className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2">
                  Overall Comments
                </p>
                <div className="space-y-1">{renderParagraphs(report.overall_comments)}</div>
              </div>
            )}

            {!report.strengths?.length &&
              !report.weaknesses?.length &&
              !report.overall_comments && (
                <p className="text-slate-400 italic">No analyst comments</p>
              )}
          </PinnedCard>

          {/* Character Notes */}
          {report.character_notes && (
            <PinnedCard title="Character Notes" colorIndex={2}>
              <div className="space-y-1">{renderParagraphs(report.character_notes)}</div>
            </PinnedCard>
          )}

          {/* Structure Analysis */}
          {report.structure_analysis && (
            <PinnedCard title="Structure Analysis" colorIndex={3}>
              <div className="space-y-1">{renderParagraphs(report.structure_analysis)}</div>
            </PinnedCard>
          )}

          {/* Market Positioning */}
          {report.market_positioning && (
            <PinnedCard title="Market Positioning" colorIndex={4}>
              <div className="space-y-1">{renderParagraphs(report.market_positioning)}</div>
            </PinnedCard>
          )}
        </div>

        {/* Right Column */}
        <div className="lg:col-span-7 space-y-6">
          {/* Scorecard */}
          {subscoreEntries.length > 0 && (
            <PinnedCard title="Scorecard" colorIndex={4}>
              <div className="space-y-4">
                {subscoreEntries.map(({ key, score }) => (
                  <ScoreRow key={key} label={labelForKey(key)} score={score} />
                ))}

                {/* Total Score */}
                <div className="pt-4 border-t border-amber-200/50">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800">Total Score</span>
                    <span
                      className={`text-2xl font-bold ${
                        (totalScore ?? 0) >= 40
                          ? 'text-green-600'
                          : (totalScore ?? 0) >= 30
                          ? 'text-yellow-600'
                          : 'text-red-600'
                      }`}
                    >
                      {totalScore !== null ? `${totalScore}/50` : '—'}
                    </span>
                  </div>
                </div>
              </div>
            </PinnedCard>
          )}

          {/* Mandate Checklist */}
          {mandateChecklistEntries.length > 0 && (
            <PinnedCard title="Mandate Checklist" colorIndex={5}>
              <div className="grid grid-cols-2 gap-4">
                {mandateChecklistEntries.map(({ key, label, item }) => (
                  <MandateItem
                    key={key}
                    checked={item.result}
                    label={label}
                    rationale={item.rationale}
                  />
                ))}
              </div>
            </PinnedCard>
          )}

          {/* Evidence Quotes */}
          {report.evidence_quotes?.length > 0 && (
            <PinnedCard title="Evidence Quotes" colorIndex={2}>
              <div className="space-y-4">
                {report.evidence_quotes.map((q, i) => (
                  <div
                    key={i}
                    className="bg-white/60 rounded-lg p-3 border border-amber-100"
                  >
                    <span className="text-xs font-semibold text-amber-700 uppercase tracking-wide">
                      Page {q.page}
                    </span>
                    <blockquote className="mt-2 text-slate-700 text-sm italic leading-relaxed border-l-2 border-amber-400 pl-3">
                      "{q.quote}"
                    </blockquote>
                    {q.context && (
                      <p className="mt-1 text-xs text-slate-500">{q.context}</p>
                    )}
                  </div>
                ))}
              </div>
            </PinnedCard>
          )}

          {/* Export */}
          <PinnedCard title="Export Report" colorIndex={3}>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={onExportGoogleDoc}
                disabled={exporting.googleDoc}
                type="button"
                className="flex items-center justify-center gap-2 px-4 py-3 bg-white border border-amber-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-amber-50 transition-colors disabled:opacity-60"
              >
                {exporting.googleDoc ? 'Creating…' : '📄 Google Doc'}
              </button>
              <button
                onClick={onExportPDF}
                disabled={exporting.pdf}
                type="button"
                className="flex items-center justify-center gap-2 px-4 py-3 bg-amber-500 text-white rounded-lg text-sm font-medium hover:bg-amber-600 transition-colors disabled:opacity-60"
              >
                {exporting.pdf ? 'Generating…' : '📑 Download PDF'}
              </button>
            </div>
          </PinnedCard>
        </div>
      </div>
    </div>
  )
}

// ─── History Panel ────────────────────────────────────────────────────────────

function recommendationClass(recommendation?: string) {
  if (recommendation === 'Recommend') return 'badge-recommend'
  if (recommendation === 'Consider') return 'badge-consider'
  return 'badge-pass'
}

function HistoryPanel({ items, onSelect }: { items: HistoryItem[]; onSelect: (id: string) => void }) {
  if (!items.length) {
    return (
      <div className="empty-state">
        No reports yet. Generate your first coverage report to build a history.
      </div>
    )
  }
  return (
    <div className="history-list">
      {items.map((item) => (
        <button key={item.id} type="button" className="history-card" onClick={() => onSelect(item.id)}>
          <div>
            <h3>{item.title || 'Untitled Script'}</h3>
            <p>
              {item.genre || 'Unspecified genre'} • {item.analysis_depth} •{' '}
              {new Date(item.created_at).toLocaleDateString()}
            </p>
            <p className="history-model">{item.model_used}</p>
          </div>
          <div className="history-score">
            <strong>{item.total_score ?? '—'}/50</strong>
            <span className={`recommendation-pill ${recommendationClass(item.recommendation)}`}>
              {item.recommendation || 'Pending'}
            </span>
          </div>
        </button>
      ))}
    </div>
  )
}

// ─── Admin Page ────────────────────────────────────────────────────────────────

function AdminPage() {
  const [entries, setEntries] = useState<KnowledgeEntry[]>([])
  const [category, setCategory] = useState('general')
  const [content, setContent] = useState('')
  const [error, setError] = useState('')

  const loadEntries = useCallback(async () => {
    const response = await axios.get(`${API_BASE}/api/coverage/admin/knowledge`)
    setEntries(response.data.entries)
  }, [])

  useEffect(() => {
    void loadEntries()
  }, [loadEntries])

  const grouped = useMemo(
    () =>
      entries.reduce<Record<string, KnowledgeEntry[]>>((acc, entry) => {
        acc[entry.category] = acc[entry.category] || []
        acc[entry.category].push(entry)
        return acc
      }, {}),
    [entries],
  )

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await axios.post(`${API_BASE}/api/coverage/admin/knowledge`, { category, content })
      setContent('')
      setError('')
      await loadEntries()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || 'Failed to save knowledge')
    }
  }

  const handleDelete = async (id: string) => {
    await axios.delete(`${API_BASE}/api/coverage/admin/knowledge/${id}`)
    await loadEntries()
  }

  return (
    <div className="container">
      <header>
        <h1>
          <span className="logo-icon">🧠</span>CoverageIQ Admin
        </h1>
        <p>Domain knowledge store for better script coverage.</p>
      </header>
      <main>
        <form onSubmit={handleCreate}>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="category">Category</label>
              <input
                id="category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="general, drama, comedy..."
              />
            </div>
          </div>
          <div className="form-group full-width">
            <label htmlFor="content">Knowledge Entry</label>
            <textarea
              id="content"
              rows={8}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Add coverage heuristics, genre patterns, buyer language, or notes from great reports..."
            />
          </div>
          <button type="submit" disabled={!category.trim() || !content.trim()}>
            Add Knowledge Entry
          </button>
        </form>

        {error && <div className="error">{error}</div>}

        <div className="admin-groups">
          {Object.keys(grouped).length === 0 ? (
            <div className="empty-state">No domain knowledge yet.</div>
          ) : (
            Object.entries(grouped).map(([group, items]) => (
              <div className="admin-group" key={group}>
                <h3>{group}</h3>
                <div className="knowledge-list">
                  {items.map((entry) => (
                    <div className="knowledge-card" key={entry.id}>
                      <p>{entry.content}</p>
                      <button
                        type="button"
                        className="danger-btn"
                        onClick={() => void handleDelete(entry.id)}
                      >
                        Delete
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </main>
    </div>
  )
}

// ─── Main App ─────────────────────────────────────────────────────────────────

function App() {
  const [scriptContent, setScriptContent] = useState('')
  const [scriptFile, setScriptFile] = useState<File | null>(null)
  const [scriptTitle, setScriptTitle] = useState('')
  const [genre, setGenre] = useState('drama')
  const [comps, setComps] = useState('')
  const [analysisDepth, setAnalysisDepth] = useState('standard')
  const [activeTab, setActiveTab] = useState<'new' | 'history'>('new')
  const [report, setReport] = useState<CoverageReport | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState('')
  const [exporting, setExporting] = useState({ pdf: false, googleDoc: false })
  const [flagging, setFlagging] = useState(false)

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const loadHistory = useCallback(async () => {
    const response = await axios.get(`${API_BASE}/api/coverage/history`)
    setHistory(response.data.items || [])
  }, [])

  useEffect(() => {
    void loadHistory()
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [loadHistory])

  const fetchReport = useCallback(
    async (reportId: string) => {
      const response = await axios.get(`${API_BASE}/api/coverage/${reportId}`)
      setReport(response.data)
      setActiveTab('history')
      await loadHistory()
    },
    [loadHistory],
  )

  const startPolling = useCallback(
    (jobId: string, reportId: string) => {
      if (pollingRef.current) clearInterval(pollingRef.current)
      const poll = async () => {
        try {
          const response = await axios.get(`${API_BASE}/api/coverage/jobs/${jobId}/status`)
          const status: JobStatus = response.data
          setJobStatus(status)
          if (status.status === 'completed') {
            if (pollingRef.current) clearInterval(pollingRef.current)
            setIsAnalyzing(false)
            await fetchReport(reportId)
          }
          if (status.status === 'failed') {
            if (pollingRef.current) clearInterval(pollingRef.current)
            setIsAnalyzing(false)
            setError(status.error_message || 'Analysis failed')
          }
        } catch (err) {
          console.error(err)
        }
      }
      void poll()
      pollingRef.current = setInterval(() => {
        void poll()
      }, 2000)
    },
    [fetchReport],
  )

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setReport(null)
    setIsAnalyzing(true)
    try {
      let scriptId: string
      let scriptText: string
      if (scriptFile) {
        const formData = new FormData()
        formData.append('file', scriptFile)
        formData.append('title', scriptTitle || scriptFile.name.replace(/\.[^/.]+$/, ''))
        formData.append('content_type', 'tv_pilot')
        const uploadRes = await axios.post(`${API_BASE}/api/scripts/upload-file`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        scriptId = uploadRes.data.script_id
        scriptText = uploadRes.data.extracted_text || ''
      } else {
        const uploadRes = await axios.post(`${API_BASE}/api/scripts/upload`, {
          title: scriptTitle || 'Untitled Script',
          content: scriptContent,
          content_type: 'tv_pilot',
        })
        scriptId = uploadRes.data.script_id
        scriptText = scriptContent
      }
      const asyncRes = await axios.post(`${API_BASE}/api/coverage/generate-async`, {
        script_id: scriptId,
        script_text: scriptText,
        genre,
        comps: comps
          ? comps
              .split(',')
              .map((c) => c.trim())
              .filter(Boolean)
          : [],
        analysis_depth: analysisDepth,
      })
      startPolling(asyncRes.data.job_id, asyncRes.data.report_id)
    } catch (err: unknown) {
      setIsAnalyzing(false)
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || 'Failed to generate report')
    }
  }

  const handleExportPDF = async () => {
    if (!report) return
    setExporting((prev) => ({ ...prev, pdf: true }))
    try {
      const response = await axios.post(
        `${API_BASE}/api/coverage/${report.report_id}/export/pdf`,
        {},
        { responseType: 'blob' },
      )
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = `coverage_report_${report.report_id}.pdf`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } finally {
      setExporting((prev) => ({ ...prev, pdf: false }))
    }
  }

  const handleExportGoogleDoc = async () => {
    if (!report) return
    setExporting((prev) => ({ ...prev, googleDoc: true }))
    try {
      const response = await axios.post(
        `${API_BASE}/api/coverage/${report.report_id}/export/google-doc`,
        { email: 'philipriccio@gmail.com' },
      )
      if (response.data.url) window.open(response.data.url, '_blank')
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || 'Failed to export to Google Doc')
    } finally {
      setExporting((prev) => ({ ...prev, googleDoc: false }))
    }
  }

  const handleFlagExample = async () => {
    if (!report) return
    setFlagging(true)
    try {
      await axios.post(`${API_BASE}/api/coverage/${report.report_id}/flag-example`)
      setReport({ ...report, is_flagged_example: true })
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || 'Failed to flag report as example')
    } finally {
      setFlagging(false)
    }
  }

  if (isAdminRoute) return <AdminPage />

  // When viewing a report, render full-page corkboard UI (outside the container)
  if (report) {
    return (
      <>
        <ReportViewer
          report={report}
          onBack={() => {
            setReport(null)
            void loadHistory()
          }}
          onExportPDF={handleExportPDF}
          onExportGoogleDoc={handleExportGoogleDoc}
          onFlagExample={handleFlagExample}
          exporting={exporting}
          flagging={flagging}
        />
        {error && (
          <div className="fixed bottom-4 right-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg shadow-lg">
            {error}
          </div>
        )}
      </>
    )
  }

  return (
    <div className="container">
      <header>
        <h1>
          <span className="logo-icon">🎬</span>CoverageIQ
        </h1>
        <p>AI-powered script coverage for TV pilots &amp; features</p>
      </header>
      <main>
        {isAnalyzing && (
          <div className="analyzing-overlay">
            <div className="analyzing-content">
              <ProgressBar
                progress={jobStatus?.progress || 0}
                status={jobStatus?.status || 'queued'}
                message={
                  jobStatus?.status === 'queued' ? 'Starting analysis...' : undefined
                }
              />
            </div>
          </div>
        )}

        <div className="tab-row">
          <button
            type="button"
            className={`tab-btn ${activeTab === 'new' ? 'active' : ''}`}
            onClick={() => setActiveTab('new')}
          >
            New Analysis
          </button>
          <button
            type="button"
            className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('history')
              void loadHistory()
            }}
          >
            History
          </button>
        </div>

        {activeTab === 'new' ? (
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="title">Script Title</label>
                <input
                  id="title"
                  value={scriptTitle}
                  onChange={(e) => setScriptTitle(e.target.value)}
                  placeholder="e.g., The Last Frontier"
                />
              </div>
              <div className="form-group">
                <label htmlFor="genre">Genre</label>
                <select id="genre" value={genre} onChange={(e) => setGenre(e.target.value)}>
                  <option value="drama">Drama</option>
                  <option value="comedy">Comedy</option>
                  <option value="thriller">Thriller</option>
                  <option value="sci-fi">Sci-Fi</option>
                  <option value="crime">Crime</option>
                  <option value="horror">Horror</option>
                  <option value="procedural">Procedural</option>
                </select>
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="comps">Comparable Series</label>
                <input
                  id="comps"
                  value={comps}
                  onChange={(e) => setComps(e.target.value)}
                  placeholder="e.g., Northern Exposure, ER"
                />
              </div>
              <div className="form-group">
                <label htmlFor="depth">Analysis Depth</label>
                <select
                  id="depth"
                  value={analysisDepth}
                  onChange={(e) => setAnalysisDepth(e.target.value)}
                >
                  <option value="quick">Quick</option>
                  <option value="standard">Standard</option>
                  <option value="deep">Deep</option>
                </select>
              </div>
            </div>
            <div className="form-group full-width">
              <label htmlFor="scriptFile">Upload Script File (PDF or Final Draft)</label>
              <input
                id="scriptFile"
                type="file"
                accept=".pdf,.fdx"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) {
                    setScriptFile(file)
                    setScriptContent('')
                  }
                }}
              />
              {scriptFile && <p className="file-selected">Selected: {scriptFile.name}</p>}
            </div>
            <div className="form-group full-width">
              <label htmlFor="script">Or Paste Script Text</label>
              <textarea
                id="script"
                rows={20}
                value={scriptContent}
                onChange={(e) => {
                  setScriptContent(e.target.value)
                  setScriptFile(null)
                }}
                placeholder="Paste your TV pilot script here..."
                disabled={!!scriptFile}
              />
            </div>
            <button type="submit" disabled={isAnalyzing || (!scriptFile && !scriptContent)}>
              Generate Coverage Report
            </button>
          </form>
        ) : (
          <HistoryPanel items={history} onSelect={(id) => void fetchReport(id)} />
        )}

        {error && <div className="error">{error}</div>}
      </main>
      <footer>
        <p>CoverageIQ Upgrade Sprint • GPT-4.1 + history + knowledge base</p>
      </footer>
    </div>
  )
}

export default App
