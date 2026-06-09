import React, { useState, useEffect } from 'react'
import PredictionCard from './PredictionCard'
import './App.css'

export default function App() {
  const [predictions, setPredictions] = useState({})
  const [connected, setConnected] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)

  useEffect(() => {
    let ws
    let retryTimeout

    function connect() {
      ws = new WebSocket('ws://localhost:8000/ws/predictions')

      ws.onopen = () => {
        setConnected(true)
        console.log('✅ Connected to WebSocket')
      }

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        setPredictions(prev => ({ ...prev, [data.ticker]: data }))
        setLastUpdate(new Date().toLocaleTimeString())
      }

      ws.onerror = () => setConnected(false)

      ws.onclose = () => {
        setConnected(false)
        console.log('❌ Disconnected — retrying in 5s...')
        retryTimeout = setTimeout(connect, 5000)
      }
    }

    connect()
    return () => {
      clearTimeout(retryTimeout)
      ws.close()
    }
  }, [])

  return (
    <div className="app">
      <header>
        <h1>📊 Stock Price Predictions</h1>
        <div className="status">
          <span className={`indicator ${connected ? 'connected' : 'disconnected'}`}></span>
          {connected ? 'Live' : 'Offline'}
          {lastUpdate && <span className="timestamp">Last update: {lastUpdate}</span>}
        </div>
      </header>

      <div className="predictions-grid">
        {Object.values(predictions).length === 0 ? (
          <div className="loading">Waiting for predictions...</div>
        ) : (
          Object.values(predictions).map(pred => (
            <PredictionCard key={pred.ticker} data={pred} />
          ))
        )}
      </div>
    </div>
  )
}
