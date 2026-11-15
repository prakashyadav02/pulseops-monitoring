import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './context'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Monitors from './pages/Monitors'
import Incidents from './pages/Incidents'
import Activity from './pages/Activity'
import StatusPage from './pages/StatusPage'
import Settings from './pages/Settings'
import Login from './pages/Login'

export default function App() {
  const { user } = useAuth()
  return <Routes>
    <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
    <Route path="/public/:slug" element={<StatusPage publicOnly />} />
    <Route element={user ? <Layout /> : <Navigate to="/login" replace />}>
      <Route index element={<Dashboard />} />
      <Route path="/monitors" element={<Monitors />} />
      <Route path="/incidents" element={<Incidents />} />
      <Route path="/activity" element={<Activity />} />
      <Route path="/status" element={<StatusPage />} />
      <Route path="/settings" element={<Settings />} />
    </Route>
    <Route path="*" element={<Navigate to={user ? '/' : '/login'} replace />} />
  </Routes>
}
