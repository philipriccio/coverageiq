import { useState, useEffect, useRef, useCallback } from 'react'
import axios from 'axios'
import './App.css'
import { ProgressBar } from './components/ProgressBar'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Types
interface EvidenceQuote {
  quote: string
  page: number
  context?: string
}

interface Subscore {
  score: number
  rationale?: string
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
  
  // Scores
  subscores?: Record<string, Subscore | number>
  total_score?: number
  recommendation?: 'Pass' | 'Consider' | 'Recommend'
  
  // Content
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
}

interface JobStatus {
  job_id: string
  report_id: string | null
  status: 'queued' | 'processing' | 'completed' | 'failed'
  progress: number
  error_message?: string
  created_at: string
  updated_at: string
  completed_at?: string
}

// Collapsible Section Component
function CollapsibleSection({ 
  title, 
  children, 
  defaultOpen = false 
}: { 
  title: string
  children: React.ReactNode
  defaultOpen?: boolean 
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  
  return (
    <div className="collapsible-section">
      <button 
        className="section-header"
        onClick={() => setIsOpen(!isOpen)}
        type="button"
      >
        <span className="section-title">{title}</span>
        <span className={`section-toggle ${isOpen ? 'open' : ''}`}>
          {isOpen ? '−' : '+'}
        </span>
      </button>
      {isOpen && (
        <div className="section-content">
          {children}
        </div>
      )}
    </div>
  )
}

// Score Badge Component
function ScoreBadge({ recommendation, totalScore }: { recommendation: string, totalScore: number }) {
  const getBadgeClass = () => {
    if (recommendation === 'Recommend') return 'badge-recommend'
    if (recommendation === 'Consider') return 'badge-consider'
    return 'badge-pass'
  }
  
  const getBorderColor = () => {
    if (recommendation === 'Recommend') return '#4caf50'
    if (recommendation === 'Consider') return '#ff9800'
    return '#e53935'
  }
  
  return (
    <div className="score-badge" style={{ borderColor: getBorderColor() }}>
      <div className="score-total">
        <span className="score-number">{totalScore}</span>
        <span className="score-max">/50</span>
      </div>
      <div className={`recommendation ${getBadgeClass()}`}>
        {recommendation}
      </div>
    </div>
  )
}

// Subscore Bar Component
function SubscoreBar({ label, score }: { label: string, score: number }) {
  const percentage = (score / 10) * 100
  
  return (
    <div className="subscore-item">
      <div className="subscore-label">{label.charAt(0).toUpperCase() + label.slice(1)}</div>
      <div className="subscore-bar-container">
        <div 
          className="subscore-bar" 
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="subscore-value">{score}/10</div>
    </div>
  )
}

// Evidence Quote Component
function EvidenceQuoteDisplay({ quote, page, context }: EvidenceQuote) {
  return (
    <div className="evidence-quote">
      <div className="quote-header">
        <span className="quote-page">Page {page}</span>
      </div>
      <blockquote className="quote-text">"{quote}"</blockquote>
      {context && <p className="quote-context">{context}</p>}
    </div>
  )
}

// Report Viewer Component
function ReportViewer({ 
  report, 
  onExportPDF, 
  onExportGoogleDoc,
  exporting 
}: { 
  report: CoverageReport
  onExportPDF: () => void
  onExportGoogleDoc: () => void
  exporting: { pdf: boolean, googleDoc: boolean }
}) {
  const subscores = report.subscores || {}
  
  // Convert subscores to array for rendering
  const subscoreEntries = Object.entries(subscores).map(([key, value]) => ({
    key,
    score: typeof value === 'number' ? value : value.score
  }))
  
  return (
    <div className="report-viewer">
      <div className="report-header">
        <h2>{report.script_title || 'Untitled Script'}</h2>
        <ScoreBadge 
          recommendation={report.recommendation || 'N/A'} 
          totalScore={report.total_score || 0}
        />
      </div>
      
      {/* Subscores */}
      <CollapsibleSection title="Score Breakdown" defaultOpen={true}>
        <div className="subscores-container">
          {subscoreEntries.map(({ key, score }) => (
            <SubscoreBar key={key} label={key} score={score} />
          ))}
        </div>
      </CollapsibleSection>
      
      {/* Logline */}
      {report.logline && (
        <CollapsibleSection title="Logline" defaultOpen={true}>
          <p className="logline">{report.logline}</p>
        </CollapsibleSection>
      )}
      
      {/* Synopsis */}
      {report.synopsis && (
        <CollapsibleSection title="Synopsis">
          <p className="synopsis">{report.synopsis}</p>
        </CollapsibleSection>
      )}
      
      {/* Overall Comments */}
      {report.overall_comments && (
        <CollapsibleSection title="Overall Comments">
          <p className="comments">{report.overall_comments}</p>
        </CollapsibleSection>
      )}
      
      {/* Strengths */}
      {report.strengths && report.strengths.length > 0 && (
        <CollapsibleSection title="Strengths" defaultOpen={true}>
          <ul className="strengths-list">
            {report.strengths.map((strength, i) => (
              <li key={i} className="strength-item">{strength}</li>
            ))}
          </ul>
        </CollapsibleSection>
      )}
      
      {/* Weaknesses */}
      {report.weaknesses && report.weaknesses.length > 0 && (
        <CollapsibleSection title="Weaknesses">
          <ul className="weaknesses-list">
            {report.weaknesses.map((weakness, i) => (
              <li key={i} className="weakness-item">{weakness}</li>
            ))}
          </ul>
        </CollapsibleSection>
      )}
      
      {/* Character Notes */}
      {report.character_notes && (
        <CollapsibleSection title="Character Notes">
          <pre className="json-content">{report.character_notes}</pre>
        </CollapsibleSection>
      )}
      
      {/* Structure Analysis */}
      {report.structure_analysis && (
        <CollapsibleSection title="Structure Analysis">
          <pre className="json-content">{report.structure_analysis}</pre>
        </CollapsibleSection>
      )}
      
      {/* Market Positioning */}
      {report.market_positioning && (
        <CollapsibleSection title="Market Positioning">
          <pre className="json-content">{report.market_positioning}</pre>
        </CollapsibleSection>
      )}
      
      {/* Evidence Quotes */}
      {report.evidence_quotes && report.evidence_quotes.length > 0 && (
        <CollapsibleSection title="Evidence Quotes" defaultOpen={true}>
          <div className="evidence-quotes-container">
            {report.evidence_quotes.map((quote, i) => (
              <EvidenceQuoteDisplay key={i} {...quote} />
            ))}
          </div>
        </CollapsibleSection>
      )}
      
      {/* Export Buttons */}
      <div className="export-section">
        <h3>Export Report</h3>
        <div className="export-buttons">
          <button 
            onClick={onExportGoogleDoc}
            disabled={exporting.googleDoc}
            className="export-btn google-doc-btn"
            type="button"
          >
            {exporting.googleDoc ? 'Creating Google Doc...' : '📄 Export to Google Doc'}
          </button>
          <button 
            onClick={onExportPDF}
            disabled={exporting.pdf}
            className="export-btn pdf-btn"
            type="button"
          >
            {exporting.pdf ? 'Generating PDF...' : '📑 Download PDF'}
          </button>
        </div>
      </div>
      
      <div className="report-footer">
        <p>Generated by {report.model_used} • {new Date(report.created_at).toLocaleString()}</p>
      </div>
    </div>
  )
}

// Main App Component
function App() {
  const [scriptContent, setScriptContent] = useState('')
  const [scriptFile, setScriptFile] = useState<File | null>(null)
  const [scriptTitle, setScriptTitle] = useState('')
  const [genre, setGenre] = useState('drama')
  const [comps, setComps] = useState('')
  const [analysisDepth, setAnalysisDepth] = useState('standard')
  
  // Async job state
  const [, setJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  
  const [report, setReport] = useState<CoverageReport | null>(null)
  const [error, setError] = useState('')
  const [exporting, setExporting] = useState({ pdf: false, googleDoc: false })
  
  // Polling ref
  const pollingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  // Poll job status
  const startPolling = useCallback((jobId: string, reportId: string) => {
    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
    }

    // Create new abort controller for this job
    abortControllerRef.current = new AbortController()

    // Poll immediately, then every 2 seconds
    const pollStatus = async () => {
      try {
        const response = await axios.get(
          `${API_BASE}/api/coverage/jobs/${jobId}/status`,
          { signal: abortControllerRef.current?.signal }
        )
        
        const status: JobStatus = response.data
        setJobStatus(status)

        if (status.status === 'completed') {
          // Stop polling and fetch the report
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current)
            pollingIntervalRef.current = null
          }
          await fetchReport(reportId)
        } else if (status.status === 'failed') {
          // Stop polling and show error
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current)
            pollingIntervalRef.current = null
          }
          setIsAnalyzing(false)
          setError(status.error_message || 'Analysis failed')
          setJobId(null)
        }
        // Otherwise continue polling (queued or processing)
      } catch (err: any) {
        if (err.name === 'CanceledError' || err.name === 'AbortError') {
          // Polling was cancelled, ignore
          return
        }
        console.error('Polling error:', err)
        // Don't stop polling on transient errors
      }
    }

    // Initial poll
    pollStatus()

    // Start interval
    pollingIntervalRef.current = setInterval(pollStatus, 2000)
  }, [])

  // Fetch completed report
  const fetchReport = async (reportId: string) => {
    try {
      const response = await axios.get(`${API_BASE}/api/coverage/${reportId}`)
      setReport(response.data)
      setIsAnalyzing(false)
      setJobId(null)
      setJobStatus(null)
    } catch (err: any) {
      setIsAnalyzing(false)
      setError(err.response?.data?.detail || 'Failed to fetch report')
      setJobId(null)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Reset state
    setIsAnalyzing(true)
    setError('')
    setReport(null)
    setJobId(null)
    setJobStatus(null)
    
    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
    
    try {
      let scriptId: string
      let scriptText: string
      
      if (scriptFile) {
        // File upload path
        const formData = new FormData()
        formData.append('file', scriptFile)
        formData.append('title', scriptTitle || scriptFile.name.replace(/\.[^/.]+$/, ''))
        formData.append('content_type', 'tv_pilot')
        
        const uploadRes = await axios.post(`${API_BASE}/api/scripts/upload-file`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        scriptId = uploadRes.data.script_id
        scriptText = uploadRes.data.extracted_text || ''
      } else {
        // Text paste path
        const uploadRes = await axios.post(`${API_BASE}/api/scripts/upload`, {
          title: scriptTitle || 'Untitled Script',
          content: scriptContent,
          content_type: 'tv_pilot'
        })
        
        scriptId = uploadRes.data.script_id
        scriptText = scriptContent
      }
      
      // Start async analysis
      const asyncRes = await axios.post(`${API_BASE}/api/coverage/generate-async`, {
        script_id: scriptId,
        script_text: scriptText,
        genre: genre,
        comps: comps ? comps.split(',').map(c => c.trim()) : [],
        analysis_depth: analysisDepth
      })
      
      const { job_id: newJobId, report_id } = asyncRes.data
      setJobId(newJobId)
      
      // Start polling for status
      startPolling(newJobId, report_id)
      
    } catch (err: any) {
      console.error('Error:', err)
      setIsAnalyzing(false)
      setError(err.response?.data?.detail || err.message || 'An error occurred')
    }
  }

  const handleCancel = () => {
    // Stop polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
    
    // Abort any in-flight requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    setIsAnalyzing(false)
    setJobId(null)
    setJobStatus(null)
    setError('Analysis cancelled')
  }

  const handleExportPDF = async () => {
    if (!report) return
    
    setExporting(prev => ({ ...prev, pdf: true }))
    
    try {
      const response = await axios.post(
        `${API_BASE}/api/coverage/${report.report_id}/export/pdf`,
        {},
        { responseType: 'blob' }
      )
      
      // Download the PDF
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      
      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers['content-disposition']
      const filenameMatch = contentDisposition?.match(/filename="?(.+)"?/)
      link.download = filenameMatch?.[1] || `coverage_report_${report.report_id}.pdf`
      
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      console.error('Export error:', err)
      setError('Failed to export PDF: ' + (err.response?.data?.detail || err.message))
    } finally {
      setExporting(prev => ({ ...prev, pdf: false }))
    }
  }

  const handleExportGoogleDoc = async () => {
    if (!report) return
    
    setExporting(prev => ({ ...prev, googleDoc: true }))
    setError('')
    
    try {
      const response = await axios.post(
        `${API_BASE}/api/coverage/${report.report_id}/export/google-doc`,
        { email: 'philipriccio@gmail.com' }
      )
      
      if (response.data.url) {
        window.open(response.data.url, '_blank')
      }
    } catch (err: any) {
      console.error('Export error:', err)
      const errorMsg = err.response?.data?.detail || err.message
      if (errorMsg.includes('credentials') || errorMsg.includes('browser')) {
        setError(
          'Google Docs export requires OAuth setup. Please run: python setup_google_auth.py'
        )
      } else {
        setError('Failed to export to Google Doc: ' + errorMsg)
      }
    } finally {
      setExporting(prev => ({ ...prev, googleDoc: false }))
    }
  }

  return (
    <div className="container">
      <header>
        <h1>
          <span className="logo-icon">🎬</span>
          CoverageIQ
        </h1>
        <p>AI-powered script coverage for TV pilots & features</p>
      </header>

      <main>
        {/* Analysis Progress Overlay */}
        {isAnalyzing && (
          <div className="analyzing-overlay">
            <div className="analyzing-content">
              <ProgressBar
                progress={jobStatus?.progress || 0}
                status={jobStatus?.status || 'queued'}
                message={jobStatus?.status === 'queued' ? 'Starting analysis...' : undefined}
                onCancel={handleCancel}
              />
            </div>
          </div>
        )}

        {!report ? (
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="title">Script Title</label>
                <input
                  id="title"
                  type="text"
                  value={scriptTitle}
                  onChange={(e) => setScriptTitle(e.target.value)}
                  placeholder="e.g., The Last Frontier"
                  disabled={isAnalyzing}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="genre">Genre</label>
                <select
                  id="genre"
                  value={genre}
                  onChange={(e) => setGenre(e.target.value)}
                  disabled={isAnalyzing}
                >
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
                <label htmlFor="comps">Comparable Series (comma-separated)</label>
                <input
                  id="comps"
                  type="text"
                  value={comps}
                  onChange={(e) => setComps(e.target.value)}
                  placeholder="e.g., Northern Exposure, ER"
                  disabled={isAnalyzing}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="depth">Analysis Depth</label>
                <select
                  id="depth"
                  value={analysisDepth}
                  onChange={(e) => setAnalysisDepth(e.target.value)}
                  disabled={isAnalyzing}
                >
                  <option value="quick">Quick (~2 min)</option>
                  <option value="standard">Standard (~5 min)</option>
                  <option value="deep">Deep (~10 min)</option>
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
                    setScriptContent('') // Clear text if file is selected
                  }
                }}
                disabled={isAnalyzing}
              />
              {scriptFile && (
                <p className="file-selected">
                  Selected: {scriptFile.name} ({(scriptFile.size / 1024).toFixed(1)} KB)
                </p>
              )}
            </div>

            <div className="form-group full-width">
              <label htmlFor="script">Or Paste Script Text</label>
              <textarea
                id="script"
                rows={20}
                value={scriptContent}
                onChange={(e) => {
                  setScriptContent(e.target.value)
                  setScriptFile(null) // Clear file if text is pasted
                }}
                placeholder="Paste your TV pilot script here...&#10;&#10;Or use the file upload above."
                disabled={!!scriptFile || isAnalyzing}
              />
            </div>

            <button type="submit" disabled={isAnalyzing || (!scriptFile && !scriptContent)}>
              {isAnalyzing ? 'Analyzing Script...' : 'Generate Coverage Report'}
            </button>
          </form>
        ) : (
          <div className="report-container">
            <button 
              className="back-btn"
              onClick={() => setReport(null)}
              type="button"
            >
              ← Analyze Another Script
            </button>
            <ReportViewer 
              report={report}
              onExportPDF={handleExportPDF}
              onExportGoogleDoc={handleExportGoogleDoc}
              exporting={exporting}
            />
          </div>
        )}

        {error && <div className="error">{error}</div>}
      </main>

      <footer>
        <p>CoverageIQ MVP • Day 4 Build • AI-Powered Script Coverage</p>
      </footer>
    </div>
  )
}

export default App
