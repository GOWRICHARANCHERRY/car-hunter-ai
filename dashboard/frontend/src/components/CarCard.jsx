export default function CarCard({ car }) {
  const scoreColor = car.score >= 85 ? 'text-green-400' : car.score >= 70 ? 'text-yellow-400' : 'text-red-400'

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden hover:border-gray-700 transition">
      <div className="h-40 bg-gray-800 flex items-center justify-center">
        {car.image_urls?.[0] ? (
          <img src={car.image_urls[0]} alt={car.title} className="w-full h-full object-cover" />
        ) : (
          <span className="text-gray-600 text-4xl">🚗</span>
        )}
      </div>
      <div className="p-4">
        <div className="flex justify-between items-start mb-2">
          <h3 className="font-semibold text-white truncate">{car.title || `${car.brand || ''} ${car.model || ''}`}</h3>
          {car.score != null && (
            <span className={`text-lg font-bold ${scoreColor}`}>{car.score}</span>
          )}
        </div>
        <div className="space-y-1 text-sm text-gray-400">
          <div className="flex justify-between">
            <span>{car.year} &middot; {car.kms?.toLocaleString()} km</span>
            <span className="text-white font-semibold">₹{car.price?.toLocaleString()}</span>
          </div>
          <div className="flex gap-2 flex-wrap">
            {car.fuel_type && <span className="bg-gray-800 px-2 py-0.5 rounded text-xs">{car.fuel_type}</span>}
            {car.transmission && <span className="bg-gray-800 px-2 py-0.5 rounded text-xs">{car.transmission}</span>}
            {car.owners != null && <span className="bg-gray-800 px-2 py-0.5 rounded text-xs">{car.owners} owner{car.owners > 1 ? 's' : ''}</span>}
          </div>
          {car.city && <span className="text-gray-500">{car.city}</span>}
          {car.source && <span className="text-gray-600 text-xs">{car.source}</span>}
        </div>
        {car.recommendation && (
          <div className={`mt-2 text-xs font-medium ${
            car.recommendation === 'Excellent Deal' ? 'text-green-400' :
            car.recommendation === 'Good Deal' ? 'text-yellow-400' : 'text-gray-500'
          }`}>
            {car.recommendation}
          </div>
        )}
        {car.listing_url && (
          <a href={car.listing_url} target="_blank" rel="noopener noreferrer"
            className="mt-3 block text-center text-sm bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg transition">
            View Listing
          </a>
        )}
      </div>
    </div>
  )
}
