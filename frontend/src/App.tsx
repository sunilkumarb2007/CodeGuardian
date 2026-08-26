import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import Landing from './pages/Landing'
import Investigation from './pages/Investigation'

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/runs/:runId" element={<Investigation />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  )
}
