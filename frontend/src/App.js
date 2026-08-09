import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = 'http://127.0.0.1:5000';

function App() {
  const [gameState, setGameState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showRawHeaders, setShowRawHeaders] = useState(false);

  const startSimulation = async () => {
    setLoading(true);
    setError(null);
    setShowRawHeaders(false);
    try {
      const res = await fetch(`${API_BASE_URL}/api/start`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setGameState(data);
    } catch (err) {
      console.error(err);
      setError('Backend communication failed. Ensure Flask app.py is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    startSimulation();
  }, []);

  const handleOptionClick = async (optionId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/next`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_node_id: gameState.current_node.id,
          option_id: optionId,
          risk_score: gameState.risk_score,
          history: gameState.history
        })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setGameState(data);
    } catch (err) {
      console.error(err);
      setError('Error updating decision state.');
    }
  };

  const getRiskLevel = (score) => {
    if (score <= 15) return { text: 'LOW / SECURE', color: '#10B981' };
    if (score <= 45) return { text: 'MODERATE RISK', color: '#F59E0B' };
    return { text: 'CRITICAL BREACH', color: '#EF4444' };
  };

  if (loading) return <div className="app-status">Initializing Threat Engine...</div>;

  if (error) {
    return (
      <div className="layout-wrapper">
        <div className="card error-box">
          <h2>⚠️ Connection Error</h2>
          <p>{error}</p>
          <button className="btn primary-btn" onClick={startSimulation}>Retry Engine</button>
        </div>
      </div>
    );
  }

  const { current_node, risk_score, history, is_completed } = gameState;
  const riskMeta = getRiskLevel(risk_score);

  return (
    <div className="layout-wrapper">
      {/* Top Threat Metrics Bar */}
      <header className="top-nav">
        <div className="brand">
          <span className="dot"></span>
          <h1>SOC Cyber Attack Surface Simulator</h1>
        </div>
        <div className="nav-stats">
          <div className="stat-item">
            <span className="stat-label">Calculated Risk Index</span>
            <span className="stat-value" style={{ color: riskMeta.color }}>
              {risk_score} / 100 ({riskMeta.text})
            </span>
          </div>
        </div>
      </header>

      <main className="main-grid">
        {/* Left Column: Interactive Scenario Environment */}
        <section className="card primary-pane">
          <div className="pane-header">
            <span className="stage-tag">{current_node.title}</span>
            {current_node.email_headers && (
              <button 
                className="btn-outline-sm" 
                onClick={() => setShowRawHeaders(!showRawHeaders)}
              >
                {showRawHeaders ? 'Hide Headers' : 'Inspect Raw Headers'}
              </button>
            )}
          </div>

          {/* Optional Interactive Raw Header Inspector */}
          {showRawHeaders && current_node.email_headers && (
            <div className="header-inspector">
              <div><strong>From:</strong> {current_node.email_headers.from}</div>
              <div><strong>Reply-To:</strong> {current_node.email_headers.reply_to}</div>
              <div><strong>Subject:</strong> {current_node.email_headers.subject}</div>
              <div>
                <strong>SPF Record:</strong> 
                <span className={current_node.email_headers.spf_pass ? "pass" : "fail"}>
                  {current_node.email_headers.spf_pass ? " PASS" : " FAIL / UNVERIFIED"}
                </span>
              </div>
              <div>
                <strong>DKIM Signature:</strong> 
                <span className={current_node.email_headers.dkim_pass ? "pass" : "fail"}>
                  {current_node.email_headers.dkim_pass ? " PASS" : " FAIL"}
                </span>
              </div>
            </div>
          )}

          {/* Browser Address Bar Simulator if on Phishing Page */}
          {current_node.url_bar && (
            <div className="url-bar-simulator">
              <span className="lock-icon">🔒</span>
              <input type="text" readOnly value={current_node.url_bar} />
            </div>
          )}

          {/* Scenario Context Body */}
          <div className="scenario-body">
            <p>{current_node.email_body}</p>
          </div>

          {/* Action Choice Matrix */}
          {!is_completed ? (
            <div className="choices-matrix">
              <h3>Select Response Strategy:</h3>
              {current_node.options.map((opt) => (
                <button
                  key={opt.id}
                  className="choice-btn"
                  onClick={() => handleOptionClick(opt.id)}
                >
                  {opt.text}
                </button>
              ))}
            </div>
          ) : (
            <div className="debrief-box">
              <h2>Simulation Debrief Complete</h2>
              <p>
                {risk_score <= 15
                  ? " Outstanding threat response! You successfully contained the attack without compromising organizational assets."
                  : " Critical Security Breach Detected! Your choices allowed sensitive credentials or MFA session tokens to leak to adversaries."}
              </p>
              <button className="btn primary-btn" onClick={startSimulation}>
                🔄 Restart Simulation
              </button>
            </div>
          )}
        </section>

        {/* Right Column: Live Incident Log Audit Trail */}
        <aside className="card sidebar-pane">
          <h3>Incident Response Audit Log</h3>
          {history.length === 0 ? (
            <p className="empty-log">No actions taken yet. Waiting for operator input...</p>
          ) : (
            <div className="audit-timeline">
              {history.map((item, idx) => (
                <div key={idx} className="timeline-event">
                  <div className="event-head">
                    <span className="step-num">Step {item.step}</span>
                    <span 
                      className="delta-badge"
                      style={{ color: item.risk_impact > 0 ? '#EF4444' : '#10B981' }}
                    >
                      {item.risk_impact > 0 ? `+${item.risk_impact} Risk` : `${item.risk_impact} Risk`}
                    </span>
                  </div>
                  <div className="event-action">{item.action}</div>
                  <div className="event-log">{item.log}</div>
                </div>
              ))}
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}

export default App;