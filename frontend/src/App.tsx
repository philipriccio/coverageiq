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

// ─── JSON field parsers for character_notes and structure_analysis ───────────

function tryParseJSON(value: string): unknown | null {
  try {
    return JSON.parse(value)
  } catch {
    return null
  }
}

function CharacterNotesRenderer({ value }: { value: string }) {
  const parsed = tryParseJSON(value) as {
    protagonist?: { name?: string; assessment?: string; series_runway?: string }
    supporting_cast?: { assessment?: string; standouts?: string[]; concerns?: string[] }
    character_dynamics?: string
  } | null

  if (!parsed) {
    // plain text fallback
    return (
      <div className="space-y-1">
        {value.split('\n').filter(Boolean).map((line, i) => (
          <p key={i} className="text-slate-700 text-sm leading-relaxed">{line}</p>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {parsed.protagonist && (
        <div>
          <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-1">
            Protagonist{parsed.protagonist.name ? ` — ${parsed.protagonist.name}` : ''}
          </p>
          {parsed.protagonist.assessment && (
            <p className="text-slate-700 text-sm leading-relaxed mb-1">{parsed.protagonist.assessment}</p>
          )}
          {parsed.protagonist.series_runway && (
            <p className="text-slate-600 text-sm leading-relaxed italic">{parsed.protagonist.series_runway}</p>
          )}
        </div>
      )}
      {parsed.supporting_cast && (
        <div>
          <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-1">Supporting Cast</p>
          {parsed.supporting_cast.assessment && (
            <p className="text-slate-700 text-sm leading-relaxed mb-2">{parsed.supporting_cast.assessment}</p>
          )}
          {parsed.supporting_cast.standouts && parsed.supporting_cast.standouts.length > 0 && (
            <div className="mb-1">
              <p className="text-xs font-medium text-slate-500 mb-1">Standouts</p>
              <div className="flex flex-wrap gap-1">
                {parsed.supporting_cast.standouts.map((name, i) => (
                  <span key={i} className="px-2 py-0.5 rounded-full bg-white/70 border border-amber-200 text-xs text-amber-900 font-medium">{name}</span>
                ))}
              </div>
            </div>
          )}
          {parsed.supporting_cast.concerns && parsed.supporting_cast.concerns.length > 0 && (
            <div>
              <p className="text-xs font-medium text-slate-500 mb-1">Concerns</p>
              {parsed.supporting_cast.concerns.map((c, i) => (
                <p key={i} className="text-slate-600 text-sm italic">{c}</p>
              ))}
            </div>
          )}
        </div>
      )}
      {parsed.character_dynamics && (
        <div>
          <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-1">Character Dynamics</p>
          <p className="text-slate-700 text-sm leading-relaxed">{parsed.character_dynamics}</p>
        </div>
      )}
    </div>
  )
}

const structureKeyLabels: Record<string, string> = {
  pilot_type: 'Pilot Type',
  act_breaks: 'Act Breaks',
  pacing: 'Pacing',
  cold_open: 'Cold Open',
  act_one: 'Act One',
  act_two: 'Act Two',
  act_three: 'Act Three',
  tag: 'Tag / Coda',
}

function StructureAnalysisRenderer({ value }: { value: string }) {
  const parsed = tryParseJSON(value) as Record<string, string> | null

  if (!parsed) {
    return (
      <div className="space-y-1">
        {value.split('\n').filter(Boolean).map((line, i) => (
          <p key={i} className="text-slate-700 text-sm leading-relaxed">{line}</p>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {Object.entries(parsed).map(([key, val]) => (
        <div key={key}>
          <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-0.5">
            {structureKeyLabels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
          </p>
          <p className="text-slate-700 text-sm leading-relaxed">{String(val)}</p>
        </div>
      ))}
    </div>
  )
}

// ─── Market Positioning renderer ─────────────────────────────────────────────

const marketPositioningTextFields: Array<{ key: string; label: string }> = [
  { key: 'genre', label: 'Genre' },
  { key: 'tone', label: 'Tone' },
  { key: 'target_network', label: 'Target Network' },
  { key: 'target_audience', label: 'Target Audience' },
  { key: 'market_timing', label: 'Market Timing' },
  { key: 'castability', label: 'Castability' },
  { key: 'production_considerations', label: 'Production Considerations' },
]

function MarketPositioningRenderer({ value }: { value: string }) {
  const parsed = tryParseJSON(value) as {
    genre?: string
    tone?: string
    comparable_series?: string[]
    target_network?: string
    target_audience?: string
    market_timing?: string
    castability?: string
    production_considerations?: string
  } | null

  if (!parsed) {
    return (
      <div className="space-y-1">
        {value.split('\n').filter(Boolean).map((line, i) => (
          <p key={i} className="text-slate-700 text-sm leading-relaxed">{line}</p>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {marketPositioningTextFields.map(({ key, label }) => {
        const val = (parsed as Record<string, unknown>)[key]
        if (!val) return null
        return (
          <div key={key}>
            <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-0.5">{label}</p>
            <p className="text-slate-700 text-sm leading-relaxed">{String(val)}</p>
          </div>
        )
      })}
      {parsed.comparable_series && parsed.comparable_series.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-1">Comparable Series</p>
          <div className="flex flex-wrap gap-2">
            {parsed.comparable_series.map((s, i) => (
              <span key={i} className="px-3 py-1 rounded-full bg-white/80 border border-amber-200 text-sm text-amber-900 font-medium">{s}</span>
            ))}
          </div>
        </div>
      )}
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
              <CharacterNotesRenderer value={report.character_notes} />
            </PinnedCard>
          )}

          {/* Structure Analysis */}
          {report.structure_analysis && (
            <PinnedCard title="Structure Analysis" colorIndex={3}>
              <StructureAnalysisRenderer value={report.structure_analysis} />
            </PinnedCard>
          )}

          {/* Market Positioning */}
          {report.market_positioning && (
            <PinnedCard title="Market Positioning" colorIndex={4}>
              <MarketPositioningRenderer value={report.market_positioning} />
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

            {/* Save to CRM — only shown when embedded in Hawco CRM */}
            {typeof window !== 'undefined' && window.self !== window.top && (
              <button
                onClick={() => {
                  const subscores: Record<string, number> = {}
                  Object.entries(report.subscores || {}).forEach(([key, value]) => {
                    subscores[key] = typeof value === 'number' ? value : (value as { score?: number }).score ?? 0
                  })
                  window.parent.postMessage(
                    {
                      type: 'COVERAGEIQ_SAVE',
                      payload: {
                        title: report.title ?? 'AI Coverage',
                        verdict: (report.recommendation ?? 'PASS').toUpperCase(),
                        total_score: report.total_score ?? null,
                        subscores,
                        summary: report.synopsis ?? report.logline ?? '',
                        raw_report: report,
                      },
                    },
                    '*'
                  )
                }}
                type="button"
                className="mt-3 w-full flex items-center justify-center gap-2 px-4 py-3 bg-violet-600 text-white rounded-lg text-sm font-medium hover:bg-violet-700 transition-colors"
              >
                💾 Save to CRM Project
              </button>
            )}
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

const CATEGORY_OPTIONS = [
  'general', 'drama', 'comedy', 'thriller', 'mystery',
  'procedural', 'canadian', 'horror', 'sci-fi', 'period', 'calibration',
]

function extractTitle(content: string): string {
  const firstLine = content.split('\n').find(l => l.trim()) || ''
  return firstLine.replace(/^BENCHMARK:\s*/i, '').trim() || 'Untitled Entry'
}

function extractPreview(content: string): string {
  return content.split('\n').filter(Boolean).slice(0, 3).join('\n')
}

function KnowledgeCard({
  entry,
  onDelete,
  onSaved,
}: {
  entry: KnowledgeEntry
  onDelete: (id: string) => void
  onSaved: (updated: KnowledgeEntry) => void
}) {
  const [editing, setEditing] = useState(false)
  const [editCategory, setEditCategory] = useState(entry.category)
  const [editContent, setEditContent] = useState(entry.content)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      const res = await axios.patch(`${API_BASE}/api/coverage/admin/knowledge/${entry.id}`, {
        category: editCategory,
        content: editContent,
      })
      onSaved(res.data as KnowledgeEntry)
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  const handleCancel = () => {
    setEditCategory(entry.category)
    setEditContent(entry.content)
    setEditing(false)
  }

  const title = extractTitle(entry.content)
  const preview = extractPreview(entry.content)

  if (editing) {
    return (
      <div style={{
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '0.75rem',
        padding: '1rem',
        marginBottom: '0.75rem',
      }}>
        <div style={{ marginBottom: '0.75rem' }}>
          <label style={{ color: '#94a3b8', fontSize: '0.75rem', fontWeight: 600, display: 'block', marginBottom: '0.25rem' }}>
            CATEGORY
          </label>
          <select
            value={editCategory}
            onChange={e => setEditCategory(e.target.value)}
            style={{
              background: '#0f172a',
              color: '#e2e8f0',
              border: '1px solid #475569',
              borderRadius: '0.5rem',
              padding: '0.4rem 0.75rem',
              fontSize: '0.875rem',
              width: '100%',
            }}
          >
            {CATEGORY_OPTIONS.map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
        <div style={{ marginBottom: '0.75rem' }}>
          <label style={{ color: '#94a3b8', fontSize: '0.75rem', fontWeight: 600, display: 'block', marginBottom: '0.25rem' }}>
            CONTENT
          </label>
          <textarea
            value={editContent}
            onChange={e => setEditContent(e.target.value)}
            rows={12}
            style={{
              background: '#0f172a',
              color: '#e2e8f0',
              border: '1px solid #475569',
              borderRadius: '0.5rem',
              padding: '0.5rem 0.75rem',
              fontSize: '0.8rem',
              width: '100%',
              fontFamily: 'monospace',
              resize: 'vertical',
              boxSizing: 'border-box',
            }}
          />
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={saving}
            style={{
              background: '#d97706',
              color: '#fff',
              border: 'none',
              borderRadius: '0.5rem',
              padding: '0.4rem 1rem',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              opacity: saving ? 0.6 : 1,
            }}
          >
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button
            type="button"
            onClick={handleCancel}
            style={{
              background: '#334155',
              color: '#e2e8f0',
              border: 'none',
              borderRadius: '0.5rem',
              padding: '0.4rem 1rem',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={{
      background: '#1e293b',
      border: '1px solid #334155',
      borderRadius: '0.75rem',
      padding: '0.875rem 1rem',
      marginBottom: '0.75rem',
      display: 'flex',
      gap: '1rem',
      alignItems: 'flex-start',
    }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
          <span style={{
            fontWeight: 700,
            color: '#e2e8f0',
            fontSize: '0.9rem',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}>{title}</span>
          <span style={{
            background: '#0f172a',
            color: '#f59e0b',
            border: '1px solid #f59e0b44',
            borderRadius: '99px',
            padding: '0.1rem 0.6rem',
            fontSize: '0.7rem',
            fontWeight: 700,
            flexShrink: 0,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}>{entry.category}</span>
        </div>
        <pre style={{
          color: '#64748b',
          fontSize: '0.75rem',
          margin: 0,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          fontFamily: 'inherit',
          lineHeight: 1.5,
        }}>{preview}</pre>
      </div>
      <div style={{ display: 'flex', gap: '0.4rem', flexShrink: 0 }}>
        <button
          type="button"
          onClick={() => setEditing(true)}
          style={{
            background: '#334155',
            color: '#e2e8f0',
            border: 'none',
            borderRadius: '0.4rem',
            padding: '0.3rem 0.75rem',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Edit
        </button>
        <button
          type="button"
          onClick={() => onDelete(entry.id)}
          style={{
            background: '#7f1d1d',
            color: '#fca5a5',
            border: 'none',
            borderRadius: '0.4rem',
            padding: '0.3rem 0.75rem',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Delete
        </button>
      </div>
    </div>
  )
}

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
    if (!confirm('Delete this entry?')) return
    await axios.delete(`${API_BASE}/api/coverage/admin/knowledge/${id}`)
    await loadEntries()
  }

  const handleSaved = (updated: KnowledgeEntry) => {
    setEntries(prev => prev.map(e => e.id === updated.id ? updated : e))
  }

  // Sort categories: known ones first, then alphabetical
  const categoryOrder = [...CATEGORY_OPTIONS, 'calibration']
  const sortedGroups = Object.entries(grouped).sort(([a], [b]) => {
    const ai = categoryOrder.indexOf(a)
    const bi = categoryOrder.indexOf(b)
    if (ai === -1 && bi === -1) return a.localeCompare(b)
    if (ai === -1) return 1
    if (bi === -1) return -1
    return ai - bi
  })

  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', color: '#e2e8f0', padding: '2rem' }}>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f59e0b', margin: 0 }}>
            🧠 Benchmark Manager
          </h1>
          <p style={{ color: '#64748b', margin: '0.25rem 0 0', fontSize: '0.9rem' }}>
            Manage domain knowledge entries — edit categories, content, and move benchmarks between groups.
          </p>
        </div>

        {/* New Entry Form */}
        <div style={{
          background: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '0.75rem',
          padding: '1.25rem',
          marginBottom: '2rem',
        }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#94a3b8', margin: '0 0 1rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            New Entry
          </h2>
          <form onSubmit={(e) => void handleCreate(e)}>
            <div style={{ marginBottom: '0.75rem' }}>
              <label style={{ color: '#94a3b8', fontSize: '0.75rem', fontWeight: 600, display: 'block', marginBottom: '0.25rem' }}>
                CATEGORY
              </label>
              <select
                value={category}
                onChange={e => setCategory(e.target.value)}
                style={{
                  background: '#0f172a',
                  color: '#e2e8f0',
                  border: '1px solid #475569',
                  borderRadius: '0.5rem',
                  padding: '0.4rem 0.75rem',
                  fontSize: '0.875rem',
                  width: '100%',
                }}
              >
                {CATEGORY_OPTIONS.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div style={{ marginBottom: '0.75rem' }}>
              <label style={{ color: '#94a3b8', fontSize: '0.75rem', fontWeight: 600, display: 'block', marginBottom: '0.25rem' }}>
                CONTENT
              </label>
              <textarea
                rows={6}
                value={content}
                onChange={e => setContent(e.target.value)}
                placeholder="Add coverage heuristics, genre patterns, buyer language, or benchmark notes..."
                style={{
                  background: '#0f172a',
                  color: '#e2e8f0',
                  border: '1px solid #475569',
                  borderRadius: '0.5rem',
                  padding: '0.5rem 0.75rem',
                  fontSize: '0.875rem',
                  width: '100%',
                  fontFamily: 'monospace',
                  resize: 'vertical',
                  boxSizing: 'border-box',
                }}
              />
            </div>
            {error && (
              <div style={{ color: '#f87171', fontSize: '0.85rem', marginBottom: '0.75rem' }}>{error}</div>
            )}
            <button
              type="submit"
              disabled={!category.trim() || !content.trim()}
              style={{
                background: '#d97706',
                color: '#fff',
                border: 'none',
                borderRadius: '0.5rem',
                padding: '0.5rem 1.5rem',
                fontWeight: 700,
                fontSize: '0.875rem',
                cursor: 'pointer',
                opacity: (!category.trim() || !content.trim()) ? 0.5 : 1,
              }}
            >
              Add Entry
            </button>
          </form>
        </div>

        {/* Grouped entries */}
        <div>
          {sortedGroups.length === 0 ? (
            <div style={{ color: '#64748b', textAlign: 'center', padding: '2rem' }}>No domain knowledge yet.</div>
          ) : (
            sortedGroups.map(([group, items]) => (
              <div key={group} style={{ marginBottom: '2rem' }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  marginBottom: '0.75rem',
                  paddingBottom: '0.5rem',
                  borderBottom: '1px solid #1e293b',
                }}>
                  <h3 style={{ margin: 0, color: '#f59e0b', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', fontSize: '0.9rem' }}>
                    {group}
                  </h3>
                  <span style={{ color: '#64748b', fontSize: '0.8rem' }}>{items.length} {items.length === 1 ? 'entry' : 'entries'}</span>
                </div>
                <div>
                  {items.map(entry => (
                    <KnowledgeCard
                      key={entry.id}
                      entry={entry}
                      onDelete={(id) => void handleDelete(id)}
                      onSaved={handleSaved}
                    />
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Main App ─────────────────────────────────────────────────────────────────

function App() {
  const [scriptFile, setScriptFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
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
    if (!scriptFile) return
    setError('')
    setReport(null)
    setIsAnalyzing(true)
    try {
      const formData = new FormData()
      formData.append('file', scriptFile)
      formData.append('title', scriptFile.name.replace(/\.[^/.]+$/, ''))
      formData.append('content_type', 'tv_pilot')
      const uploadRes = await axios.post(`${API_BASE}/api/scripts/upload-file`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const scriptId: string = uploadRes.data.script_id
      const scriptText: string = uploadRes.data.extracted_text || ''
      const asyncRes = await axios.post(`${API_BASE}/api/coverage/generate-async`, {
        script_id: scriptId,
        script_text: scriptText,
        genre: '',
        comps: [],
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
              <label>Script File</label>
              {/* Drop zone */}
              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={(e) => {
                  e.preventDefault()
                  setIsDragging(false)
                  const file = e.dataTransfer.files?.[0]
                  if (file) setScriptFile(file)
                }}
                onClick={() => document.getElementById('scriptFileInput')?.click()}
                style={{
                  border: `2px dashed ${isDragging ? '#d97706' : '#fbbf24'}`,
                  borderRadius: '0.75rem',
                  padding: '2.5rem 1.5rem',
                  textAlign: 'center',
                  cursor: 'pointer',
                  background: isDragging ? 'rgba(251,191,36,0.08)' : 'rgba(255,251,235,0.6)',
                  transition: 'all 0.15s ease',
                }}
              >
                {scriptFile ? (
                  <p style={{ color: '#92400e', fontWeight: 600, margin: 0 }}>
                    📄 {scriptFile.name}
                  </p>
                ) : (
                  <>
                    <p style={{ color: '#b45309', fontWeight: 600, margin: '0 0 0.5rem' }}>
                      Drag &amp; drop your script here, or click to browse
                    </p>
                    <p style={{ color: '#a16207', fontSize: '0.85rem', margin: 0 }}>
                      Accepts .pdf and .fdx files
                    </p>
                  </>
                )}
              </div>
              <input
                id="scriptFileInput"
                type="file"
                accept=".pdf,.fdx"
                style={{ display: 'none' }}
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) setScriptFile(file)
                }}
              />
            </div>
            <button type="submit" disabled={isAnalyzing || !scriptFile}>
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
