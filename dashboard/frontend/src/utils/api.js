const BASE = '/api'

async function fetchJSON(url, opts = {}) {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const api = {
  getCars(params = {}) {
    const q = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([_, v]) => v != null && v !== ''))
    ).toString()
    return fetchJSON(`/cars?${q}`)
  },

  getCar(id) {
    return fetchJSON(`/cars/${id}`)
  },

  getDeals(threshold = 85) {
    return fetchJSON(`/deals?threshold=${threshold}`)
  },

  getStats() {
    return fetchJSON('/stats')
  },

  getPreferences() {
    return fetchJSON('/preferences')
  },

  savePreferences(data) {
    return fetchJSON('/preferences', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  getSearchProfiles() {
    return fetchJSON('/search-profiles')
  },

  createSearchProfile(data) {
    return fetchJSON('/search-profiles', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  getFavorites() {
    return fetchJSON('/favorites')
  },

  addFavorite(carId) {
    return fetchJSON(`/favorites/${carId}`, { method: 'POST' })
  },

  removeFavorite(carId) {
    return fetchJSON(`/favorites/${carId}`, { method: 'DELETE' })
  },

  getNotifications(limit = 50) {
    return fetchJSON(`/notifications?limit=${limit}`)
  },

  testNotification(channel = 'telegram') {
    return fetchJSON(`/notifications/test?channel=${channel}`, { method: 'POST' })
  },

  async chat(message) {
    const res = await fetch(`${BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },
}
