import { useState } from 'react'
import { api } from '../utils/api'
import CarCard from '../components/CarCard'

export default function Chat() {
  const [message, setMessage] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!message.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await api.chat(message)
      setResult(data)
    } catch (err) {
      setError('Chat requires Gemini API key to be configured.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">🤖 AI Chat</h1>
      <p className="text-gray-400 mb-4">Ask in natural language to find cars. Example: "Find me an automatic Honda City under 9 lakh in Bangalore"</p>

      <form onSubmit={handleSubmit} className="mb-6">
        <div className="flex gap-2">
          <input
            value={message}
            onChange={e => setMessage(e.target.value)}
            placeholder='e.g. "White car with good resale under ₹10L"'
            className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500"
          />
          <button type="submit" disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-3 rounded-lg font-medium transition">
            {loading ? '...' : 'Search'}
          </button>
        </div>
      </form>

      {error && <p className="text-red-400 mb-4">{error}</p>}

      {result && (
        <div>
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 mb-6">
            <p className="text-sm text-gray-400 mb-2">AI understood:</p>
            <p className="text-white">{result.explanation}</p>
            {result.filters && (
              <pre className="mt-2 text-xs text-gray-500 bg-gray-950 p-2 rounded">
                {JSON.stringify(result.filters, null, 2)}
              </pre>
            )}
          </div>

          {result.cars?.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {result.cars.map(car => <CarCard key={car.id} car={car} />)}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-10">No cars match your query.</p>
          )}
        </div>
      )}
    </div>
  )
}
