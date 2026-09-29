import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Compass, Settings } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import AskEngine from './pages/AskEngine';
import ProblemExplorer from './pages/ProblemExplorer';
import './index.css';

const Sidebar = () => {
  return (
    <div style={{
      width: '260px',
      backgroundColor: 'var(--bg-secondary)',
      borderRight: '1px solid rgba(255, 255, 255, 0.05)',
      display: 'flex',
      flexDirection: 'column',
      padding: 'var(--spacing-6)',
      height: '100vh',
      position: 'fixed'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--spacing-3)',
        marginBottom: '48px'
      }}>
        <div style={{
          width: '32px',
          height: '32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <img src="https://www.gstatic.com/images/branding/product/2x/photos_96dp.png" alt="Google Photos" style={{ width: '100%', height: '100%' }} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em', background: 'var(--accent-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', lineHeight: 1.2 }}>
            Discovery Engine
          </h1>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '2px' }}>
            Google Photos Research
          </div>
        </div>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
        <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} style={navLinkStyle}>
          <LayoutDashboard size={20} /> Dashboard
        </NavLink>
        <NavLink to="/ask" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} style={navLinkStyle}>
          <MessageSquare size={20} /> Ask AI
        </NavLink>
        <NavLink to="/explore" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} style={navLinkStyle}>
          <Compass size={20} /> Problem Explorer
        </NavLink>
      </nav>

      <div style={{ marginTop: 'auto', paddingTop: '24px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
        <div style={navLinkStyle}>
          <Settings size={20} /> Settings
        </div>
      </div>
    </div>
  );
};

const navLinkStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
  padding: '12px 16px',
  borderRadius: '8px',
  color: 'var(--text-secondary)',
  textDecoration: 'none',
  fontWeight: 500,
  transition: 'all 0.2s',
  cursor: 'pointer'
};

const App = () => {
  return (
    <BrowserRouter>
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <Sidebar />
        <main style={{ 
          marginLeft: '260px', 
          flex: 1, 
          padding: 'var(--spacing-8) 48px',
          maxWidth: '1400px'
        }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/ask" element={<AskEngine />} />
            <Route path="/explore/*" element={<ProblemExplorer />} />
          </Routes>
        </main>
      </div>
      
      {/* Dynamic styles for NavLink active state since we can't use pseudo-classes in inline styles easily */}
      <style>{`
        .nav-link:hover {
          background-color: var(--bg-tertiary);
          color: var(--text-primary) !important;
        }
        .nav-link.active {
          background-color: rgba(59, 130, 246, 0.1);
          color: var(--accent-primary) !important;
        }
      `}</style>
    </BrowserRouter>
  );
};

export default App;
