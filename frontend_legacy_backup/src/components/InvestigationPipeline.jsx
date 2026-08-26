import { useEffect, useState, useRef } from 'react';
import { getDemoRun, approveDemo, rejectDemo } from '../api/demoApi';
import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react';

const STAGE_ORDER = [
  { id: 'repository', name: '01 REPOSITORY', duration: 4000 },
  { id: 'inspection', name: '02 INSPECTION', duration: 5000 },
  { id: 'architecture', name: '03 ARCHITECTURE', duration: 5000 },
  { id: 'failure_detection', name: '04 FAILURE DETECTION', duration: 5000 },
  { id: 'evidence', name: '05 EVIDENCE', duration: 5000 },
  { id: 'ghosttrace', name: '06 GHOSTTRACE', duration: 7000 },
  { id: 'memory', name: '07 FAILURE MEMORY', duration: 5000 },
  { id: 'investigation', name: '08 INVESTIGATION', duration: 8000 },
  { id: 'patch', name: '09 PATCH', duration: 6000 },
  { id: 'compatibility', name: '10 COMPATIBILITY', duration: 5000 },
  { id: 'replay', name: '11 REPLAY', duration: 7000 },
  { id: 'build', name: '12 BUILD', duration: 5000 },
  { id: 'tests', name: '13 TESTS', duration: 5000 },
  { id: 'validation', name: '14 VALIDATION', duration: 6000 },
  { id: 'approval', name: '15 APPROVAL', duration: 100 }, // Wait happens here manually
  { id: 'delivery', name: '16 DELIVERY', duration: 6000 },
  { id: 'memory_update', name: '17 MEMORY UPDATE', duration: 5000 }
];

export default function InvestigationPipeline({ runId, onComplete }) {
  const [backendState, setBackendState] = useState(null);
  const [activeStageIndex, setActiveStageIndex] = useState(0);
  const [approving, setApproving] = useState(false);
  const [pipelineError, setPipelineError] = useState(null);

  // Poll backend
  useEffect(() => {
    let timeoutCount = 0;
    const interval = setInterval(async () => {
      try {
        const data = await getDemoRun(runId);
        timeoutCount = 0;
        setBackendState(data);
        
        if (data.status === 'completed' || data.status === 'failed' || data.status === 'waiting_for_approval') {
          clearInterval(interval);
        }
      } catch (err) {
        timeoutCount++;
        if (timeoutCount > 5) {
          clearInterval(interval);
          setPipelineError("CODEGUARDIAN BACKEND UNAVAILABLE. Start the backend manually and try again.");
        }
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [runId]);

  // Frontend progressive reveal timer
  useEffect(() => {
    if (!backendState || pipelineError) return;
    
    // Stop advancing if we hit approval and waiting
    if (STAGE_ORDER[activeStageIndex].id === 'approval' && backendState.status === 'waiting_for_approval') {
      return;
    }
    
    // Check if current stage is ready from backend (for precomputed demo, usually they are ready quickly)
    const currentStageId = STAGE_ORDER[activeStageIndex].id;
    const isReadyInBackend = backendState.stages?.[currentStageId] === 'passed' || backendState.stages?.[currentStageId] === 'failed' || backendState.status === 'completed';
    
    // Only advance if backend says it's ready, OR if we are completely done and just catching up visually.
    if (isReadyInBackend || backendState.status === 'completed' || backendState.status === 'waiting_for_approval') {
      const timer = setTimeout(() => {
        if (activeStageIndex < STAGE_ORDER.length - 1) {
          setActiveStageIndex(prev => prev + 1);
        } else if (activeStageIndex === STAGE_ORDER.length - 1) {
          // Finished rendering all stages
          onComplete(backendState.results, backendState.status, backendState.error);
        }
      }, STAGE_ORDER[activeStageIndex].duration);
      return () => clearTimeout(timer);
    }
  }, [activeStageIndex, backendState, pipelineError, onComplete]);

  const handleApprove = async () => {
    setApproving(true);
    try {
      await approveDemo(runId);
      // We manually fetch once to get running status and resume the timers.
      const data = await getDemoRun(runId);
      setBackendState(data);
      setActiveStageIndex(prev => prev + 1); // move past approval
      
      // Start polling again for delivery
      const interval = setInterval(async () => {
        try {
          const newData = await getDemoRun(runId);
          setBackendState(newData);
          if (newData.status === 'completed' || newData.status === 'failed') {
            clearInterval(interval);
          }
        } catch (e) {
          // ignore
        }
      }, 1000);
      
    } catch (e) {
      setPipelineError(e.message);
    } finally {
      setApproving(false);
    }
  };
  
  const handleReject = async () => {
    setApproving(true);
    try {
      await rejectDemo(runId);
      onComplete(backendState.results, 'failed', 'PATCH REJECTED');
    } catch (e) {
      setPipelineError(e.message);
    } finally {
      setApproving(false);
    }
  };

  if (!backendState) return <div className="workspace fade-in"><div>Loading...</div></div>;

  const currentStage = STAGE_ORDER[activeStageIndex];
  const results = backendState.results || {};

  return (
    <div className="workspace fade-in">
      {/* LEFT: PROGRESS SIDEBAR */}
      <div className="sidebar">
        {STAGE_ORDER.map((stage, idx) => {
          let statusIcon = <Circle size={16} />;
          let className = 'stage-item';
          
          if (idx < activeStageIndex) {
            className += ' completed';
            statusIcon = <CheckCircle2 size={16} />;
          } else if (idx === activeStageIndex) {
            className += ' active';
            statusIcon = <Loader2 size={16} className="spin" />;
            if (stage.id === 'approval' && backendState.status === 'waiting_for_approval') {
              statusIcon = <Circle size={16} className="color-lime" fill="var(--accent-lime)" />;
            }
          }
          
          return (
            <div key={stage.id} className={className}>
              <div className="stage-icon">{statusIcon}</div>
              <div>{stage.name}</div>
            </div>
          );
        })}
      </div>

      {/* RIGHT: MAIN CONTENT */}
      <div className="content-area">
        {pipelineError && (
          <div className="panel" style={{borderColor: 'var(--accent-red)'}}>
            <h3 className="color-red">ERROR</h3>
            <p>{pipelineError}</p>
          </div>
        )}
        
        {currentStage.id === 'repository' && (
          <div className="fade-in">
            <h2 className="stage-header">REPOSITORY IDENTIFIED</h2>
            <div className="panel">
              <div className="value large">{results.repository?.name || 'JavaAPICheck'}</div>
              <div className="color-muted mono">{results.repository?.url}</div>
              <div className="divider" />
              <div className="panel-row">
                <div>
                  <div className="label">STATUS</div>
                  <div className="color-lime" style={{fontWeight: 600}}>✓ FOUND</div>
                </div>
                <div>
                  <div className="label">BRANCH</div>
                  <div className="mono">main</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {currentStage.id === 'inspection' && (
          <div className="fade-in">
            <h2 className="stage-header">INSPECTING REPOSITORY</h2>
            <div className="panel panel-row">
              <div>
                <div className="value large">{results.inspection?.files_scanned || 15}</div>
                <div className="label">FILES SCANNED</div>
              </div>
              <div>
                <div className="value large">1</div>
                <div className="label">MAVEN PROJECT</div>
              </div>
            </div>
            <div className="panel mono color-muted">
              pom.xml<br/>
              mvnw<br/>
              payment-service/<br/>
              order-service/<br/>
              gateway/<br/>
              README.md
            </div>
          </div>
        )}

        {currentStage.id === 'architecture' && (
          <div className="fade-in">
            <h2 className="stage-header">ARCHITECTURE DETECTED</h2>
            <div className="panel" style={{textAlign: 'center'}}>
              <div className="color-lime" style={{fontWeight: 700, letterSpacing: '0.1em', marginBottom: '32px'}}>JAVA • SPRING BOOT • MAVEN</div>
              <div className="mono" style={{display: 'inline-block', textAlign: 'left', background: 'var(--bg-color)', padding: '32px', borderRadius: '12px', border: '1px solid var(--border-color)'}}>
                CLIENT<br/>
                &nbsp;↓<br/>
                API GATEWAY<br/>
                &nbsp;↓<br/>
                ORDER SERVICE<br/>
                &nbsp;↓<br/>
                PAYMENT SERVICE<br/>
                &nbsp;↓<br/>
                DATABASE
              </div>
            </div>
          </div>
        )}

        {currentStage.id === 'failure_detection' && (
          <div className="fade-in">
            <h2 className="stage-header">FAILURE DETECTED</h2>
            <div className="panel" style={{borderColor: 'var(--accent-red)'}}>
              <div className="color-red" style={{fontSize: '3rem', fontWeight: 800}}>NullPointerException</div>
              <div className="color-red mono" style={{marginTop: '16px', fontWeight: 600}}>NULL_OBJECT_ACCESS</div>
              <div className="divider" />
              <div className="panel-row">
                <div>
                  <div className="label">VISIBLE SYMPTOM</div>
                  <div className="value mono">HTTP 500</div>
                </div>
                <div>
                  <div className="label">SERVICE</div>
                  <div className="value mono">payment-service</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {currentStage.id === 'evidence' && (
          <div className="fade-in">
            <h2 className="stage-header">EVIDENCE</h2>
            <div className="panel mono" style={{fontSize: '0.9rem', lineHeight: 2}}>
              {results.evidence ? results.evidence.map((e, i) => (
                <div key={i} style={{marginBottom: '16px'}}>
                  <span className="color-muted">14:55:4{i}</span><br/>
                  <span className="color-lime">{e.type?.toUpperCase() || 'EVENT'}</span><br/>
                  {e.message}
                </div>
              )) : (
                <>
                  <span className="color-muted">14:55:42</span><br/><span className="color-lime">REQUEST</span><br/>POST /checkout<br/><br/>
                  <span className="color-muted">14:55:43</span><br/><span className="color-lime">PAYMENT</span><br/>repository.findByOrderId()<br/><br/>
                  <span className="color-muted">14:55:44</span><br/><span className="color-red">DATABASE</span><br/>returned null<br/><br/>
                  <span className="color-muted">14:55:45</span><br/><span className="color-red">ERROR</span><br/>NullPointerException<br/><br/>
                  <span className="color-muted">14:55:46</span><br/><span className="color-red">HTTP</span><br/>500 Internal Server Error
                </>
              )}
            </div>
          </div>
        )}

        {currentStage.id === 'ghosttrace' && (
          <div className="fade-in">
            <h2 className="stage-header">GHOSTTRACE</h2>
            <div className="stage-subtitle">RECONSTRUCTING THE HIDDEN FAILURE CHAIN</div>
            <div className="panel" style={{textAlign: 'center', background: '#000'}}>
              <div className="mono" style={{display: 'inline-block', textAlign: 'left', lineHeight: 2}}>
                <span className="color-muted">CLIENT</span><br/>
                <span className="color-muted">&nbsp;↓</span><br/>
                <span className="color-muted">API GATEWAY</span><br/>
                <span className="color-muted">&nbsp;↓</span><br/>
                <span className="color-muted">ORDER SERVICE</span><br/>
                <span className="color-muted">&nbsp;↓</span><br/>
                <span className="color-muted">PAYMENT SERVICE</span><br/>
                <span className="color-lime">&nbsp;↓</span><br/>
                <strong className="color-lime">PaymentProcessingService.charge()</strong><br/>
                <span className="color-lime">&nbsp;↓</span><br/>
                <strong className="color-lime">repository.findByOrderId()</strong><br/>
                <span className="color-red">&nbsp;↓</span><br/>
                <strong className="color-red">NULL</strong><br/>
                <span className="color-red">&nbsp;↓</span><br/>
                <strong className="color-red">NullPointerException</strong><br/>
                <span className="color-red">&nbsp;↓</span><br/>
                <strong className="color-red">HTTP 500</strong>
              </div>
              <div className="divider" />
              <div className="label">ROOT CAUSE CANDIDATE</div>
              <div className="value color-lime mono" style={{fontSize: '1.25rem'}}>PaymentProcessingService.charge()</div>
              <div className="color-muted" style={{marginTop: '16px', fontSize: '0.85rem'}}>SYMPTOM ≠ ROOT CAUSE</div>
            </div>
          </div>
        )}

        {currentStage.id === 'memory' && (
          <div className="fade-in">
            <h2 className="stage-header">FAILURE MEMORY</h2>
            <div className="stage-subtitle">Has CodeGuardian seen this failure before?</div>
            <div className="panel">
              <div className="demo-pill" style={{marginBottom: '24px', display: 'inline-block'}}>ILLUSTRATIVE DEMO MATCH</div>
              <h3 className="color-lime" style={{margin: '0 0 8px 0'}}>MATCH FOUND</h3>
              <div className="color-red mono" style={{marginBottom: '32px'}}>NULL_OBJECT_ACCESS</div>
              
              <div className="panel-row">
                <div>
                  <div className="label">PREVIOUS INCIDENT</div>
                  <div className="value mono">#{results.memory?.matched_incident_id || '102'}</div>
                </div>
                <div>
                  <div className="label">SIMILARITY</div>
                  <div className="value mono">{results.memory?.similarity ? results.memory.similarity * 100 : '87'}%</div>
                </div>
              </div>
              <div className="divider" />
              <div className="label">PREVIOUS RESOLUTION</div>
              <div className="value">{results.memory?.previous_fix || 'Add null validation before object access.'}</div>
              <div className="divider" />
              <div style={{display: 'flex', alignItems: 'center', gap: '16px', justifyContent: 'center'}} className="color-muted mono">
                <div>PAST INCIDENT</div>
                <div>+</div>
                <div>CURRENT FAILURE</div>
                <div>↓</div>
                <div className="color-lime" style={{fontWeight: 700}}>KNOWN ENGINEERING PATTERN</div>
              </div>
            </div>
          </div>
        )}

        {currentStage.id === 'investigation' && (
          <div className="fade-in">
            <h2 className="stage-header">AI INVESTIGATION</h2>
            <div className="stage-subtitle">Correlating evidence with source and verified history.</div>
            <div className="panel">
              <div className="label">OBSERVATION</div>
              <div className="value" style={{marginBottom: '24px'}}>{results.investigation?.observation || 'Payment service received the checkout request.'}</div>
              
              <div className="label">EVIDENCE</div>
              <div className="value" style={{marginBottom: '24px'}}>{results.investigation?.evidence || 'Repository lookup returned null.'}</div>
              
              <div className="label">SOURCE</div>
              <div className="value mono" style={{marginBottom: '24px'}}>{results.investigation?.source || 'PaymentProcessingService.java'}</div>
              
              <div className="label">HYPOTHESIS</div>
              <div className="value" style={{marginBottom: '24px'}}>{results.investigation?.hypothesis || 'paymentRecord is dereferenced before existence validation.'}</div>
              
              <div className="label">HISTORICAL CONTEXT</div>
              <div className="value" style={{marginBottom: '24px'}}>{results.investigation?.context || 'Previous verified NULL_OBJECT_ACCESS incident found.'}</div>
              
              <div className="label">DECISION</div>
              <div className="value" style={{marginBottom: '24px'}}>{results.investigation?.decision || 'Add a null guard before object access.'}</div>
              
              <div className="label color-lime">NEXT ACTION</div>
              <div className="value color-lime">{results.investigation?.next_action || 'Generate minimal Java patch.'}</div>
            </div>
          </div>
        )}

        {currentStage.id === 'patch' && (
          <div className="fade-in">
            <h2 className="stage-header">REPAIR CANDIDATE</h2>
            <div className="stage-subtitle color-lime">MINIMAL CHANGE</div>
            <div className="panel">
              <div className="flex-between" style={{marginBottom: '16px'}}>
                <div className="mono">{results.investigation?.patch_candidate?.file || 'PaymentProcessingService.java'}</div>
                <div className="badge badge-unvalidated">UNVALIDATED</div>
              </div>
              <div className="diff-viewer">
                <div className="color-muted">@@ -42,5 +42,7 @@</div>
                <div>&nbsp;PaymentRecord paymentRecord = repository.findByOrderId(orderId);</div>
                <div className="diff-remove">-process(paymentRecord);</div>
                <div className="diff-add">+if (paymentRecord != null) &#123;</div>
                <div className="diff-add">+&nbsp;&nbsp;&nbsp;&nbsp;process(paymentRecord);</div>
                <div className="diff-add">+&#125;</div>
              </div>
              <div className="panel-row" style={{marginTop: '24px'}}>
                <div>
                  <div className="label">FILES CHANGED</div>
                  <div className="value">1</div>
                </div>
                <div>
                  <div className="label">LINES ADDED</div>
                  <div className="value color-green">3</div>
                </div>
                <div>
                  <div className="label">LINES REMOVED</div>
                  <div className="value color-red">1</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {currentStage.id === 'compatibility' && (
          <div className="fade-in">
            <h2 className="stage-header">PATCH SAFETY</h2>
            <div className="panel">
              <div style={{display: 'flex', flexDirection: 'column', gap: '16px', fontSize: '1.1rem'}}>
                <div className="flex-between"><span>Java source</span><span className="color-green">✓</span></div>
                <div className="flex-between"><span>File path</span><span className="color-green">✓</span></div>
                <div className="flex-between"><span>Context match</span><span className="color-green">✓</span></div>
                <div className="flex-between"><span>No secrets</span><span className="color-green">✓</span></div>
                <div className="flex-between"><span>No .env</span><span className="color-green">✓</span></div>
                <div className="flex-between"><span>No unrelated files</span><span className="color-green">✓</span></div>
              </div>
              <div className="divider" />
              <div className="color-lime" style={{fontSize: '1.25rem', fontWeight: 700, textAlign: 'center'}}>PATCH COMPATIBLE</div>
            </div>
          </div>
        )}

        {currentStage.id === 'replay' && (
          <div className="fade-in">
            <h2 className="stage-header">GHOST REPLAY</h2>
            <div className="stage-subtitle">Reproducing the original failure against the repair.</div>
            <div className="panel-row">
              <div className="panel" style={{margin: 0, borderColor: 'var(--accent-red)'}}>
                <div className="label">ORIGINAL</div>
                <div className="value large color-red mono">HTTP 500</div>
                <div className="color-red mono" style={{marginTop: '16px'}}>NULL_OBJECT_ACCESS</div>
                <div className="color-red" style={{marginTop: '16px', fontWeight: 700}}>FAILED</div>
              </div>
              <div className="panel" style={{margin: 0, borderColor: 'var(--accent-green)'}}>
                <div className="label">PATCHED</div>
                <div className="value large color-green mono">HTTP 200</div>
                <div className="color-green mono" style={{marginTop: '16px'}}>NO ERROR</div>
                <div className="color-green" style={{marginTop: '16px', fontWeight: 700}}>PASSED</div>
              </div>
            </div>
            <div className="panel" style={{marginTop: '24px', textAlign: 'center'}}>
              <div className="label">RESULT</div>
              <div className="value large color-lime">BEHAVIOR CHANGED</div>
              <div className="mono" style={{fontSize: '1.5rem', marginTop: '16px'}}>500 &rarr; 200</div>
            </div>
          </div>
        )}

        {currentStage.id === 'build' && (
          <div className="fade-in">
            <h2 className="stage-header">BUILD VERIFICATION</h2>
            <div className="panel">
              <div className="label">COMMAND</div>
              <div className="mono color-muted">mvnw.cmd clean test</div>
              <div className="divider" />
              <div className="label">STATUS</div>
              <div className="color-green" style={{fontWeight: 700, fontSize: '1.25rem'}}>PASS</div>
              <div className="divider" />
              <div className="mono color-muted" style={{background: '#000', padding: '16px', borderRadius: '8px'}}>
                [INFO] BUILD SUCCESS<br/>
                [INFO] ------------------------------------------------------------------------<br/>
                [INFO] Total time:  4.123 s
              </div>
            </div>
          </div>
        )}

        {currentStage.id === 'tests' && (
          <div className="fade-in">
            <h2 className="stage-header">REGRESSION TESTS</h2>
            <div className="panel">
              <div className="panel-row" style={{marginBottom: '32px'}}>
                <div>
                  <div className="label">TESTS RUN</div>
                  <div className="value large">34</div>
                </div>
                <div>
                  <div className="label color-red">FAILURES</div>
                  <div className="value large">0</div>
                </div>
                <div>
                  <div className="label color-red">ERRORS</div>
                  <div className="value large">0</div>
                </div>
                <div>
                  <div className="label">SKIPPED</div>
                  <div className="value large">0</div>
                </div>
              </div>
              <div className="color-green" style={{fontSize: '1.5rem', fontWeight: 700, textAlign: 'center'}}>
                ALL REQUIRED TESTS PASSED
              </div>
            </div>
          </div>
        )}

        {currentStage.id === 'validation' && (
          <div className="fade-in">
            <h2 className="stage-header">VALIDATION</h2>
            <div className="panel">
              <div style={{display: 'flex', flexDirection: 'column', gap: '24px', fontSize: '1.25rem', fontWeight: 600}}>
                <div className="flex-between"><span>PATCH CONTEXT</span><span className="color-green">✓</span></div>
                <div className="flex-between"><span>PATH SAFETY</span><span className="color-green">✓</span></div>
                <div className="flex-between"><span>REPLAY</span><span className="color-green">✓</span></div>
                <div className="flex-between"><span>BUILD</span><span className="color-green">✓</span></div>
                <div className="flex-between"><span>TESTS</span><span className="color-green">✓</span></div>
                <div className="flex-between"><span>FINAL VALIDATION</span><span className="color-green">✓</span></div>
              </div>
              <div className="divider" />
              <div className="color-lime" style={{fontSize: '2.5rem', fontWeight: 800, textAlign: 'center'}}>PATCH VALIDATED</div>
            </div>
          </div>
        )}

        {currentStage.id === 'approval' && (
          <div className="fade-in">
            <h2 className="stage-header">PATCH READY FOR REVIEW</h2>
            <div className="panel" style={{border: '2px solid var(--accent-lime)'}}>
              <div className="panel-row" style={{marginBottom: '24px'}}>
                <div><div className="label">ROOT CAUSE</div><div className="mono">PaymentProcessingService.charge()</div></div>
                <div><div className="label">AFFECTED FILE</div><div className="mono">PaymentProcessingService.java</div></div>
                <div><div className="label color-green">PATCH</div><div className="color-green" style={{fontWeight:600}}>✓ VALIDATED</div></div>
                <div><div className="label color-green">REPLAY</div><div className="color-green" style={{fontWeight:600}}>✓ 500 &rarr; 200</div></div>
                <div><div className="label color-green">BUILD</div><div className="color-green" style={{fontWeight:600}}>✓ PASS</div></div>
                <div><div className="label color-green">TESTS</div><div className="color-green" style={{fontWeight:600}}>✓ PASS</div></div>
              </div>
              
              <div className="diff-viewer" style={{marginBottom: '32px'}}>
                <div className="color-muted">@@ -42,5 +42,7 @@</div>
                <div>&nbsp;PaymentRecord paymentRecord = repository.findByOrderId(orderId);</div>
                <div className="diff-remove">-process(paymentRecord);</div>
                <div className="diff-add">+if (paymentRecord != null) &#123;</div>
                <div className="diff-add">+&nbsp;&nbsp;&nbsp;&nbsp;process(paymentRecord);</div>
                <div className="diff-add">+&#125;</div>
              </div>

              {backendState.status === 'waiting_for_approval' ? (
                <div style={{display: 'flex', gap: '24px', justifyContent: 'flex-end'}}>
                  <button className="btn-danger" onClick={handleReject} disabled={approving}>REJECT PATCH</button>
                  <button className="btn-primary" onClick={handleApprove} disabled={approving}>APPROVE &amp; CREATE FEATURE BRANCH &rarr;</button>
                </div>
              ) : (
                <div className="color-lime" style={{fontWeight: 700, textAlign: 'right'}}>APPROVAL GRANTED</div>
              )}
            </div>
          </div>
        )}

        {currentStage.id === 'delivery' && (
          <div className="fade-in">
            <h2 className="stage-header">READY TO SHIP</h2>
            <div className="panel" style={{border: '1px solid var(--accent-blue)'}}>
              <div className="demo-pill" style={{marginBottom: '24px', display: 'inline-block', borderColor: 'var(--accent-blue)', color: 'var(--accent-blue)', background: 'rgba(59, 130, 246, 0.1)'}}>SIMULATED DELIVERY</div>
              
              <div style={{display: 'flex', flexDirection: 'column', gap: '16px'}}>
                <div className="flex-between">
                  <span className="label" style={{margin:0}}>REPOSITORY</span>
                  <span className="mono">sunilkumarb2007 / JavaAPICheck</span>
                </div>
                <div className="flex-between">
                  <span className="label" style={{margin:0}}>BASE</span>
                  <span className="mono">main</span>
                </div>
                <div className="flex-between">
                  <span className="label" style={{margin:0}}>FEATURE</span>
                  <span className="mono">{results.delivery?.branch || 'feature/codeguardian/null-object-access'}</span>
                </div>
                <div className="flex-between">
                  <span className="label" style={{margin:0}}>COMMIT</span>
                  <span className="mono">fix: guard missing payment record</span>
                </div>
                <div className="flex-between">
                  <span className="label" style={{margin:0}}>PULL REQUEST</span>
                  <span className="mono color-blue">DEMO-PR-001</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {currentStage.id === 'memory_update' && (
          <div className="fade-in">
            <h2 className="stage-header">FAILURE MEMORY UPDATED</h2>
            <div className="panel">
              <div className="flex-between" style={{marginBottom: '24px'}}>
                <div className="label">STATUS</div>
                <div className="color-lime" style={{fontWeight: 700, fontSize: '1.25rem'}}>VERIFIED</div>
              </div>
              
              <div className="panel-row" style={{marginBottom: '32px'}}>
                <div><div className="label">ERROR PATTERN</div><div className="mono">NULL_OBJECT_ACCESS</div></div>
                <div><div className="label">ROOT CAUSE</div><div className="mono">PaymentProcessingService.charge()</div></div>
                <div><div className="label">AFFECTED FILE</div><div className="mono">PaymentProcessingService.java</div></div>
                <div><div className="label">CODE CHANGE</div><div className="mono">+ null guard</div></div>
                <div><div className="label color-green">VALIDATION</div><div className="color-green" style={{fontWeight:600}}>✓ SUCCESS</div></div>
                <div><div className="label">DELIVERY REF</div><div className="mono">DEMO-PR-001</div></div>
              </div>

              <div className="color-muted" style={{textAlign: 'center', fontSize: '1.1rem', letterSpacing: '0.05em', textTransform: 'uppercase'}}>
                THE NEXT INVESTIGATION STARTS WITH ENGINEERING KNOWLEDGE.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
