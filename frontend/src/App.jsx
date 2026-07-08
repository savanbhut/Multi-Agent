import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { runResearch } from './api'

const LOADING_STAGES = [
  'Searching the web...',
  'Scraping source content...',
  'Writing the report...',
  'Critiquing and revising...',
]

function App() {
  const [topic, setTopic] = useState('')
  const [maxSources, setMaxSources] = useState(5)
  const [loading, setLoading] = useState(false)
  const [loadingStage, setLoadingStage] = useState(0)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (topic.trim().length < 3) {
      setError('Enter a topic with at least 3 characters.')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)
    setLoadingStage(0)

    const stageTimer = setInterval(() => {
      setLoadingStage((s) => Math.min(s + 1, LOADING_STAGES.length - 1))
    }, 6000)

    try {
      const data = await runResearch(topic, maxSources)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      clearInterval(stageTimer)
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <header className="header">
        <h1>Multi-Agent Research System</h1>
        <p className="subtitle">Search Agent → Reader Agent → Writer Chain → Critic Chain</p>
      </header>

      <form className="research-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g. impact of AI agents on software engineering jobs"
          disabled={loading}
        />

        <div className="form-row">
          <label>
            Sources: <strong>{maxSources}</strong>
            <input
              type="range"
              min={3}
              max={8}
              value={maxSources}
              onChange={(e) => setMaxSources(Number(e.target.value))}
              disabled={loading}
            />
          </label>

          <button type="submit" disabled={loading}>
            {loading ? 'Running...' : 'Run Research'}
          </button>
        </div>
      </form>

      {loading && (
        <div className="loading-panel">
          <div className="spinner" />
          <p>{LOADING_STAGES[loadingStage]}</p>
          <p className="loading-note">
            Takes 20-40s due to the LLM rate limit. Don't refresh.
          </p>
        </div>
      )}

      {error && (
        <div className="error-panel">
          <strong>Failed:</strong> {error}
        </div>
      )}

      {result && (
        <div className="results">
          <section className="score-panel">
            <div className="score-box">
              <span className="score-label">Final Score</span>
              <span className="score-value">{result.score}/10</span>
              {result.score_after_revision !== null && (
                <span className="score-delta">
                  {result.score_before_revision} → {result.score_after_revision}
                </span>
              )}
            </div>
            <div className="strengths-box">
              <span className="score-label">Strengths</span>
              <p>{result.strengths}</p>
            </div>
          </section>

         {(result.citation_gaps?.length > 0 || result.accuracy_concerns?.length > 0) && (
            <section className="issues-panel">
              {result.citation_gaps?.length > 0 && (
                <>
                  <h3>Citation Gaps (fixed by adding sources)</h3>
                  <ul>
                    {result.citation_gaps.map((issue, i) => (
                      <li key={i}>{issue}</li>
                    ))}
                  </ul>
                </>
              )}
              {result.accuracy_concerns?.length > 0 && (
                <>
                  <h3 className="accuracy-heading">Accuracy Concerns (verified against sources)</h3>
                  <ul>
                    {result.accuracy_concerns.map((issue, i) => (
                      <li key={i}>{issue}</li>
                    ))}
                  </ul>
                </>
              )}
            </section>
          )}

          <section className="report-panel">
            <h3>Report</h3>
            <div className="markdown-body">
              <ReactMarkdown>{result.report}</ReactMarkdown>
            </div>
          </section>

          <section className="sources-panel">
            <h3>Sources</h3>
            <ul>
              {result.sources.map((url) => (
                <li key={url}>
                  <a href={url} target="_blank" rel="noreferrer">{url}</a>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </div>
  )
}

export default App