import { Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Listings from './pages/Listings'
import Deals from './pages/Deals'
import Settings from './pages/Settings'
import Favorites from './pages/Favorites'
import Chat from './pages/Chat'

function Navbar() {
  const linkClass = ({ isActive }) =>
    `px-3 py-2 rounded-lg text-sm font-medium transition ${
      isActive ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'
    }`

  return (
    <nav className="border-b border-gray-800 px-6 py-3 flex items-center gap-6">
      <span className="text-xl font-bold text-white">🚗 Car Hunter AI</span>
      <div className="flex gap-2">
        <NavLink to="/" end className={linkClass}>Dashboard</NavLink>
        <NavLink to="/listings" className={linkClass}>Listings</NavLink>
        <NavLink to="/deals" className={linkClass}>Deals</NavLink>
        <NavLink to="/favorites" className={linkClass}>Favorites</NavLink>
        <NavLink to="/chat" className={linkClass}>AI Chat</NavLink>
        <NavLink to="/settings" className={linkClass}>Settings</NavLink>
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <main className="p-6 max-w-7xl mx-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/listings" element={<Listings />} />
          <Route path="/deals" element={<Deals />} />
          <Route path="/favorites" element={<Favorites />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}
