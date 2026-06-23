import React, { useMemo, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

function normalizeRows(rows) {
  return Array.isArray(rows) ? rows : []
}

function App() {
  const [file, setFile] = useState(null)
  const [upload, setUpload] = useState(null)
  const [patternDescription, setPatternDescription] = useState('Find email addresses')
  const [replacementValue, setReplacementValue] = useState('REDACTED')
  const [transformMode, setTransformMode] = useState('replace')
  const [selectedColumns, setSelectedColumns] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const previewRows = useMemo(() => normalizeRows(upload?.preview_rows), [upload])
  const processedRows = useMemo(() => normalizeRows(result?.upload?.processed_rows), [result])
  const columns = upload?.column_names || []

  async function handleUpload(event) {
    event.preventDefault()
    if (!file) {
      setError('Choose a CSV or Excel file first.')
      return
    }
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const response = await fetch(`${API_BASE}/api/upload/`, {
        method: 'POST',
        body: form,
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.error || 'Upload failed.')
      setUpload(data.upload)
      setSelectedColumns(data.upload.target_columns || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleProcess(event) {
    event.preventDefault()
    if (!upload?.id) {
      setError('Upload a file before processing it.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const response = await fetch(`${API_BASE}/api/process/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          upload_id: upload.id,
          pattern_description: patternDescription,
          replacement_value: replacementValue,
          target_columns: selectedColumns,
          transform_mode: transformMode,
        }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.error || 'Processing failed.')
      setResult(data)
      setUpload(data.upload)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function toggleColumn(column) {
    setSelectedColumns((current) =>
      current.includes(column)
        ? current.filter((item) => item !== column)
        : [...current, column],
    )
  }

  return (
    <main className="shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Django + React</p>
          <h1>Regex pattern matching and replacement for CSV and Excel files</h1>
          <p className="subcopy">
            Upload a file, describe the pattern in plain English, and let the backend turn it into a regex before applying the replacement.
          </p>
        </div>
      </section>

      <section className="workspace">
        <form className="panel" onSubmit={handleUpload}>
          <h2>Upload</h2>
          <label className="field">
            <span>CSV or Excel file</span>
            <input type="file" accept=".csv,.xlsx,.xls" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </label>
          <button type="submit" disabled={loading}>Upload file</button>
        </form>

        <form className="panel" onSubmit={handleProcess}>
          <h2>Pattern and replacement</h2>
          <label className="field">
            <span>Natural language pattern</span>
            <textarea value={patternDescription} onChange={(e) => setPatternDescription(e.target.value)} rows={3} />
          </label>
          <label className="field">
            <span>Replacement value</span>
            <input value={replacementValue} onChange={(e) => setReplacementValue(e.target.value)} />
          </label>
          <label className="field">
            <span>Transformation mode</span>
            <select value={transformMode} onChange={(e) => setTransformMode(e.target.value)}>
              <option value="replace">Replace</option>
              <option value="mask">Mask</option>
            </select>
          </label>
          <div className="columns">
            <div className="columns-head">
              <span>Target columns</span>
              <button type="button" className="link" onClick={() => setSelectedColumns(columns)}>Select all</button>
            </div>
            <div className="chip-grid">
              {columns.length === 0 && <span className="muted">Upload a file to pick columns.</span>}
              {columns.map((column) => (
                <label key={column} className="chip">
                  <input
                    type="checkbox"
                    checked={selectedColumns.includes(column)}
                    onChange={() => toggleColumn(column)}
                  />
                  <span>{column}</span>
                </label>
              ))}
            </div>
          </div>
          <button type="submit" disabled={loading || !upload}>Process file</button>
        </form>
      </section>

      {error && <div className="alert">{error}</div>}
      {upload && (
        <section className="panel">
          <div className="summary">
            <div>
              <h2>Preview</h2>
              <p className="muted">{upload.original_name} · {upload.row_count} rows</p>
            </div>
            {upload.download_url && (
              <a href={`${API_BASE}${upload.download_url}`} className="download" target="_blank" rel="noreferrer">
                Download processed file
              </a>
            )}
          </div>
          <DataTable rows={result?.upload?.processed_rows?.length ? processedRows : previewRows} columns={columns} />
        </section>
      )}

      {result && (
        <section className="panel">
          <h2>Regex result</h2>
          <dl className="metrics">
            <div><dt>Regex</dt><dd>{result.regex}</dd></div>
            <div><dt>Flags</dt><dd>{result.flags}</dd></div>
            <div><dt>Confidence</dt><dd>{Number(result.confidence).toFixed(2)}</dd></div>
            <div><dt>Explanation</dt><dd>{result.explanation || 'No explanation returned.'}</dd></div>
          </dl>
        </section>
      )}
    </main>
  )
}

function DataTable({ rows, columns }) {
  const visibleColumns = columns.length > 0 ? columns : rows[0] ? Object.keys(rows[0]) : []
  if (!rows.length) return <p className="muted">No data to display yet.</p>
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {visibleColumns.map((column) => <th key={column}>{column}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {visibleColumns.map((column) => (
                <td key={column}>{row?.[column] ?? ''}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default App

