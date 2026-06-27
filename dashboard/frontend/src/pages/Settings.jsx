import { useState, useEffect } from 'react'
import { api } from '../utils/api'

const defaultPrefs = {
  budget_min: '', budget_max: '',
  preferred_models: '', cities: '', max_kms: '',
  fuel_types: '', transmission: '', colors: '',
}

export default function Settings() {
  const [prefs, setPrefs] = useState(defaultPrefs)
  const [profiles, setProfiles] = useState([])
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    api.getPreferences().then(data => {
      setPrefs({
        budget_min: data.budget_min ?? '',
        budget_max: data.budget_max ?? '',
        preferred_models: (data.preferred_models || []).join(', '),
        cities: (data.cities || []).join(', '),
        max_kms: data.max_kms ?? '',
        fuel_types: (data.fuel_types || []).join(', '),
        transmission: data.transmission ?? '',
        colors: (data.colors || []).join(', '),
      })
    }).catch(console.error)

    api.getSearchProfiles().then(setProfiles).catch(console.error)
  }, [])

  function handleChange(e) {
    setPrefs(p => ({ ...p, [e.target.name]: e.target.value }))
  }

  async function handleSave(e) {
    e.preventDefault()
    setSaving(true)
    setMessage('')
    try {
      await api.savePreferences({
        budget_min: prefs.budget_min ? Number(prefs.budget_min) : null,
        budget_max: prefs.budget_max ? Number(prefs.budget_max) : null,
        preferred_models: prefs.preferred_models.split(',').map(s => s.trim()).filter(Boolean),
        cities: prefs.cities.split(',').map(s => s.trim()).filter(Boolean),
        max_kms: prefs.max_kms ? Number(prefs.max_kms) : null,
        fuel_types: prefs.fuel_types.split(',').map(s => s.trim()).filter(Boolean),
        transmission: prefs.transmission || null,
        colors: prefs.colors.split(',').map(s => s.trim()).filter(Boolean),
      })
      setMessage('Preferences saved! Searching all sites for matching cars... Check Telegram for results.')
    } catch (e) {
      setMessage('Error saving preferences')
    } finally {
      setSaving(false)
    }
  }

  async function testTelegram() {
    try {
      await api.testNotification('telegram')
      setMessage('Test notification sent!')
    } catch (e) {
      setMessage('Telegram not configured.')
    }
  }

  function Field({ label, name, placeholder = '', type = 'text' }) {
    return (
      <div>
        <label className="block text-sm text-gray-400 mb-1">{label}</label>
        {type === 'textarea' ? (
          <textarea name={name} value={prefs[name]} onChange={handleChange} placeholder={placeholder}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500" rows={2} />
        ) : (
          <input type={type} name={name} value={prefs[name]} onChange={handleChange} placeholder={placeholder}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500" />
        )}
      </div>
    )
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Search Preferences</h2>
        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Budget Min (₹)" name="budget_min" type="number" placeholder="500000" />
            <Field label="Budget Max (₹)" name="budget_max" type="number" placeholder="900000" />
          </div>
          <Field label="Preferred Models (comma separated)" name="preferred_models" placeholder="Honda City, Hyundai Verna" />
          <Field label="Cities (comma separated)" name="cities" placeholder="Bangalore, Hyderabad, Chennai" />
          <div className="grid grid-cols-2 gap-4">
            <Field label="Max KMs" name="max_kms" type="number" placeholder="50000" />
            <Field label="Transmission" name="transmission" placeholder="Automatic" />
          </div>
          <Field label="Fuel Types (comma separated)" name="fuel_types" placeholder="Petrol, Diesel" />
          <Field label="Colors (comma separated)" name="colors" placeholder="White, Black" />
          <button type="submit" disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-2 rounded-lg text-sm transition">
            {saving ? 'Saving...' : 'Save Preferences'}
          </button>
          {message && <p className={`text-sm ${message.includes('Error') ? 'text-red-400' : 'text-green-400'}`}>{message}</p>}
        </form>
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Notifications</h2>
        <button onClick={testTelegram}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition">
          Test Telegram Notification
        </button>
      </div>

      {profiles.length > 0 && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <h2 className="text-lg font-semibold mb-4">Search Profiles</h2>
          <div className="space-y-3">
            {profiles.map(p => (
              <div key={p.id} className="bg-gray-800 rounded-lg p-3">
                <div className="text-white font-medium">{p.profile_name}</div>
                <div className="text-sm text-gray-400 mt-1">
                  Budget: {p.budget_min ? `₹${p.budget_min.toLocaleString()}` : '—'} – {p.budget_max ? `₹${p.budget_max.toLocaleString()}` : '—'}
                  {(p.cities?.length > 0) && ` · Cities: ${p.cities.join(', ')}`}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
