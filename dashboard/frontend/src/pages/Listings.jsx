import { useState, useEffect } from 'react'
import { api } from '../utils/api'
import CarCard from '../components/CarCard'

export default function Listings() {
  const [cars, setCars] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    brand: '', min_price: '', max_price: '', min_year: '',
    city: '', fuel_type: '', transmission: '', min_score: '',
    max_kms: '', max_owners: '',
  })
  const [page, setPage] = useState(0)
  const limit = 24

  function fetchCars() {
    setLoading(true)
    const params = { ...filters, limit, offset: page * limit }
    Object.keys(params).forEach(k => { if (!params[k]) delete params[k] })
    api.getCars(params)
      .then(data => {
        setCars(data.cars)
        setTotal(data.total)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchCars() }, [page])

  function handleSearch(e) {
    e?.preventDefault()
    setPage(0)
    fetchCars()
  }

  function handleReset() {
    setFilters({
      brand: '', min_price: '', max_price: '', min_year: '',
      city: '', fuel_type: '', transmission: '', min_score: '',
      max_kms: '', max_owners: '',
    })
    setPage(0)
  }

  const totalPages = Math.ceil(total / limit)

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Listings</h1>

      <form onSubmit={handleSearch} className="bg-gray-900 rounded-xl border border-gray-800 p-4 mb-6">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <input name="brand" placeholder="Brand" value={filters.brand} onChange={e => setFilters(f => ({...f, brand: e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500" />
          <input name="min_price" type="number" placeholder="Min Price" value={filters.min_price} onChange={e => setFilters(f => ({...f, min_price: e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500" />
          <input name="max_price" type="number" placeholder="Max Price" value={filters.max_price} onChange={e => setFilters(f => ({...f, max_price: e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500" />
          <input name="min_year" type="number" placeholder="Min Year" value={filters.min_year} onChange={e => setFilters(f => ({...f, min_year: e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500" />
          <input name="city" placeholder="City" value={filters.city} onChange={e => setFilters(f => ({...f, city: e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500" />
          <select name="fuel_type" value={filters.fuel_type} onChange={e => setFilters(f => ({...f, fuel_type: e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white">
            <option value="">Fuel</option>
            <option value="Petrol">Petrol</option>
            <option value="Diesel">Diesel</option>
            <option value="Electric">Electric</option>
          </select>
          <select name="transmission" value={filters.transmission} onChange={e => setFilters(f => ({...f, transmission: e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white">
            <option value="">Transmission</option>
            <option value="Automatic">Automatic</option>
            <option value="Manual">Manual</option>
          </select>
          <input name="min_score" type="number" placeholder="Min Score" value={filters.min_score} onChange={e => setFilters(f => ({...f, min_score: e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500" />
          <input name="max_kms" type="number" placeholder="Max KMs" value={filters.max_kms} onChange={e => setFilters(f => ({...f, max_kms: e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500" />
          <input name="max_owners" type="number" placeholder="Max Owners" value={filters.max_owners} onChange={e => setFilters(f => ({...f, max_owners: e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500" />
        </div>
        <div className="flex gap-2 mt-3">
          <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition">Search</button>
          <button type="button" onClick={handleReset} className="bg-gray-800 hover:bg-gray-700 text-gray-300 px-4 py-2 rounded-lg text-sm transition">Reset</button>
          <span className="text-sm text-gray-500 self-center ml-auto">{total} results</span>
        </div>
      </form>

      {loading ? (
        <div className="text-center text-gray-500 py-20">Loading...</div>
      ) : cars.length === 0 ? (
        <p className="text-gray-500 text-center py-20">No listings found.</p>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {cars.map(car => <CarCard key={car.id} car={car} />)}
          </div>
          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-8">
              <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
                className="bg-gray-800 hover:bg-gray-700 disabled:opacity-50 px-4 py-2 rounded-lg text-sm transition">Previous</button>
              <span className="self-center text-sm text-gray-400">Page {page + 1} of {totalPages}</span>
              <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}
                className="bg-gray-800 hover:bg-gray-700 disabled:opacity-50 px-4 py-2 rounded-lg text-sm transition">Next</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
