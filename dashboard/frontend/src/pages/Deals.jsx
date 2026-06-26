import { useState, useEffect } from 'react'
import { api } from '../utils/api'
import CarCard from '../components/CarCard'

export default function Deals() {
  const [deals, setDeals] = useState([])
  const [threshold, setThreshold] = useState(85)
  const [loading, setLoading] = useState(true)

  function fetchDeals() {
    setLoading(true)
    api.getDeals(threshold)
      .then(setDeals)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchDeals() }, [threshold])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">🔥 Deals</h1>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400">Min Score:</span>
          <select value={threshold} onChange={e => setThreshold(Number(e.target.value))}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-white">
            <option value={85}>85+</option>
            <option value={90}>90+</option>
            <option value={95}>95+</option>
            <option value={70}>70+</option>
            <option value={60}>60+</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="text-center text-gray-500 py-20">Loading...</div>
      ) : deals.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-gray-500 text-lg mb-2">No deals found</p>
          <p className="text-gray-600 text-sm">Listings with score &ge; {threshold} will appear here.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {deals.map(car => <CarCard key={car.id} car={car} />)}
        </div>
      )}
    </div>
  )
}
