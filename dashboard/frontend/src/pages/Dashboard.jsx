import { useState, useEffect } from 'react'
import { api } from '../utils/api'
import CarCard from '../components/CarCard'

function StatCard({ label, value, color }) {
  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
      <div className="text-sm text-gray-400 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${color}`}>{value ?? '—'}</div>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [deals, setDeals] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.getStats(), api.getDeals(85)])
      .then(([s, d]) => {
        setStats(s)
        setDeals(d)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="text-center text-gray-500 py-20">Loading...</div>
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
        <StatCard label="Total Listings" value={stats?.total_listings} color="text-white" />
        <StatCard label="Analyzed" value={stats?.analyzed} color="text-blue-400" />
        <StatCard label="Avg Score" value={stats?.avg_score != null ? `${stats.avg_score}/100` : null} color="text-green-400" />
        <StatCard label="Active Deals" value={stats?.active_deals} color="text-yellow-400" />
        <StatCard label="Favorites" value={stats?.favorites} color="text-purple-400" />
      </div>

      <h2 className="text-xl font-semibold mb-4">🔥 Top Deals</h2>
      {deals.length === 0 ? (
        <p className="text-gray-500">No great deals found yet. Scrapers run every 30 minutes.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {deals.slice(0, 8).map((car) => (
            <CarCard key={car.id} car={car} />
          ))}
        </div>
      )}
    </div>
  )
}
