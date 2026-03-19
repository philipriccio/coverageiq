import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
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

function CollapsibleSection({ title, children, defaultOpen = false }: { title: string; children: React.ReactNode; defaultOpen?: boolean }) {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  return (
    <div className="collapsible-section">
      <button className="section-header" onClick={() => setIsOpen(!isOpen)} type="button">
        <span className="section-title">{title}</span>
        <span className={`section-toggle ${isOpen ? 'open' : ''}`}>{isOpen ? '−' : '+'}</span>
      </button>
      {isOpen && <div className="section-content">{children}</div>}
    </div>
  )
}

function recommendationClass(recommendation?: string) {
  if (recommendation === 'Recommend') return 'badge-recommend'
  if (recommendation === 'Consider') return 'badge-consider'
  return 'badge-pass'
}

function ScoreBadge({ recommendation, totalScore }: { recommendation: string; totalScore: number }) {
  const borderColor = recommendation === 'Recommend' ? '#4caf50' : recommendation === 'Consider' ? '#ff9800' : '#e53935'
  return (
    <div className="score-badge" style={{ borderColor }}>
      <div className="score-total">
        <span className="score-number">{totalScore}</span>
        <span className="score-max">/50</span>
      </div>
      <div className={`recommendation ${recommendationClass(recommendation)}`}>{recommendation}</div>
    </div>
  )
}

function ReportViewer({ report, onBack, onExportPDF, onExportGoogleDoc, onFlagExample, exporting, flagging }: {
  report: CoverageReport
  onBack: () => void
  onExportPDF: () => void
  onExportGoogleDoc: () => void
  onFlagExample: () => void
  exporting: { pdf: boolean; googleDoc: boolean }
  flagging: boolean
}) {
  const subscoreEntries = Object.entries(report.subscores || {}).map(([key, value]) => ({ key, score: typeof value === 'number' ? value : value.score || 0 }))
  const renderParagraphs = (value?: string) => value?.split('\n').filter(Boolean).map((line, i) => <p key={i}>{line}</p>)

  return (
    <div className="report-container">
      <button className="back-btn" onClick={onBack} type="button">← Back</button>
      <div className="report-viewer">
        <div className="report-header">
          <div>
            <h2>{report.script_title || 'Untitled Script'}</h2>
            <p className="report-meta-line">{report.genre || 'Unspecified genre'} • {report.analysis_depth} • {new Date(report.created_at).toLocaleString()}</p>
          </div>
          <ScoreBadge recommendation={report.recommendation || 'Pass'} totalScore={report.total_score || 0} />
        </div>

        <div className="action-row">
          <button type="button" className="secondary-btn" onClick={onFlagExample} disabled={flagging || report.is_flagged_example}>
            {report.is_flagged_example ? '★ Saved as example' : flagging ? 'Saving example...' : '★ Flag as example'}
          </button>
        </div>

        <CollapsibleSection title="Score Breakdown" defaultOpen>
          <div className="subscores-container">
            {subscoreEntries.map(({ key, score }) => (
              <div className="subscore-item" key={key}>
                <div className="subscore-label">{key}</div>
                <div className="subscore-bar-container"><div className="subscore-bar" style={{ width: `${score * 10}%` }} /></div>
                <div className="subscore-value">{score}/10</div>
              </div>
            ))}
          </div>
        </CollapsibleSection>

        {report.logline && <CollapsibleSection title="Logline" defaultOpen><p className="logline">{report.logline}</p></CollapsibleSection>}
        {report.synopsis && <CollapsibleSection title="Synopsis">{renderParagraphs(report.synopsis)}</CollapsibleSection>}
        {report.overall_comments && <CollapsibleSection title="Overall Comments" defaultOpen>{renderParagraphs(report.overall_comments)}</CollapsibleSection>}
        {report.strengths?.length > 0 && <CollapsibleSection title="Strengths" defaultOpen><ul className="strengths-list">{report.strengths.map((item, i) => <li className="strength-item" key={i}>{item}</li>)}</ul></CollapsibleSection>}
        {report.weaknesses?.length > 0 && <CollapsibleSection title="Weaknesses"><ul className="weaknesses-list">{report.weaknesses.map((item, i) => <li className="weakness-item" key={i}>{item}</li>)}</ul></CollapsibleSection>}
        {report.character_notes && <CollapsibleSection title="Character Notes"><div className="formatted-content">{renderParagraphs(report.character_notes)}</div></CollapsibleSection>}
        {report.structure_analysis && <CollapsibleSection title="Structure Analysis"><div className="formatted-content">{renderParagraphs(report.structure_analysis)}</div></CollapsibleSection>}
        {report.market_positioning && <CollapsibleSection title="Market Positioning"><div className="formatted-content">{renderParagraphs(report.market_positioning)}</div></CollapsibleSection>}
        {report.evidence_quotes?.length > 0 && (
          <CollapsibleSection title="Evidence Quotes" defaultOpen>
            <div className="evidence-quotes-container">
              {report.evidence_quotes.map((quote, i) => (
                <div className="evidence-quote" key={i}>
                  <div className="quote-header"><span className="quote-page">Page {quote.page}</span></div>
                  <blockquote className="quote-text">“{quote.quote}”</blockquote>
                  {quote.context && <p className="quote-context">{quote.context}</p>}
                </div>
              ))}
            </div>
          </CollapsibleSection>
        )}

        <div className="export-section">
          <h3>Export Report</h3>
          <div className="export-buttons">
            <button onClick={onExportGoogleDoc} disabled={exporting.googleDoc} className="export-btn google-doc-btn" type="button">
              {exporting.googleDoc ? 'Creating Google Doc...' : '📄 Export to Google Doc'}
            </button>
            <button onClick={onExportPDF} disabled={exporting.pdf} className="export-btn pdf-btn" type="button">
              {exporting.pdf ? 'Generating PDF...' : '📑 Download PDF'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function HistoryPanel({ items, onSelect }: { items: HistoryItem[]; onSelect: (id: string) => void }) {
  if (!items.length) {
    return <div className="empty-state">No reports yet. Generate your first coverage report to build a history.</div>
  }
  return (
    <div className="history-list">
      {items.map((item) => (
        <button key={item.id} type="button" className="history-card" onClick={() => onSelect(item.id)}>
          <div>
            <h3>{item.title || 'Untitled Script'}</h3>
            <p>{item.genre || 'Unspecified genre'} • {item.analysis_depth} • {new Date(item.created_at).toLocaleDateString()}</p>
            <p className="history-model">{item.model_used}</p>
          </div>
          <div className="history-score">
            <strong>{item.total_score ?? '—'}/50</strong>
            <span className={`recommendation-pill ${recommendationClass(item.recommendation)}`}>{item.recommendation || 'Pending'}</span>
          </div>
        </button>
      ))}
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

  useEffect(() => { void loadEntries() }, [loadEntries])

  const grouped = useMemo(() => entries.reduce<Record<string, KnowledgeEntry[]>>((acc, entry) => {
    acc[entry.category] = acc[entry.category] || []
    acc[entry.category].push(entry)
    return acc
  }, {}), [entries])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await axios.post(`${API_BASE}/api/coverage/admin/knowledge`, { category, content })
      setContent('')
      setError('')
      await loadEntries()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save knowledge')
    }
  }

  const handleDelete = async (id: string) => {
    await axios.delete(`${API_BASE}/api/coverage/admin/knowledge/${id}`)
    await loadEntries()
  }

  return (
    <div className="container">
      <header>
        <h1><span className="logo-icon">🧠</span>CoverageIQ Admin</h1>
        <p>Domain knowledge store for better script coverage.</p>
      </header>
      <main>
        <form onSubmit={handleCreate}>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="category">Category</label>
              <input id="category" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="general, drama, comedy..." />
            </div>
          </div>
          <div className="form-group full-width">
            <label htmlFor="content">Knowledge Entry</label>
            <textarea id="content" rows={8} value={content} onChange={(e) => setContent(e.target.value)} placeholder="Add coverage heuristics, genre patterns, buyer language, or notes from great reports..." />
          </div>
          <button type="submit" disabled={!category.trim() || !content.trim()}>Add Knowledge Entry</button>
        </form>

        {error && <div className="error">{error}</div>}

        <div className="admin-groups">
          {Object.keys(grouped).length === 0 ? (
            <div className="empty-state">No domain knowledge yet.</div>
          ) : Object.entries(grouped).map(([group, items]) => (
            <div className="admin-group" key={group}>
              <h3>{group}</h3>
              <div className="knowledge-list">
                {items.map((entry) => (
                  <div className="knowledge-card" key={entry.id}>
                    <p>{entry.content}</p>
                    <button type="button" className="danger-btn" onClick={() => void handleDelete(entry.id)}>Delete</button>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}

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
    return () => { if (pollingRef.current) clearInterval(pollingRef.current) }
  }, [loadHistory])

  const fetchReport = useCallback(async (reportId: string) => {
    const response = await axios.get(`${API_BASE}/api/coverage/${reportId}`)
    setReport(response.data)
    setActiveTab('history')
    await loadHistory()
  }, [loadHistory])

  const startPolling = useCallback((jobId: string, reportId: string) => {
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
    pollingRef.current = setInterval(() => { void poll() }, 2000)
  }, [fetchReport])

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
        const uploadRes = await axios.post(`${API_BASE}/api/scripts/upload-file`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
        scriptId = uploadRes.data.script_id
        scriptText = uploadRes.data.extracted_text || ''
      } else {
        const uploadRes = await axios.post(`${API_BASE}/api/scripts/upload`, { title: scriptTitle || 'Untitled Script', content: scriptContent, content_type: 'tv_pilot' })
        scriptId = uploadRes.data.script_id
        scriptText = scriptContent
      }
      const asyncRes = await axios.post(`${API_BASE}/api/coverage/generate-async`, {
        script_id: scriptId,
        script_text: scriptText,
        genre,
        comps: comps ? comps.split(',').map((c) => c.trim()).filter(Boolean) : [],
        analysis_depth: analysisDepth,
      })
      startPolling(asyncRes.data.job_id, asyncRes.data.report_id)
    } catch (err: any) {
      setIsAnalyzing(false)
      setError(err.response?.data?.detail || 'Failed to generate report')
    }
  }

  const handleExportPDF = async () => {
    if (!report) return
    setExporting((prev) => ({ ...prev, pdf: true }))
    try {
      const response = await axios.post(`${API_BASE}/api/coverage/${report.report_id}/export/pdf`, {}, { responseType: 'blob' })
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
      const response = await axios.post(`${API_BASE}/api/coverage/${report.report_id}/export/google-doc`, { email: 'philipriccio@gmail.com' })
      if (response.data.url) window.open(response.data.url, '_blank')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to export to Google Doc')
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
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to flag report as example')
    } finally {
      setFlagging(false)
    }
  }

  if (isAdminRoute) return <AdminPage />

  return (
    <div className="container">
      <header>
        <h1><span className="logo-icon">🎬</span>CoverageIQ</h1>
        <p>AI-powered script coverage for TV pilots & features</p>
      </header>
      <main>
        {isAnalyzing && (
          <div className="analyzing-overlay">
            <div className="analyzing-content">
              <ProgressBar progress={jobStatus?.progress || 0} status={jobStatus?.status || 'queued'} message={jobStatus?.status === 'queued' ? 'Starting analysis...' : undefined} />
            </div>
          </div>
        )}

        {!report && (
          <>
            <div className="tab-row">
              <button type="button" className={`tab-btn ${activeTab === 'new' ? 'active' : ''}`} onClick={() => setActiveTab('new')}>New Analysis</button>
              <button type="button" className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`} onClick={() => { setActiveTab('history'); void loadHistory() }}>History</button>
            </div>

            {activeTab === 'new' ? (
              <form onSubmit={handleSubmit}>
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="title">Script Title</label>
                    <input id="title" value={scriptTitle} onChange={(e) => setScriptTitle(e.target.value)} placeholder="e.g., The Last Frontier" />
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
                    <input id="comps" value={comps} onChange={(e) => setComps(e.target.value)} placeholder="e.g., Northern Exposure, ER" />
                  </div>
                  <div className="form-group">
                    <label htmlFor="depth">Analysis Depth</label>
                    <select id="depth" value={analysisDepth} onChange={(e) => setAnalysisDepth(e.target.value)}>
                      <option value="quick">Quick</option>
                      <option value="standard">Standard</option>
                      <option value="deep">Deep</option>
                    </select>
                  </div>
                </div>
                <div className="form-group full-width">
                  <label htmlFor="scriptFile">Upload Script File (PDF or Final Draft)</label>
                  <input id="scriptFile" type="file" accept=".pdf,.fdx" onChange={(e) => { const file = e.target.files?.[0]; if (file) { setScriptFile(file); setScriptContent('') } }} />
                  {scriptFile && <p className="file-selected">Selected: {scriptFile.name}</p>}
                </div>
                <div className="form-group full-width">
                  <label htmlFor="script">Or Paste Script Text</label>
                  <textarea id="script" rows={20} value={scriptContent} onChange={(e) => { setScriptContent(e.target.value); setScriptFile(null) }} placeholder="Paste your TV pilot script here..." disabled={!!scriptFile} />
                </div>
                <button type="submit" disabled={isAnalyzing || (!scriptFile && !scriptContent)}>Generate Coverage Report</button>
              </form>
            ) : (
              <HistoryPanel items={history} onSelect={(id) => void fetchReport(id)} />
            )}
          </>
        )}

        {report && <ReportViewer report={report} onBack={() => { setReport(null); void loadHistory() }} onExportPDF={handleExportPDF} onExportGoogleDoc={handleExportGoogleDoc} onFlagExample={handleFlagExample} exporting={exporting} flagging={flagging} />}
        {error && <div className="error">{error}</div>}
      </main>
      <footer><p>CoverageIQ Upgrade Sprint • GPT-4.1 + history + knowledge base</p></footer>
    </div>
  )
}

export default App
