import { useState } from 'react';
import { startDemo } from '../api/demoApi';

export default function RepositoryInput({ onInvestigate }) {
  const [url, setUrl] = useState('https://github.com/sunilkumarb2007/JavaAPICheck');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (url !== 'https://github.com/sunilkumarb2007/JavaAPICheck') {
      setError('PREPARED DEMO NOT AVAILABLE. Current prepared scenario: JavaAPICheck');
      return;
    }
    setError('');
    setLoading(true);
    
    try {
      const data = await startDemo(url);
      onInvestigate(data.run_id);
    } catch (err) {
      setError(err.message === 'Failed to fetch' ? 'CODEGUARDIAN BACKEND UNAVAILABLE. Start the backend manually and try again.' : err.message);
      setLoading(false);
    }
  };

  return (
    <div className="hero fade-in">
      <div className="hero-left">
        <div className="hero-eyebrow">Engineering Failure Investigation</div>
        <h1>FROM FAILURE<br/>TO VERIFIED REPAIR.</h1>
        <div className="hero-subtitle">
          Trace failures. Reconstruct hidden causes. Reuse engineering knowledge. Validate repairs. Prepare safe delivery.
        </div>
        
        <form onSubmit={handleSubmit} style={{marginBottom: '24px'}}>
          <label style={{display: 'block', marginBottom: '12px', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase'}}>GitHub Repository</label>
          <div className="input-box">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/..."
              disabled={loading}
            />
            <button type="submit" className="btn-primary" disabled={loading}>
              INVESTIGATE FAILURE &rarr;
            </button>
          </div>
        </form>
        
        {error && <div className="color-red" style={{marginBottom: '16px', fontWeight: 500}}>{error}</div>}
        
        <div className="demo-pill" style={{display: 'inline-block'}}>DEMO MODE — PRECOMPUTED INVESTIGATION</div>
      </div>
      
      <div className="hero-right">
        <div className="panel" style={{background: 'var(--bg-surface)', border: '1px solid var(--border-light)'}}>
          <div style={{display: 'flex', flexDirection: 'column', gap: '24px'}}>
            <div className="flex-between">
              <span className="color-red mono" style={{fontWeight: 700}}>FAILURE</span>
              <span className="color-muted">01</span>
            </div>
            <div className="divider" style={{margin: '0'}}/>
            <div className="flex-between">
              <span className="color-muted mono" style={{fontWeight: 700}}>GHOSTTRACE</span>
              <span className="color-muted">02</span>
            </div>
            <div className="divider" style={{margin: '0'}}/>
            <div className="flex-between">
              <span className="color-lime mono" style={{fontWeight: 700}}>ROOT CAUSE</span>
              <span className="color-muted">03</span>
            </div>
            <div className="divider" style={{margin: '0'}}/>
            <div className="flex-between">
              <span className="color-muted mono" style={{fontWeight: 700}}>PATCH</span>
              <span className="color-muted">04</span>
            </div>
            <div className="divider" style={{margin: '0'}}/>
            <div className="flex-between">
              <span className="color-green mono" style={{fontWeight: 700}}>VALIDATION</span>
              <span className="color-muted">05</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

