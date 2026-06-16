import { useState } from "react"

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
        <div className="grid grid-cols-2 gap-6 max-w-3xl mx-auto">
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
        </div>

        {/* Active Panel */}
        <div className="max-w-5xl mx-auto mt-10">
          {activeCard === "researcher" && <Researcher />}
          {activeCard === "podcast" && <Podcast />}
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
  const [answer, setAnswer] = useState("")
  const [loading, setLoading] = useState(false)
  const [listening, setListening] = useState(false)

  const ask = async (q) => {
    const query = q || question
    if (!query.trim()) return
    setLoading(true)
    setAnswer("")

    const res = await fetch("https://stockflow-api-een5pcjcrq-nw.a.run.app/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: query })
    })

    const data = await res.json()
    setAnswer(data.answer)
    setLoading(false)

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

      {answer && (
        <div className="mt-6 p-4 bg-gray-800 rounded-lg text-gray-200 leading-relaxed">
          {answer}
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

  const getVoices = () => {
    return new Promise(resolve => {
      let voices = window.speechSynthesis.getVoices()
      if (voices.length) {
        resolve(voices)
      } else {
        window.speechSynthesis.onvoiceschanged = () => {
          voices = window.speechSynthesis.getVoices()
          resolve(voices)
        }
      }
    })
  }

  const speak = (text, voice) => {
    return new Promise(resolve => {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.voice = voice
      utterance.rate = 1.0
      utterance.onend = resolve
      window.speechSynthesis.speak(utterance)
    })
  }

  const togglePause = () => {
    if (paused) {
      window.speechSynthesis.resume()
      setPaused(false)
    } else {
      window.speechSynthesis.pause()
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
  const voices = await getVoices()
  const female = voices.find(v => v.name.includes("Female") || v.name.includes("Samantha") || v.name.includes("Zira")) || voices[0]
  const male = voices.find(v => v.name.includes("Male") || v.name.includes("David") || v.name.includes("Mark")) || voices[1]

  for (const turn of data.conversation) {
    setTranscript(prev => [...prev, turn])
    const voice = turn.speaker === "Host" ? female : male
    await speak(turn.text, voice)
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