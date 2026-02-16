import './ProgressBar.css'

interface ProgressBarProps {
  progress: number
  status: string
  message?: string
  onCancel?: () => void
}

export function ProgressBar({ progress, status, message, onCancel }: ProgressBarProps) {
  const getStatusMessage = () => {
    if (message) return message
    switch (status) {
      case 'queued':
        return 'Waiting in queue...'
      case 'processing':
        if (progress < 25) return 'Initializing analysis...'
        if (progress < 50) return 'Analyzing script with AI...'
        if (progress < 75) return 'Processing results...'
        return 'Finalizing report...'
      case 'completed':
        return 'Analysis complete!'
      case 'failed':
        return 'Analysis failed'
      default:
        return 'Processing...'
    }
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'queued':
        return '⏳'
      case 'processing':
        return '🤖'
      case 'completed':
        return '✅'
      case 'failed':
        return '❌'
      default:
        return '⏳'
    }
  }

  return (
    <div className="progress-container">
      <div className="progress-header">
        <span className="progress-icon">{getStatusIcon()}</span>
        <span className="progress-status">{getStatusMessage()}</span>
        <span className="progress-percentage">{progress}%</span>
      </div>
      
      <div className="progress-bar-wrapper">
        <div 
          className={`progress-bar-fill ${status}`}
          style={{ width: `${progress}%` }}
        />
      </div>
      
      {status === 'processing' && onCancel && (
        <button 
          className="cancel-btn"
          onClick={onCancel}
          type="button"
        >
          Cancel
        </button>
      )}
    </div>
  )
}
