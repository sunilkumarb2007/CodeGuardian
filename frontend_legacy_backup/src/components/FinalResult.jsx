export default function FinalResult({ results, status, error, onReset }) {
  if (status === 'failed' || error) {
    return (
      <div className="panel fade-in" style={{borderColor: 'var(--accent-red)'}}>
        <h2 className="color-red">CODEGUARDIAN PIPELINE STOPPED</h2>
        <div style={{marginTop: '16px'}}>
          <p>Status: <strong className="color-red">FAILED</strong></p>
          <p>Error: {error}</p>
        </div>
        <button className="btn-secondary" onClick={onReset} style={{marginTop: '24px'}}>BACK TO REPOSITORY</button>
      </div>
    );
  }

  if (!results) return null;

  return (
    <div className="fade-in" style={{padding: '40px 0'}}>
      <div className="demo-pill" style={{marginBottom: '24px', display: 'inline-block'}}>DEMO MODE — PRECOMPUTED ENGINEERING SCENARIO</div>
      
      <h1 style={{fontSize: '4.5rem', fontWeight: 800, letterSpacing: '-0.03em', lineHeight: 1.1, marginBottom: '64px'}}>
        FROM FAILURE<br/>TO VERIFIED REPAIR.
      </h1>
      
      <div className="panel-row" style={{marginBottom: '40px'}}>
        <div className="panel" style={{margin: 0}}>
          <div className="label">FAILURE</div>
          <div className="value large color-red mono">{results.failure_detection?.fingerprint || 'NullPointerException'}</div>
        </div>
        
        <div className="panel" style={{margin: 0}}>
          <div className="label">ROOT CAUSE</div>
          <div className="value mono">{results.memory_update?.root_cause || 'PaymentProcessingService.charge()'}</div>
        </div>
        
        <div className="panel" style={{margin: 0}}>
          <div className="label">PATCH</div>
          <div className="value large color-lime">VALIDATED</div>
        </div>
        
        <div className="panel" style={{margin: 0}}>
          <div className="label">REPLAY</div>
          <div className="value large mono color-green">500 &rarr; 200</div>
        </div>
        
        <div className="panel" style={{margin: 0}}>
          <div className="label">TESTS</div>
          <div className="value large color-green">PASS</div>
        </div>
        
        <div className="panel" style={{margin: 0}}>
          <div className="label">DELIVERY</div>
          <div className="value large color-blue">SIMULATED</div>
        </div>
      </div>
      
      <div className="panel" style={{textAlign: 'center', marginBottom: '64px'}}>
        <div className="label">MEMORY</div>
        <div className="value large color-lime">VERIFIED</div>
        <div className="color-muted" style={{marginTop: '16px'}}>This pattern has been recorded for future investigations.</div>
      </div>
      
      <div style={{display: 'flex', gap: '24px', justifyContent: 'center'}}>
        <button className="btn-primary" onClick={onReset}>RUN DEMO AGAIN &rarr;</button>
        <button className="btn-secondary" onClick={onReset}>BACK TO REPOSITORY</button>
      </div>
    </div>
  );
}
