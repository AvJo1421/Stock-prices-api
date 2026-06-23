import React, { useEffect, useState } from 'react'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ReferenceLine
} from 'recharts'

function Chart({ data, yKeys }) {
  const allValues = data.flatMap(d => yKeys.map(k => d[k]).filter(v => v != null))
  const minY = allValues.length ? Math.min(...allValues) * 0.997 : 0
  const maxY = allValues.length ? Math.max(...allValues) * 1.003 : 100

  return (
    <ResponsiveContainer width="100%" height={380}>
      <LineChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis
          dataKey="date"
          tick={{ fill: '#94a3b8', fontSize: 11 }}
          interval={Math.max(1, Math.floor(data.length / 8))}
        />
        <YAxis
          domain={[minY, maxY]}
          tick={{ fill: '#94a3b8', fontSize: 11 }}
          tickFormatter={v => `$${v.toFixed(2)}`}
          width={75}
        />
        <Tooltip
          contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }}
          labelStyle={{ color: '#94a3b8' }}
          formatter={(val, name) => val != null ? [`$${val.toFixed(2)}`, name] : ['-', name]}
        />
        <Legend wrapperStyle={{ color: '#94a3b8', paddingTop: 12 }} />

        {yKeys.includes('actual') && (
          <Line type="monotone" dataKey="actual" name="Actual"
            stroke="#e2e8f0" dot={false} strokeWidth={2} connectNulls={false} />
        )}
        {yKeys.includes('predicted') && (
          <Line type="monotone" dataKey="predicted" name="Model (past)"
            stroke="#60a5fa" dot={false} strokeWidth={2} strokeDasharray="4 2" connectNulls={false} />
        )}
        {yKeys.includes('trend') && (
          <Line type="monotone" dataKey="trend" name="Trend"
            stroke="#f59e0b" dot={false} strokeWidth={1.5} strokeDasharray="8 4" connectNulls={false} />
        )}
        {yKeys.includes('forecast') && (
          <Line type="monotone" dataKey="forecast" name="10-Day Forecast"
            stroke="#a78bfa" dot={{ r: 4, fill: '#a78bfa' }} strokeWidth={2.5}
            strokeDasharray="6 3" connectNulls={false} />
        )}
      </LineChart>
    </ResponsiveContainer>
  )
}

export default function TickerModal({ ticker, onClose }) {
  const [tab, setTab]             = useState('history')
  const [histData, setHistData]   = useState([])
  const [foreData, setForeData]   = useState([])
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)

  // Load history (intraday)
  useEffect(() => {
    setLoading(true); setError(null)
    fetch(`http://localhost:8000/history/${ticker}?bars=200`)
      .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
      .then(json => { setHistData(json.data); setLoading(false) })
      .catch(e  => { setError(String(e)); setLoading(false) })
  }, [ticker])

  // Load forecast when tab switches
  useEffect(() => {
    if (tab !== 'forecast' || foreData.length > 0) return
    setLoading(true); setError(null)
    fetch(`http://localhost:8000/forecast/${ticker}?days=10`)
      .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
      .then(json => {
        // Combine history + forecast into one series for a seamless chart
        const combined = [
          ...json.history.slice(-30).map(d => ({ date: d.date, actual: d.actual, predicted: d.predicted, forecast: null })),
          ...json.forecast.map(d => ({ date: d.date, actual: null, predicted: null, forecast: d.forecast }))
        ]
        setForeData(combined)
        setLoading(false)
      })
      .catch(e => { setError(String(e)); setLoading(false) })
  }, [tab, ticker])

  const handleBackdrop = (e) => { if (e.target === e.currentTarget) onClose() }

  return (
    <div className="modal-backdrop" onClick={handleBackdrop}>
      <div className="modal">
        <div className="modal-header">
          <h2>{ticker} — Price History &amp; Predictions</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="modal-tabs">
          <button className={`tab-btn ${tab === 'history' ? 'active' : ''}`} onClick={() => setTab('history')}>
            Today's Chart
          </button>
          <button className={`tab-btn ${tab === 'forecast' ? 'active' : ''}`} onClick={() => setTab('forecast')}>
            10-Day Forecast
          </button>
        </div>

        <div className="modal-body">
          {loading && <div className="modal-status">Loading...</div>}
          {error   && <div className="modal-status error">Failed to load: {error}</div>}

          {!loading && !error && tab === 'history' && histData.length > 0 && (
            <Chart data={histData} yKeys={['actual', 'predicted', 'trend']} />
          )}
          {!loading && !error && tab === 'forecast' && foreData.length > 0 && (
            <>
              <p className="forecast-note">Last 30 days actual + 10-day model forecast (purple)</p>
              <Chart data={foreData} yKeys={['actual', 'predicted', 'forecast']} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
