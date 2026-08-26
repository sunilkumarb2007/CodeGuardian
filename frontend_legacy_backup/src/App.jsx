import { useState } from 'react';
import RepositoryInput from './components/RepositoryInput';
import InvestigationPipeline from './components/InvestigationPipeline';
import FinalResult from './components/FinalResult';
import './index.css';

export default function App() {
  const [stage, setStage] = useState('INPUT'); // INPUT, PIPELINE, RESULT
  const [runId, setRunId] = useState(null);
  const [results, setResults] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  const handleInvestigate = (id) => {
    setRunId(id);
    setStage('PIPELINE');
  };

  const handleComplete = (finalResults, finalStatus, finalError) => {
    setResults(finalResults);
    setStatus(finalStatus);
    setError(finalError);
    setStage('RESULT');
  };
  
  const resetApp = () => {
    setStage('INPUT');
    setRunId(null);
    setResults(null);
  };

  return (
    <>
      <nav className="top-nav">
        <div className="nav-brand">CODEGUARDIAN</div>
        <div className="nav-links">
          <a href="#" className="nav-link" style={{color: 'var(--text-main)'}}>Product</a>
          <a href="#" className="nav-link">How it works</a>
          <a href="#" className="nav-link">Investigation</a>
          <a href="#" className="nav-link">Architecture</a>
        </div>
        <div className="nav-right">
          <div className="demo-pill">DEMO MODE</div>
          <button className="btn-secondary" style={{padding: '8px 16px', fontSize: '0.9rem'}} onClick={resetApp}>Investigate</button>
        </div>
      </nav>

      <div className="container">
        {stage === 'INPUT' && (
          <RepositoryInput onInvestigate={handleInvestigate} />
        )}
        
        {stage === 'PIPELINE' && (
          <InvestigationPipeline runId={runId} onComplete={handleComplete} />
        )}
        
        {stage === 'RESULT' && (
          <FinalResult results={results} status={status} error={error} onReset={resetApp} />
        )}
      </div>
    </>
  );
}
