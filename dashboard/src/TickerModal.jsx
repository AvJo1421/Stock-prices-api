import React, { useEffect, useState } from 'react'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend
} from 'recharts'

export default function TickerModal({ ticker, onClose }) {
  const [data, setData]       = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetch(`http://localhost:8000/history/${ticker}?bars=200`)
      .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
      .then(json => { setData(json.data); setLoading(false) })
      .catch(e  => { setError(String(e)); setLoading(false) })
  }, [ticker])

  // Close on backdrop click
  const handleBackdrop = (e) => {
    if (e.target === e.currentTarget) onClose()
  }

  const prices = data.map(d => d.actual)
  const minY   = prices.length ? Math.min(...prices) * 0.998 : 0
  const maxY   = prices.length ? Math.max(...prices) * 1.002 : 100

  return (
    <div className="modal-backdrop" onClick={handleBackdrop}>
      <div className="modal">
        <div className="modal-header">
          <h2>{ticker} — Price History &amp; Predictions</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {loading && <div className="modal-status">Loading chart data...</div>}
          {error   && <div className="modal-status error">Failed to load: {error}</div>}
          {!loading && !error && data.length > 0 && (
            <ResponsiveContainer width="100%" height={380}>
              <LineChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="time"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  interval={Math.floor(data.length / 8)}
                />
                <YAxis
                  domain={[minY, maxY]}
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  tickFormatter={v => `$${v.toFixed(2)}`}
                  width={70}
                />
                <Tooltip
                  contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }}
                  labelStyle={{ color: '#94a3b8' }}
                  formatter={(val, name) => [`$${val.toFixed(2)}`, name]}
                />
                <Legend wrapperStyle={{ color: '#94a3b8', paddingTop: 12 }} />
                <Line
                  type="monotone"
                  dataKey="actual"
                  name="Actual"
                  stroke="#e2e8f0"
                  dot={false}
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="predicted"
                  name="Predicted"
                  stroke="#60a5fa"
                  dot={false}
                  strokeWidth={2}
                  strokeDasharray="4 2"
                />
                <Line
                  type="monotone"
                  dataKey="trend"
                  name="Trend"
                  stroke="#f59e0b"
                  dot={false}
                  strokeWidth={1.5}
                  strokeDasharray="8 4"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}
