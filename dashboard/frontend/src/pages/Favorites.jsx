import { useState, useEffect } from 'react'
import { api } from '../utils/api'
import CarCard from '../components/CarCard'

export default function Favorites() {
  const [cars, setCars] = useState([])
  const [loading, setLoading] = useState(true)

  function fetchFavorites() {
    setLoading(true)
    api.getFavorites()
      .then(setCars)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchFavorites() }, [])

  async function handleRemove(carId) {
    await api.removeFavorite(carId)
    fetchFavorites()
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">⭐ Favorites</h1>

      {loading ? (
        <div className="text-center text-gray-500 py-20">Loading...</div>
      ) : cars.length === 0 ? (
        <p className="text-gray-500 text-center py-20">No favorite cars yet. Browse listings and add favorites.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {cars.map(car => (
            <div key={car.id} className="relative">
              <CarCard car={car} />
              <button onClick={() => handleRemove(car.id)}
                className="absolute top-2 right-2 bg-red-600 hover:bg-red-700 text-white text-xs px-2 py-1 rounded transition">
                Remove
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
