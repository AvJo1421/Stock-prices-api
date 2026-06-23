import { useState, useRef } from "react"

export default function App() {
  const [activeCard, setActiveCard] = useState(null)

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-8 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">StockFlow</h1>
          <p className="text-gray-400 text-sm">Stream. Analyse. Decide.</p>
        </div>
      </header>

      {/* Main */}
      <main className="px-8 py-12">
        {/* Cards */}
        <div className="grid grid-cols-4 gap-6 max-w-5xl mx-auto">
          <Card
            title="Stock Researcher"
            description="Ask anything about your watchlist using AI"
            icon="🔍"
            onClick={() => setActiveCard("researcher")}
            active={activeCard === "researcher"}
          />
          <Card
            title="AI Podcast"
            description="Stream. Listen. Discuss."
            icon="🎙️"
            onClick={() => setActiveCard("podcast")}
            active={activeCard === "podcast"}
          />
          <Card
            title="Watchlist"
            description="Live prices across your portfolio"
            icon="📊"
            onClick={() => setActiveCard("watchlist")}
            active={activeCard === "watchlist"}
          />
          <Card
            title="News Feed"
            description="Latest stock related news"
            icon="📰"
            onClick={() => setActiveCard("news")}
            active={activeCard === "news"}
          />
        </div>

        {/* Active Panel */}
        <div className="max-w-7xl mx-auto mt-10">
          {activeCard === "researcher" && <Researcher />}
          {activeCard === "podcast" && <Podcast />}
          {activeCard === "watchlist" && <Watchlist />}
          {activeCard === "news" && <NewsFeed />}
        </div>
      </main>
    </div>
  )
}

function Card({ title, description, icon, onClick, active }) {
  return (
    <div
      onClick={onClick}
      className={`cursor-pointer rounded-xl p-6 border transition-all ${
        active
          ? "border-blue-500 bg-blue-950"
          : "border-gray-800 bg-gray-900 hover:border-gray-600"
      }`}
    >
      <div className="text-3xl mb-3">{icon}</div>
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="text-gray-400 text-sm mt-1">{description}</p>
    </div>
  )
}

function Researcher() {
  const [question, setQuestion] = useState("")
  const [loading, setLoading] = useState(false)
  const [listening, setListening] = useState(false)
  const [chatHistory, setChatHistory] = useState([])

  const ask = async (q) => {
    const query = q || question
    if (!query.trim()) return
    setLoading(true)
    setQuestion("")

    const res = await fetch("https://stockflow-api-een5pcjcrq-nw.a.run.app/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: query, chat_history: chatHistory })
    })

    const data = await res.json()
    setLoading(false)

    setChatHistory(prev => [
      ...prev,
      { role: "user", content: query },
      { role: "assistant", content: data.answer }
    ])

    const utterance = new SpeechSynthesisUtterance(data.answer)
    window.speechSynthesis.speak(utterance)
  }

  const startListening = () => {
    const recognition = new window.webkitSpeechRecognition()
    recognition.lang = "en-US"
    recognition.interimResults = false

    recognition.onstart = () => setListening(true)
    recognition.onend = () => setListening(false)

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      setQuestion(transcript)
      ask(transcript)
    }

    recognition.start()
  }

  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
      <h2 className="text-xl font-semibold mb-4">Stock Researcher</h2>
      <div className="flex gap-3">
        <input
          type="text"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={e => e.key === "Enter" && ask()}
          placeholder="Ask anything about your stocks..."
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
        />
        <button
          onClick={startListening}
          disabled={listening || loading}
          className={`px-4 py-2 rounded-lg font-medium ${
            listening ? "bg-red-600" : "bg-gray-700 hover:bg-gray-600"
          } disabled:opacity-50`}
        >
          {listening ? "🔴" : "🎤"}
        </button>
        <button
          onClick={() => ask()}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 px-5 py-2 rounded-lg font-medium disabled:opacity-50"
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </div>

      {chatHistory.length > 0 && (
        <div className="space-y-3 mt-6">
          {chatHistory.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-2xl px-4 py-2 rounded-lg text-sm ${
                msg.role === "user" ? "bg-blue-900 text-blue-100" : "bg-gray-800 text-gray-200"
              }`}>
                {msg.content}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function Podcast() {
  const [topic, setTopic] = useState("")
  const [duration, setDuration] = useState(5)
  const [running, setRunning] = useState(false)
  const [transcript, setTranscript] = useState([])
  const [paused, setPaused] = useState(false)
  const audioRef = useRef(null)

  const playAudio = (base64Audio) => {
    return new Promise(resolve => {
      if (!base64Audio) {
        resolve()
        return
      }
      const audio = new Audio(`data:audio/mpeg;base64,${base64Audio}`)
      audioRef.current = audio
      audio.onended = resolve
      audio.play()
    })
  }

  const togglePause = () => {
    if (!audioRef.current) return
    if (paused) {
      audioRef.current.play()
      setPaused(false)
    } else {
      audioRef.current.pause()
      setPaused(true)
    }
  }

  const start = async () => {
    if (!topic.trim()) return
    setRunning(true)
    setTranscript([])
    setPaused(false)

    const res = await fetch("https://stockflow-api-een5pcjcrq-nw.a.run.app/podcast", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, duration_minutes: duration })
    })

    const data = await res.json()

    for (const turn of data.conversation) {
      setTranscript(prev => [...prev, turn])
      await playAudio(turn.audio)
    }

    setRunning(false)
  }

  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
      <h2 className="text-xl font-semibold mb-4">AI Podcast</h2>

      <div className="flex gap-3 mb-4">
        <input
          type="text"
          value={topic}
          onChange={e => setTopic(e.target.value)}
          placeholder="What do you want to listen to? e.g. Tech stocks this year"
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
        />
        <select
          value={duration}
          onChange={e => setDuration(Number(e.target.value))}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
        >
          <option value={2}>2 min</option>
          <option value={5}>5 min</option>
          <option value={10}>10 min</option>
        </select>
        <button
          onClick={start}
          disabled={running}
          className="bg-purple-600 hover:bg-purple-700 px-5 py-2 rounded-lg font-medium disabled:opacity-50"
        >
          {running ? "On Air 🔴" : "Start 🎙️"}
        </button>
        {running && (
          <button
            onClick={togglePause}
            className="bg-yellow-600 hover:bg-yellow-700 px-5 py-2 rounded-lg font-medium"
          >
            {paused ? "▶️ Resume" : "⏸️ Pause"}
          </button>
        )}
      </div>

      {transcript.length > 0 && (
        <div className="space-y-3 mt-4">
          {transcript.map((turn, i) => (
            <div key={i} className={`flex gap-3 ${turn.speaker === "Host" ? "justify-start" : "justify-end"}`}>
              <div className={`max-w-2xl px-4 py-2 rounded-lg text-sm ${
                turn.speaker === "Host" ? "bg-purple-900 text-purple-100" : "bg-blue-900 text-blue-100"
              }`}>
                <span className="font-semibold text-xs opacity-70">{turn.speaker}</span>
                <p className="mt-1">{turn.text}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function Watchlist() {
  const [data, setData] = useState([])
  const [lastUpdated, setLastUpdated] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchPrices = async () => {
    setLoading(true)
    const res = await fetch("https://stockflow-api-een5pcjcrq-nw.a.run.app/watchlist")
    const result = await res.json()
    setData(result.data)
    setLastUpdated(new Date(result.fetched_at))
    setLoading(false)
  }

  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-xl font-semibold">Watchlist</h2>
        <div className="flex items-center gap-4">
          {lastUpdated && (
            <span className="text-xs text-gray-500">
              Last updated: {lastUpdated.toLocaleTimeString("en-GB")} BST
            </span>
          )}
          <button
            onClick={fetchPrices}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
          >
            {loading ? "Refreshing..." : "🔄 Refresh"}
          </button>
        </div>
      </div>

      {data.length === 0 ? (
        <p className="text-gray-500 text-sm">Click refresh to load prices</p>
      ) : (
        <div className="grid grid-cols-8 gap-3">
          {data.map(stock => {
            const isUp = stock.change_pct > 0
            const isDown = stock.change_pct < 0
            return (
              <div
                key={stock.ticker}
                className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors border border-gray-700/50"
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <div className="font-bold text-sm text-white">{stock.ticker}</div>
                    <div className="text-xs text-gray-400 truncate max-w-[100px]">{stock.name}</div>
                  </div>
                  <span className="text-[9px] bg-gray-700 text-gray-300 px-2 py-0.5 rounded-full whitespace-nowrap">
                    {stock.sector}
                  </span>
                </div>
                <div className="flex items-baseline justify-between mt-3">
                  <span className="text-lg font-bold text-white">${stock.close.toFixed(2)}</span>
                  <span className={`text-xs font-semibold ${
                    isUp ? "text-green-400" : isDown ? "text-red-400" : "text-gray-500"
                  }`}>
                    {isUp ? "▲" : isDown ? "▼" : "—"} {Math.abs(stock.change_pct).toFixed(2)}%
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function NewsFeed() {
  const [news, setNews] = useState([])
  const [loading, setLoading] = useState(false)

  const fetchNews = async () => {
    setLoading(true)
    const res = await fetch("https://stockflow-api-een5pcjcrq-nw.a.run.app/news")
    const data = await res.json()
    setNews(data.news)
    setLoading(false)
  }

  const formatDate = (utc) => {
    const date = new Date(utc)
    return date.toLocaleDateString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })
  }

  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-xl font-semibold">Latest News</h2>
        <button
          onClick={fetchNews}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
        >
          {loading ? "Loading..." : "🔄 Refresh"}
        </button>
      </div>

      {news.length === 0 ? (
        <p className="text-gray-500 text-sm">No news available</p>
      ) : (
        <div className="space-y-3">
          {news.map((item, i) => (
            <div key={i} className="bg-gray-800 rounded-lg p-4 border border-gray-700/50 hover:bg-gray-750 transition-colors">
             <div className="flex items-start justify-between gap-3">
                <a
                  href={`https://www.google.com/search?q=${encodeURIComponent(item.title)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-200 flex-1 hover:text-blue-400 hover:underline"
                >
                  {item.title}
                </a>
                <span className="text-[10px] bg-blue-900 text-blue-300 px-2 py-0.5 rounded-full whitespace-nowrap">
                  {item.ticker}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-2">{formatDate(item.published_utc)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}