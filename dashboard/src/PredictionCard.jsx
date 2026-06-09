import React from 'react'

export default function PredictionCard({ data, onClick }) {
  const { ticker, current_price, predicted_price, change_pct } = data
  const isUp = change_pct >= 0

  return (
    <div className="card" onClick={onClick} style={{ cursor: 'pointer' }}>
      <div className="card-header">
        <h2>{ticker}</h2>
        <span className={`badge ${isUp ? 'up' : 'down'}`}>
          {isUp ? '📈' : '📉'} {change_pct > 0 ? '+' : ''}{change_pct}%
        </span>
      </div>

      <div className="prices">
        <div className="price-item">
          <label>Current</label>
          <span className="price">${current_price.toFixed(2)}</span>
        </div>

        <div className="arrow">{isUp ? '↑' : '↓'}</div>

        <div className="price-item">
          <label>Predicted</label>
          <span className="price predicted">${predicted_price.toFixed(2)}</span>
        </div>
      </div>

      <div className="confidence">
        <span className="confidence-label">Confidence</span>
        <div className="confidence-bar">
          <div
            className={`confidence-fill ${Math.abs(change_pct) > 2 ? 'high' : 'medium'}`}
            style={{ width: `${Math.min(50 + Math.abs(change_pct) * 10, 100)}%` }}
          ></div>
        </div>
      </div>
    </div>
  )
}
