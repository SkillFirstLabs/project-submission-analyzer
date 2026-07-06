import React, { useState, useEffect, useRef } from 'react';

// API Base URL
const API_BASE = 'http://127.0.0.1:8000';

// ─── Timeline data ────────────────────────────────────────────────────────────
const TIMELINE_STEPS = [
  {
    step: '01',
    title: 'Submit Your Project',
    body: 'Upload a ZIP of your codebase along with the expected learning outcomes. Our extractor safely reads every file, dependency manifest, and snippet — no server storage required.',
  },
  {
    step: '02',
    title: 'Automated Analysis',
    body: 'The AI maps your codebase to a set of inferred skills, cross-references them against your stated outcomes, and produces a structured gap analysis in seconds.',
  },
  {
    step: '03',
    title: 'Contextual Viva',
    body: 'Receive codebase-specific questions that go beyond generic prompts — tailored to your architecture, your file structure, and your actual implementations.',
  },
  {
    step: '04',
    title: 'Live Proctoring',
    body: 'A privacy-first integrity layer runs entirely client-side. No video is recorded or transmitted. Only lightweight, anonymous, timestamped event signals are streamed to calculate your integrity score.',
  },
];

// ─── TimelineSection Component ─────────────────────────────────────────────────
function TimelineSection() {
  const sectionRef = useRef(null);
  const itemRefs = useRef([]);
  const spineRef = useRef(null);
  const fillRef = useRef(null);

  // Intersection Observer for items
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.25 }
    );
    itemRefs.current.forEach((el) => { if (el) observer.observe(el); });
    return () => observer.disconnect();
  }, []);

  // Scroll-driven spine fill
  useEffect(() => {
    const handleScroll = () => {
      if (!sectionRef.current || !fillRef.current) return;
      const rect = sectionRef.current.getBoundingClientRect();
      const totalHeight = sectionRef.current.offsetHeight;
      const scrolled = Math.max(0, -rect.top + window.innerHeight * 0.5);
      const pct = Math.min(100, (scrolled / totalHeight) * 100);
      fillRef.current.style.height = `${pct}%`;
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="timeline-section" ref={sectionRef}>
      {/* Spine */}
      <div className="timeline-spine" ref={spineRef}>
        <div className="timeline-spine-fill" ref={fillRef} style={{ height: '0%' }} />
      </div>

      {TIMELINE_STEPS.map((item, i) => (
        <div
          key={i}
          className="timeline-item"
          ref={(el) => (itemRefs.current[i] = el)}
          style={{ transitionDelay: `${i * 0.08}s` }}
        >
          <div className="timeline-content">
            <h3>{item.title}</h3>
            <p>{item.body}</p>
          </div>
          <div className="timeline-node">{item.step}</div>
          {/* Spacer on the other side */}
          <div style={{ flex: 1 }} />
        </div>
      ))}
    </div>
  );
}



// ─── LoadingOverlay Component ──────────────────────────────────────────────────
function LoadingOverlay({ label = 'Processing', sub = 'This may take a few seconds…' }) {
  return (
    <div className="loading-overlay">
      <div className="loading-ring" />
      <div className="loading-label">{label}</div>
      <div className="loading-sub" style={{ marginBottom: '1rem' }}>{sub}</div>
      <div className="loading-dots">
        <span /><span /><span />
      </div>
    </div>
  );
}

// ─── AuthPage Component ────────────────────────────────────────────────────────
function AuthPage({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('student');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      if (isLogin) {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);
        
        const res = await fetch(`${API_BASE}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData.toString()
        });
        
        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail || 'Login failed');
        }
        const data = await res.json();
        
        // Parse JWT to get role
        const token = data.access_token;
        const payload = JSON.parse(atob(token.split('.')[1]));
        const userRole = payload.role;
        
        onLogin(token, userRole);
      } else {
        const res = await fetch(`${API_BASE}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, name, role })
        });
        
        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail || 'Registration failed');
        }
        
        // Auto switch to login
        setIsLogin(true);
        setError('Registration successful! Please log in.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-primary)' }}>
      <div className="glass-card" style={{ width: '100%', maxWidth: '400px', padding: '2.5rem', textAlign: 'center' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
          <img src="/AIvaluate-removebg-preview.png" alt="AIvaluate Logo" style={{ height: '3.5rem', width: 'auto' }} />
        </div>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', fontSize: '0.95rem' }}>
          {isLogin ? 'Sign in to continue' : 'Create a new account'}
        </p>

        {error && (
          <div style={{ padding: '0.75rem', marginBottom: '1.5rem', background: error.includes('successful') ? 'rgba(52, 168, 83, 0.1)' : 'rgba(219, 68, 55, 0.1)', color: error.includes('successful') ? '#34a853' : '#db4437', borderRadius: '6px', fontSize: '0.9rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', textAlign: 'left' }}>
          {!isLogin && (
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Full Name</label>
              <input type="text" value={name} onChange={e => setName(e.target.value)} required className="form-input" placeholder="Jane Doe" style={{ width: '100%', boxSizing: 'border-box', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }} />
            </div>
          )}
          
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Email Address</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required className="form-input" placeholder="you@example.com" style={{ width: '100%', boxSizing: 'border-box', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }} />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required className="form-input" placeholder="••••••••" style={{ width: '100%', boxSizing: 'border-box', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }} />
          </div>

          {!isLogin && (
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Role</label>
              <select value={role} onChange={e => setRole(e.target.value)} className="form-input" style={{ width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}>
                <option value="student">Student</option>
                <option value="mentor">Mentor</option>
              </select>
            </div>
          )}

          <button type="submit" className="btn btn-primary" disabled={loading} style={{ marginTop: '1rem', width: '100%', boxSizing: 'border-box', justifyContent: 'center' }}>
            {loading ? 'Please wait...' : (isLogin ? 'Log In' : 'Sign Up')}
          </button>
        </form>

        <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(255,255,255,0.5)', borderRadius: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          <strong>Test Credentials (Auto-Login):</strong><br/>
          Email: <code>admin@aivaluate.com</code><br/>
          Password: <code>password123</code>
          <div style={{ marginTop: '0.5rem' }}>
            <button 
              onClick={(e) => { e.preventDefault(); setEmail('admin@aivaluate.com'); setPassword('password123'); }}
              style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '4px', cursor: 'pointer' }}
            >
              Fill Details
            </button>
          </div>
        </div>
        
        <p style={{ marginTop: '2rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <span style={{ color: 'var(--accent-primary)', cursor: 'pointer', fontWeight: '500' }} onClick={() => { setIsLogin(!isLogin); setError(''); }}>
            {isLogin ? 'Sign up' : 'Log in'}
          </span>
        </p>
      </div>
    </div>
  );
}

// ─── Mentor Dashboard Component ───────────────────────────────────────────────
function MentorDashboard({ authToken, onLogout, API_BASE, onViewReport }) {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSubmissions = async () => {
      try {
        const res = await fetch(`${API_BASE}/mentor/submissions`, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) throw new Error('Failed to fetch submissions');
        const data = await res.json();
        setSubmissions(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchSubmissions();
  }, [authToken, API_BASE]);

  const handleExport = async (id, format) => {
    window.open(`${API_BASE}/reports/${id}/export?format=${format}&token=${authToken}`, '_blank');
    // Note: for real apps, better to fetch and trigger download since token in query is less secure.
  };

  const handleView = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/mentor/sessions/${id}`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (!res.ok) throw new Error('Failed to fetch report');
      const data = await res.json();
      onViewReport(data);
    } catch (err) {
      alert('Error fetching report: ' + err.message);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2>Mentor Dashboard</h2>
        <button className="btn btn-secondary" onClick={onLogout} style={{ border: '1px solid #dc2626', color: '#dc2626' }}>Logout</button>
      </div>

      {loading && <p>Loading submissions...</p>}
      {error && <p style={{ color: '#dc2626' }}>{error}</p>}

      {!loading && !error && (
        <table style={{ width: '100%', borderCollapse: 'collapse', background: 'var(--bg-secondary)', borderRadius: '8px', overflow: 'hidden' }}>
          <thead>
            <tr style={{ background: 'rgba(0,0,0,0.05)', textAlign: 'left' }}>
              <th style={{ padding: '1rem' }}>Project Title</th>
              <th style={{ padding: '1rem' }}>Status</th>
              <th style={{ padding: '1rem' }}>Integrity Score</th>
              <th style={{ padding: '1rem' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {submissions.map(sub => (
              <tr key={sub.id} style={{ borderTop: '1px solid var(--border-color)' }}>
                <td style={{ padding: '1rem' }}>{sub.project_title}</td>
                <td style={{ padding: '1rem' }}>
                  <span className={`badge badge-${sub.viva_status === 'completed' ? 'low' : 'medium'}`}>
                    {sub.viva_status}
                  </span>
                </td>
                <td style={{ padding: '1rem' }}>{sub.integrity_score || '-'}</td>
                <td style={{ padding: '1rem', display: 'flex', gap: '0.5rem' }}>
                  {sub.viva_status === 'completed' && (
                    <>
                      <button onClick={() => handleView(sub.id)} className="btn btn-primary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}>View</button>
                      <button onClick={() => handleExport(sub.id, 'json')} className="btn btn-secondary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}>JSON</button>
                      <button onClick={() => handleExport(sub.id, 'pdf')} className="btn btn-secondary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}>PDF</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
            {submissions.length === 0 && (
              <tr>
                <td colSpan="4" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  No submissions yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default function App() {
  // App state: 'auth' | 'landing' | 'upload' | 'consent' | 'viva' | 'report' | 'mentor_dashboard' | 'mentor_live_view'
  const [view, setView] = useState('auth');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Auth state
  const [authToken, setAuthToken] = useState(localStorage.getItem('token') || null);
  const [userRole, setUserRole] = useState(localStorage.getItem('role') || null);
  
  useEffect(() => {
    if (authToken && userRole) {
      setView(userRole === 'mentor' ? 'mentor_dashboard' : 'landing');
    }
  }, [authToken, userRole]);

  const handleLogin = (token, role) => {
    localStorage.setItem('token', token);
    localStorage.setItem('role', role);
    setAuthToken(token);
    setUserRole(role);
    setView(role === 'mentor' ? 'mentor_dashboard' : 'landing');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    setAuthToken(null);
    setUserRole(null);
    setView('auth');
  };

  // Upload state
  const [projectTitle, setProjectTitle] = useState('Task Manager App');
  const [projectDescription, setProjectDescription] = useState('A simple backend/frontend task planner using FastAPI and React.');
  const [projectOutcomes, setProjectOutcomes] = useState("1. Complete CRUD operations for tasks\n2. Integrate SQLite/PostgreSQL database\n3. Responsive frontend design");
  const [zipFile, setZipFile] = useState(null);
  const [questionsPerSkill, setQuestionsPerSkill] = useState(2);

  // Analysis result cache
  const [analysisData, setAnalysisData] = useState(null);
  const [sessionId, setSessionId] = useState('');

  // Active Viva session state
  const [consentAcknowledged, setConsentAcknowledged] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [sessionFlags, setSessionFlags] = useState([]);
  const [isTabActive, setIsTabActive] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Final Report state
  const [finalReport, setFinalReport] = useState(null);
  const [showRawJson, setShowRawJson] = useState(false);
  const [showExitModal, setShowExitModal] = useState(false);

  // Inactivity tracking
  const [inactivityCountdown, setInactivityCountdown] = useState(null);
  const lastActivityRef = useRef(Date.now());

  // Scroll to top on view change
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [view]);

  // Media & canvas references
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const proctorIntervalRef = useRef(null);
  const audioContextRef = useRef(null);
  const audioAnalyserRef = useRef(null);

  // Simple simulator inputs (for demo verification)
  const [simulatedEvent, setSimulatedEvent] = useState('gaze_off_screen');
  const [simulatedDuration, setSimulatedDuration] = useState(4000);

  // 1. Handle Submit Zip for Analysis
  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!zipFile) {
      setError('Please upload a project ZIP file.');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('project_title', projectTitle);
    formData.append('project_description', projectDescription);
    formData.append('project_outcomes', projectOutcomes);
    formData.append('zip_file', zipFile);
    formData.append('questions_per_skill', questionsPerSkill);

    try {
      const response = await fetch(`${API_BASE}/analyze-submission`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        },
        body: formData,
      });

      if (!response.ok) {
        const errDetail = await response.json();
        throw new Error(errDetail.detail || 'Failed to analyze project.');
      }

      const data = await response.json();
      setAnalysisData(data);

      // Parse out questions flat list for easy traversal in Viva
      const allQuestions = [];
      data.evaluation_report.skills.forEach(skill => {
        skill.questions.forEach(q => {
          allQuestions.push(q);
        });
      });
      setQuestions(allQuestions);

      // Use the session ID returned by the backend
      setSessionId(data.session_id);

      setView('consent');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 2. Camera Activation and Consent
  const stopCamera = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
      audioAnalyserRef.current = null;
    }
    if (proctorIntervalRef.current) {
      clearInterval(proctorIntervalRef.current);
      proctorIntervalRef.current = null;
    }
  };

  const startCamera = async () => {
    try {
      // Request both video AND audio for microphone monitoring
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      mediaStreamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      return true;
    } catch (err) {
      // Fallback: try video-only if mic permission denied
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        mediaStreamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
        return true;
      } catch (err2) {
        setError('Could not access webcam. Camera permission is required for the proctored viva.');
        return false;
      }
    }
  };

  const handleStartViva = async () => {
    if (!consentAcknowledged) {
      setError('You must acknowledge the consent terms to start.');
      return;
    }

    const cameraOk = await startCamera();
    if (!cameraOk) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/viva-session/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          session_id: sessionId,
          consent_acknowledged: true,
          analysis_data: analysisData
        })
      });

      if (!response.ok) {
        throw new Error('Failed to initiate viva session.');
      }

      // Log success and navigate to active console
      setView('viva');

      // Trigger id_verified automatically for successful webcam boot
      setTimeout(() => {
        postTelemetryEvent('id_verified', 0.0);
      }, 1000);

    } catch (err) {
      stopCamera();
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 3. Telemetry Emitters
  const postTelemetryEvent = async (eventType, durationMs = 0.0, confidence = 1.0) => {
    const timestamp = new Date().toISOString();
    try {
      const response = await fetch(`${API_BASE}/viva-session/event`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          session_id: sessionId,
          event_type: eventType,
          timestamp: timestamp,
          duration_ms: durationMs,
          confidence: confidence
        })
      });
      const data = await response.json();
      // If server returns that new flags were added, update ui notification
      if (data.new_flags > 0) {
        const flagName = eventType.replace(/_/g, ' ');
        setSessionFlags(prev => [...prev, { type: flagName, timestamp: new Date().toLocaleTimeString() }]);
      }
    } catch (err) {
      console.error('Error posting telemetry:', err);
    }
  };

  // Browser behavior listeners
  useEffect(() => {
    if (view !== 'viva') return;

    const handleVisibilityChange = () => {
      if (document.hidden) {
        setIsTabActive(false);
        postTelemetryEvent('tab_switched', 0.0);
      } else {
        setIsTabActive(true);
      }
    };

    const handleFullscreenChange = () => {
      const isFull = !!document.fullscreenElement;
      setIsFullscreen(isFull);
      if (!isFull) {
        postTelemetryEvent('fullscreen_exited', 0.0);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    document.addEventListener('fullscreenchange', handleFullscreenChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, [view]);

  // Wire the camera stream to the <video> element once the viva view renders
  useEffect(() => {
    if (view === 'viva' && videoRef.current && mediaStreamRef.current) {
      videoRef.current.srcObject = mediaStreamRef.current;
    }
  }, [view]);

  // ── Real Face Mesh + Head Pose + Audio Monitoring ────────────────────────
  useEffect(() => {
    if (view !== 'viva') return;

    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;
    const ctx = canvas.getContext('2d');

    // ── Timing state (tracked via closure, not React state) ──
    let headTurnDir = null;
    let headTurnStart = null;
    let faceAbsentStart = null;
    const flagCooldown = {}; // type → last flag timestamp
    const FLAG_CD = 9000; // 9s cooldown between same flag type

    const canFlag = (type) => {
      const now = Date.now();
      if (!flagCooldown[type] || now - flagCooldown[type] > FLAG_CD) {
        flagCooldown[type] = now;
        return true;
      }
      return false;
    };

    // ── Activity monitoring (typing/inactivity detection) ──
    const activityInterval = setInterval(() => {
      const now = Date.now();
      const elapsed = now - lastActivityRef.current;
      if (elapsed > 15000) { // 10s + 5s warning
        if (canFlag('user_inactive')) {
          postTelemetryEvent('user_inactive', elapsed);
        }
        lastActivityRef.current = now; // reset to avoid immediate re-flagging
        setInactivityCountdown(null);
      } else if (elapsed > 10000) {
        setInactivityCountdown(5 - Math.floor((elapsed - 10000) / 1000));
      } else {
        setInactivityCountdown(null);
      }
    }, 500);

    // ── Audio monitoring (speech detection) ──
    let audioInterval = null;
    const stream = mediaStreamRef.current;
    const hasAudio = stream && stream.getAudioTracks().length > 0;

    if (hasAudio) {
      try {
        const audioCtx = new AudioContext();
        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 512;
        analyser.smoothingTimeConstant = 0.6;
        source.connect(analyser);
        audioContextRef.current = audioCtx;
        audioAnalyserRef.current = analyser;

        const timeDomain = new Uint8Array(analyser.fftSize);
        let speakingStart = null;

        audioInterval = setInterval(() => {
          if (!audioAnalyserRef.current) return;
          audioAnalyserRef.current.getByteTimeDomainData(timeDomain);
          // RMS of audio signal
          let sum = 0;
          for (let i = 0; i < timeDomain.length; i++) {
            const v = (timeDomain[i] - 128) / 128;
            sum += v * v;
          }
          const rms = Math.sqrt(sum / timeDomain.length);

          if (rms > 0.06) { // threshold: noticeable voice
            if (!speakingStart) speakingStart = Date.now();
            else if (Date.now() - speakingStart > 1500) {
              // 4000ms cooldown for voice flags specifically to avoid spam
              const now = Date.now();
              if (!flagCooldown['speaking_detected'] || now - flagCooldown['speaking_detected'] > 4000) {
                postTelemetryEvent('speaking_detected', now - speakingStart);
                flagCooldown['speaking_detected'] = now;
              }
              speakingStart = Date.now();
            }
          } else {
            speakingStart = null;
          }
        }, 250);
        proctorIntervalRef.current = audioInterval;
      } catch (e) {
        console.warn('Audio monitoring unavailable:', e);
      }
    }

    // ── MediaPipe Face Mesh ──
    let animFrameId;
    let faceMesh = null;
    let lastSend = 0;
    let multiFaceConsecutiveFrames = 0;

    const initFaceMesh = () => {
      if (!window.FaceMesh) return; // CDN not loaded yet

      faceMesh = new window.FaceMesh({
        locateFile: (file) =>
          `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh@0.4/${file}`,
      });

      faceMesh.setOptions({
        maxNumFaces: 2,
        refineLandmarks: false,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5,
      });

      faceMesh.onResults((results) => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const now = Date.now();
        const faces = results.multiFaceLandmarks || [];
        const numFaces = faces.length;

        // ── Multiple faces ──
        if (numFaces > 1) {
          multiFaceConsecutiveFrames++;
          if (multiFaceConsecutiveFrames > 3 && canFlag('multiple_faces_detected')) {
            postTelemetryEvent('multiple_faces_detected', 0);
          }
        } else {
          multiFaceConsecutiveFrames = 0;
        }
        // ── No face ──
        if (numFaces === 0) {
          if (!faceAbsentStart) faceAbsentStart = now;
          else if (now - faceAbsentStart > 5000 && canFlag('face_not_detected')) {
            postTelemetryEvent('face_not_detected', now - faceAbsentStart);
            faceAbsentStart = now;
          }
          // Red overlay
          ctx.fillStyle = 'rgba(220,38,38,0.18)';
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.fillStyle = '#dc2626';
          ctx.font = 'bold 11px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText('NO FACE DETECTED', canvas.width / 2, canvas.height / 2);
        } else {
          faceAbsentStart = null;
        }

        if (numFaces >= 1) {
          const lms = faces[0];

          // Draw key landmarks
          ctx.fillStyle = 'rgba(0,255,136,0.75)';
          [1, 33, 263, 61, 291, 234, 454, 10, 152, 168].forEach((idx) => {
            const p = lms[idx];
            if (!p) return;
            ctx.beginPath();
            ctx.arc(p.x * canvas.width, p.y * canvas.height, 2.5, 0, 2 * Math.PI);
            ctx.fill();
          });

          // ── Head Pose Estimation ──
          const nose = lms[1];
          const leftCheek = lms[234];
          const rightCheek = lms[454];
          const forehead = lms[10];
          const chin = lms[152];
          const leftEye = lms[33];
          const rightEye = lms[263];

          const faceW = Math.abs(rightCheek.x - leftCheek.x);
          const faceH = Math.abs(chin.y - forehead.y);
          const eyeMidY = (leftEye.y + rightEye.y) / 2;

          const yawRatio = faceW > 0.01 ? (nose.x - leftCheek.x) / faceW : 0.5;
          const pitchRatio = faceH > 0.01 ? (nose.y - eyeMidY) / faceH : 0.3;

          // Thresholds (tune as needed)
          let direction = null;
          if (yawRatio < 0.33) direction = 'RIGHT';
          else if (yawRatio > 0.67) direction = 'LEFT';
          else if (pitchRatio < 0.08) direction = 'UP';
          else if (pitchRatio > 0.42) direction = 'DOWN';

          if (direction) {
            if (headTurnDir !== direction) {
              headTurnDir = direction;
              headTurnStart = now;
            } else {
              const elapsed = now - headTurnStart;
              if (elapsed > 4000 && canFlag('gaze_off_screen')) {
                postTelemetryEvent('gaze_off_screen', elapsed);
                headTurnStart = now;
              }

              // Show countdown bar
              const progress = Math.min(elapsed / 4000, 1);
              ctx.fillStyle = `rgba(220,38,38,${0.25 + progress * 0.5})`;
              ctx.fillRect(0, 0, canvas.width * progress, 4);
              ctx.fillStyle = '#dc2626';
              ctx.font = 'bold 10px sans-serif';
              ctx.textAlign = 'center';
              ctx.fillText(
                `HEAD TURNED ${direction} — ${(elapsed / 1000).toFixed(1)}s`,
                canvas.width / 2, 16
              );
            }
          } else {
            headTurnDir = null;
            headTurnStart = null;
          }
        }
      });
    };

    initFaceMesh();

    // Frame processing loop
    const processFrame = async () => {
      const now = Date.now();
      if (faceMesh && video.readyState >= 2 && now - lastSend > 100) {
        lastSend = now;
        try { await faceMesh.send({ image: video }); } catch (_) {}
      } else if (!faceMesh) {
        // Fallback wireframe while CDN loads
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = 'rgba(66,133,244,0.5)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.ellipse(canvas.width / 2, canvas.height / 2, 70, 95, 0, 0, 2 * Math.PI);
        ctx.stroke();
        ctx.setLineDash([]);
        // retry init
        if (window.FaceMesh) initFaceMesh();
      }
      animFrameId = requestAnimationFrame(processFrame);
    };

    animFrameId = requestAnimationFrame(processFrame);

    return () => {
      cancelAnimationFrame(animFrameId);
      if (audioInterval) clearInterval(audioInterval);
      if (activityInterval) clearInterval(activityInterval);
      if (faceMesh) faceMesh.close().catch(() => {});
    };
  }, [view]); // eslint-disable-line react-hooks/exhaustive-deps

  // Handle paste warning
  const handlePaste = (e) => {
    postTelemetryEvent('paste_attempted', 0.0);
    alert('Warning: Paste operations are monitored during active questioning.');
  };

  // 4. Complete Session and Fetch Report
  const handleEndViva = async () => {
    stopCamera();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/viva-session/end`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          session_id: sessionId,
          questions: questions,
          answers: answers
        })
      });

      if (!response.ok) {
        throw new Error('Failed to end viva session.');
      }

      const data = await response.json();
      setFinalReport(data);
      setView('thankyou');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Reset Application
  const handleReset = () => {
    stopCamera();
    setView('landing');
    setAnalysisData(null);
    setFinalReport(null);
    setAnswers({});
    setCurrentQuestionIndex(0);
    setSessionFlags([]);
    setConsentAcknowledged(false);
  };

  // Exit Viva early
  const handleExitViva = () => {
    setShowExitModal(true);
  };

  const confirmExitViva = async () => {
    setShowExitModal(false);
    await handleEndViva();
  };

  return (
    <div className="container" style={{ minHeight: '90vh', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>

      {/* VIEW -1: AUTH PAGE */}
      {view === 'auth' && <AuthPage onLogin={handleLogin} />}



      {/* Full-screen loading overlay */}
      {loading && (
        <LoadingOverlay
          label={view === 'upload' ? 'Extracting & Analyzing Codebase' : view === 'viva' ? 'Submitting & Grading Viva' : 'Processing'}
          sub="Hang tight — the AI is working on it…"
        />
      )}

      {/* Custom Exit Viva Confirmation Modal */}
      {showExitModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.35)',
          backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 2000, animation: 'fade-in-up 0.25s ease both',
        }}>
          <div style={{
            background: '#FFFEFD', borderRadius: '20px', padding: '2.5rem 2rem',
            maxWidth: '420px', width: '90%', boxShadow: '0 24px 60px rgba(0,0,0,0.18)',
            textAlign: 'center',
          }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'rgba(220,38,38,0.08)', border: '1.5px solid rgba(220,38,38,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.2rem auto', fontSize: '1.4rem' }}>
              ⚠
            </div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '0.6rem' }}>Exit Viva?</h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '2rem' }}>
              Your session will be <strong>terminated immediately</strong> and graded using whatever answers you have submitted so far.
            </p>
            <div style={{ display: 'flex', gap: '0.8rem', justifyContent: 'center' }}>
              <button
                onClick={() => setShowExitModal(false)}
                style={{
                  background: 'none', border: '1.5px solid #000', borderRadius: '50px',
                  padding: '0.55rem 1.5rem', fontWeight: '600', fontSize: '0.9rem',
                  cursor: 'pointer', fontFamily: 'var(--font-sans)', color: 'var(--text-primary)',
                  transition: 'background 0.2s, color 0.2s',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = '#000'; e.currentTarget.style.color = '#fff'; }}
                onMouseLeave={e => { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = 'var(--text-primary)'; }}
              >
                Stay in Viva
              </button>
              <button
                onClick={confirmExitViva}
                style={{
                  background: '#dc2626', border: '1.5px solid #dc2626', borderRadius: '50px',
                  padding: '0.55rem 1.5rem', fontWeight: '600', fontSize: '0.9rem',
                  cursor: 'pointer', fontFamily: 'var(--font-sans)', color: '#fff',
                  transition: 'background 0.2s',
                }}
                onMouseEnter={e => e.currentTarget.style.background = '#b91c1c'}
                onMouseLeave={e => e.currentTarget.style.background = '#dc2626'}
              >
                Yes, Exit Now
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      {view !== 'auth' && (
        <header style={{ textAlign: 'center', marginBottom: '2.5rem', position: 'relative' }}>
          {view !== 'landing' && (
            <button
              onClick={() => setView(userRole === 'mentor' ? 'mentor_dashboard' : 'landing')}
              style={{
                position: 'absolute',
                left: 0,
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: '1.5px solid #000',
                borderRadius: '50px',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: '700',
                color: 'var(--text-primary)',
                padding: '0.45rem 1.1rem',
                fontFamily: 'var(--font-sans)',
                transition: 'background 0.2s ease, color 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
              }}
              onMouseEnter={e => { e.currentTarget.style.background = '#000'; e.currentTarget.style.color = '#fff'; }}
              onMouseLeave={e => { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = 'var(--text-primary)'; }}
            >
              {userRole === 'mentor' ? '← Dashboard' : '← Home'}
            </button>
          )}
          
          <button
            onClick={handleLogout}
            style={{
              position: 'absolute',
              right: 0,
              top: '50%',
              transform: 'translateY(-50%)',
              background: 'none',
              border: '1.5px solid #dc2626',
              borderRadius: '50px',
              cursor: 'pointer',
              fontSize: '0.85rem',
              fontWeight: '700',
              color: '#dc2626',
              padding: '0.45rem 1.1rem',
              fontFamily: 'var(--font-sans)',
              transition: 'background 0.2s ease, color 0.2s ease',
            }}
            onMouseEnter={e => { e.currentTarget.style.background = '#dc2626'; e.currentTarget.style.color = '#fff'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = '#dc2626'; }}
          >
            Logout
          </button>

          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginBottom: '0.5rem' }}>
            <img src="/AIvaluate-removebg-preview.png" alt="AI valuate Logo" style={{ height: '3.5rem' }} />
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', maxWidth: '600px', margin: '0 auto' }}>
            An exclusive AI powered platform for Hackathon Evaluation and Live Proctoring
          </p>
        </header>
      )}

      {/* VIEW: MENTOR DASHBOARD */}
      {view === 'mentor_dashboard' && (
        <MentorDashboard 
          authToken={authToken} 
          onLogout={handleLogout} 
          API_BASE={API_BASE} 
          onViewReport={(data) => {
            setFinalReport(data);
            setView('report');
          }}
        />
      )}

      {/* VIEW 0: LANDING PAGE */}
      {view === 'landing' && (
        <div style={{ textAlign: 'center', maxWidth: '1100px', margin: '0 auto', padding: '4rem 0' }}>
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginBottom: '2rem' }}>
            <img src="/AIvaluate-removebg-preview.png" alt="AI valuate Logo" style={{ height: 'auto', width: '100%', maxWidth: '700px' }} />
          </div>
          <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)', lineHeight: '1.6', maxWidth: '600px', margin: '0 auto 3.5rem auto' }}>
            The next-generation AI-powered platform for automated hackathon evaluation and live, decentralized proctoring.
          </p>

          {/* ─── Scrolly Timeline ─── */}
          <TimelineSection />

          <button
            className="btn btn-primary"
            style={{ fontSize: '1.1rem', padding: '1rem 3rem', borderRadius: '30px', fontWeight: '500' }}
            onClick={() => setView('upload')}
          >
            Enter Grading Console
          </button>
        </div>
      )}

      {error && (
        <div style={{ background: 'rgba(219, 68, 55, 0.1)', border: '1px solid rgba(219, 68, 55, 0.3)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', color: '#db4437', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{error}</span>
          <button className="btn btn-secondary" style={{ padding: '0.3rem 0.8rem', fontSize: '0.8rem' }} onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {/* VIEW 1: UPLOAD & SETUP */}
      {view === 'upload' && (
        <div className="glass-card" style={{ maxWidth: '700px', margin: '0 auto', width: '100%' }}>
          <h2 style={{ fontSize: '1.4rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.8rem', marginBottom: '1.5rem' }}>Submit Codebase for Evaluation</h2>
          <form onSubmit={handleAnalyze} style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>Project Title</label>
                <input
                  type="text"
                  value={projectTitle}
                  onChange={(e) => setProjectTitle(e.target.value)}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>Questions Per Skill</label>
                <select
                  value={questionsPerSkill}
                  onChange={(e) => setQuestionsPerSkill(Number(e.target.value))}
                >
                  <option value={1}>1 Question</option>
                  <option value={2}>2 Questions</option>
                  <option value={3}>3 Questions</option>
                </select>
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>Project Description (Optional)</label>
              <textarea
                rows="2"
                value={projectDescription}
                onChange={(e) => setProjectDescription(e.target.value)}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>Expected Learning Outcomes (One per line)</label>
              <textarea
                rows="3"
                value={projectOutcomes}
                onChange={(e) => setProjectOutcomes(e.target.value)}
                placeholder="1. CRUD operation functionality..."
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>Codebase Archive (ZIP)</label>
              <div
                className="upload-zone"
                onClick={() => document.getElementById('zip-input').click()}
              >
                <span style={{ color: 'var(--text-primary)', fontWeight: '500' }}>
                  {zipFile ? zipFile.name : 'Select or drop project ZIP archive'}
                </span>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '0.5rem 0 0 0' }}>Max uncompressed size: 100MB</p>
                <input
                  id="zip-input"
                  type="file"
                  accept=".zip"
                  style={{ display: 'none' }}
                  onChange={(e) => setZipFile(e.target.files[0])}
                />
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ alignSelf: 'center', marginTop: '1rem', width: '220px', justifyContent: 'center' }}
              disabled={loading}
            >
              {loading ? 'Analyzing Codebase...' : 'Extract & Analyze'}
            </button>
          </form>
        </div>
      )}

      {/* VIEW 2: PRIVACY CONSENT & VERIFICATION */}
      {view === 'consent' && (
        <div className="glass-card" style={{ maxWidth: '750px', margin: '0 auto', width: '100%' }}>
          <h2 style={{ fontSize: '1.4rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.8rem', marginBottom: '1.2rem', color: 'var(--text-primary)' }}>
            Proctoring Rules & Privacy Consent
          </h2>

          <div style={{ background: 'rgba(0,0,0,0.02)', padding: '1.5rem', borderRadius: '8px', marginBottom: '1.5rem', textAlign: 'left', border: '1px solid var(--border-color)' }}>
            <h3 style={{ fontSize: '1.1rem', color: '#db4437', marginBottom: '1rem' }}>Strict Proctoring Regulations</h3>
            <ul style={{ fontSize: '0.9rem', color: 'var(--text-primary)', lineHeight: 1.6, paddingLeft: '1.2rem', marginBottom: '1.5rem' }}>
              <li><strong>Face the Camera:</strong> You must stay within the camera frame at all times. Head movements (looking away for &gt;4s) will be penalized.</li>
              <li><strong>No Background Voices:</strong> The system strictly monitors microphone audio. Speaking or background noise will trigger integrity flags.</li>
              <li><strong>No Multiple Persons:</strong> Only you should be in the camera frame. Multiple faces will instantly flag the session.</li>
              <li><strong>Stay Active:</strong> If you stop typing/interacting for more than 8 seconds, an inactivity warning will appear. Prolonged inactivity is flagged.</li>
              <li><strong>No Tab Switching:</strong> Leaving the active browser tab will automatically pause the session and penalize your integrity score.</li>
              <li><strong>No Copy-Pasting:</strong> Attempting to paste external code or text into the answer box will be flagged immediately.</li>
            </ul>

            <h3 style={{ fontSize: '1rem', color: '#4285f4', marginBottom: '0.5rem' }}>Privacy Notice (Signals, Not Surveillance)</h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
              This system does not record, upload, or transmit any video or audio feed to any server. Face and eye landmark detection happens purely inside your local browser tab. Only lightweight, anonymous, timestamped event telemetry is streamed to calculate integrity indicators.
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
            <label style={{ display: 'flex', gap: '0.8rem', alignItems: 'flex-start', textAlign: 'left', cursor: 'pointer' }}>
              <input
                type="checkbox"
                style={{ marginTop: '0.2rem' }}
                checked={consentAcknowledged}
                onChange={(e) => setConsentAcknowledged(e.target.checked)}
              />
              <span style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                I acknowledge the privacy notice and consent to my local camera stream being analyzed for focus landmark tracking during the session.
              </span>
            </label>
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button className="btn btn-secondary" onClick={handleReset}>Cancel</button>
            <button
              className="btn btn-primary"
              onClick={handleStartViva}
              disabled={loading}
            >
              {loading ? 'Starting Viva...' : 'Start Proctored Session'}
            </button>
          </div>
        </div>
      )}

      {/* VIEW 3: ACTIVE VIVA CONSOLE */}
      {view === 'viva' && (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', width: '100%' }}>

          {/* Question console */}
          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '450px' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.8rem', marginBottom: '1.5rem' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  Question {currentQuestionIndex + 1} of {questions.length}
                </span>
                <span className="badge badge-low" style={{ textTransform: 'uppercase' }}>
                  {questions[currentQuestionIndex]?.type.replace('_', ' ')}
                </span>
              </div>

              <h2 style={{ fontSize: '1.3rem', lineHeight: '1.5', color: 'var(--text-primary)', marginBottom: '1.5rem', fontWeight: '400' }}>
                {questions[currentQuestionIndex]?.text}
              </h2>

              {questions[currentQuestionIndex]?.referenced_file && (
                <div style={{ background: 'rgba(0,0,0,0.03)', padding: '0.6rem 1rem', borderRadius: '6px', fontSize: '0.85rem', fontFamily: 'var(--font-mono)', border: '1px solid var(--border-color)', marginBottom: '1.5rem' }}>
                  <span style={{ color: '#4285f4' }}>Reference File: </span>
                  {questions[currentQuestionIndex].referenced_file}
                </div>
              )}

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>Your Answer</label>
                <textarea
                  rows="5"
                  placeholder="Explain your approach and code structure here..."
                  value={answers[currentQuestionIndex] || ''}
                  onChange={(e) => {
                    setAnswers({ ...answers, [currentQuestionIndex]: e.target.value });
                    lastActivityRef.current = Date.now();
                  }}
                  onPaste={handlePaste}
                />
                {inactivityCountdown !== null && (
                  <div style={{ marginTop: '0.5rem', color: '#db4437', fontSize: '0.85rem', fontWeight: 'bold' }}>
                    ⚠️ Inactivity warning: You will be flagged in {inactivityCountdown} seconds...
                  </div>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-color)', paddingTop: '1.2rem', marginTop: '1rem' }}>
              <button
                className="btn btn-secondary"
                disabled={currentQuestionIndex === 0}
                onClick={() => {
                  setCurrentQuestionIndex(prev => prev - 1);
                  lastActivityRef.current = Date.now();
                  setInactivityCountdown(null);
                }}
              >
                Previous
              </button>

              {currentQuestionIndex < questions.length - 1 ? (
                <button
                  className="btn btn-secondary"
                  disabled={!answers[currentQuestionIndex]}
                  onClick={() => {
                    setCurrentQuestionIndex(prev => prev + 1);
                    lastActivityRef.current = Date.now();
                    setInactivityCountdown(null);
                  }}
                >
                  Next Question
                </button>
              ) : (
                <button
                  className="btn btn-primary"
                  onClick={handleEndViva}
                  disabled={loading}
                >
                  {loading ? 'Submitting...' : 'Finish Viva & Grade'}
                </button>
              )}
            </div>

            {/* Exit Viva early */}
            <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem', marginTop: '0.5rem', textAlign: 'right' }}>
              <button
                onClick={handleExitViva}
                style={{
                  background: 'none',
                  border: '1.5px solid #dc2626',
                  borderRadius: '50px',
                  color: '#dc2626',
                  fontWeight: '600',
                  fontSize: '0.85rem',
                  padding: '0.45rem 1.2rem',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-sans)',
                  transition: 'background 0.2s ease, color 0.2s ease',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = '#dc2626'; e.currentTarget.style.color = '#fff'; }}
                onMouseLeave={e => { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = '#dc2626'; }}
              >
                Exit Viva
              </button>
            </div>
          </div>

          {/* Right sidebar: Web feed & Simulator panel */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

            {/* Camera feed */}
            <div className="glass-card" style={{ padding: '1rem', textAlign: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#0f9d58', display: 'inline-block', boxShadow: '0 0 4px #0f9d58' }} />
                  Camera
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#4285f4', display: 'inline-block', boxShadow: '0 0 4px #4285f4' }} />
                  Mic
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>LIVE</span>
              </div>
              <div className="camera-container">
                <video
                  ref={videoRef}
                  className="camera-feed"
                  autoPlay
                  playsInline
                  muted
                />
                <canvas
                  ref={canvasRef}
                  style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', transform: 'scaleX(-1)' }}
                  width="320"
                  height="180"
                />
                <div className="camera-overlay">
                  <span style={{ color: '#fff', fontSize: '0.7rem', textShadow: '1px 1px 2px #000' }}>MediaPipe Active</span>
                </div>
              </div>
            </div>

            {/* Session flag log */}
            {sessionFlags.length > 0 && (
              <div className="glass-card" style={{ padding: '1rem', maxHeight: '200px', overflowY: 'auto' }}>
                <h4 style={{ fontSize: '0.85rem', color: '#dc2626', marginBottom: '0.5rem' }}>Integrity Flags ({sessionFlags.length})</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {sessionFlags.map((flag, idx) => (
                    <div key={idx} style={{ fontSize: '0.75rem', color: '#dc2626', borderLeft: '2px solid #dc2626', paddingLeft: '0.5rem' }}>
                      <strong>{flag.type}</strong> at {flag.timestamp}
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>

        </div>
      )}

      {/* VIEW: THANK YOU SCREEN */}
      {view === 'thankyou' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', width: '100%', maxWidth: '600px', margin: '4rem auto', textAlign: 'center' }}>
          <div className="glass-card" style={{ padding: '3rem' }}>
            <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🎉</div>
            <h2 style={{ fontSize: '2rem', color: 'var(--text-primary)', marginBottom: '1rem' }}>Thank You for Your Time!</h2>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '2.5rem' }}>
              Your viva has been successfully submitted and analyzed by the AI. The mentor has been notified.
            </p>
            <button
              className="btn btn-primary"
              onClick={() => setView('report')}
            >
              View Evaluation Report
            </button>
          </div>
        </div>
      )}

      {/* VIEW 4: MERGED FINAL REPORT */}
      {view === 'report' && finalReport && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem', width: '100%', maxWidth: '1000px', margin: '0 auto' }}>

          {/* Main overview card */}
          <div className="glass-card" style={{ padding: '2.5rem', position: 'relative' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1.5rem', marginBottom: '1.5rem' }}>
              <div>
                <span style={{ fontSize: '0.85rem', color: '#4285f4', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Final Evaluation Package</span>
                <h2 style={{ fontSize: '1.8rem', margin: '0.2rem 0 0.5rem 0', color: 'var(--text-primary)' }}>{finalReport.project_title}</h2>
              </div>

              <div style={{ display: 'flex', gap: '1.5rem' }}>
                <div style={{ textAlign: 'center' }}>
                  <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Code Alignment</span>
                  <span style={{ fontSize: '1.5rem', fontWeight: '600', color: '#0f9d58' }}>
                    {Math.round(finalReport.evaluation_report.summary.alignment_score * 100)}%
                  </span>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Integrity Score</span>
                  <span style={{ fontSize: '1.5rem', fontWeight: '600', color: finalReport.proctoring_report.risk_level === 'low' ? '#0f9d58' : finalReport.proctoring_report.risk_level === 'medium' ? '#f4b400' : '#db4437' }}>
                    {Math.round(finalReport.proctoring_report.integrity_score * 100)}%
                  </span>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Risk Level</span>
                  <span className={`badge badge-${finalReport.proctoring_report.risk_level}`} style={{ marginTop: '0.3rem' }}>
                    {finalReport.proctoring_report.risk_level.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>

            <div style={{ background: 'rgba(0,0,0,0.01)', padding: '1.2rem', borderRadius: '8px', border: '1px solid var(--border-color)', marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Mentor Summary Narrative</h3>
              <p style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text-primary)', fontStyle: 'italic', lineHeight: '1.5' }}>
                "{finalReport.evaluation_report.summary.narrative}"
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', textAlign: 'left' }}>
              <div>
                <h4 style={{ color: '#0f9d58', fontSize: '0.9rem', marginBottom: '0.6rem' }}>Key Strengths</h4>
                <ul style={{ margin: 0, paddingLeft: '1.2rem', color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6' }}>
                  {finalReport.evaluation_report.summary.strengths.map((str, i) => <li key={i}>{str}</li>)}
                </ul>
              </div>
              <div>
                <h4 style={{ color: '#db4437', fontSize: '0.9rem', marginBottom: '0.6rem' }}>Identified Gaps</h4>
                <ul style={{ margin: 0, paddingLeft: '1.2rem', color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6' }}>
                  {finalReport.evaluation_report.summary.gaps.map((gap, i) => <li key={i}>{gap}</li>)}
                </ul>
              </div>
            </div>
          </div>

          {/* Section 2: Stated Outcomes Evidence Checklist */}
          <div className="glass-card" style={{ padding: '2rem', textAlign: 'left' }}>
            <h3 style={{ fontSize: '1.2rem', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.6rem', marginBottom: '1rem' }}>
              Stated Learning Outcomes Mapping
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {(finalReport.evaluation_report.outcome_evaluation || finalReport.evaluation_report.summary?.outcome_evaluation || []).map((evalItem, index) => (
                <div key={index} style={{ padding: '1rem', background: 'rgba(0,0,0,0.02)', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                    <span style={{ fontWeight: '500', color: 'var(--text-primary)', fontSize: '0.95rem' }}>{evalItem.outcome_text}</span>
                    <span className={`badge badge-${evalItem.status === 'met' ? 'low' : evalItem.status === 'partial' ? 'medium' : 'high'}`}>
                      {evalItem.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>

                  {evalItem.evidence.length > 0 && (
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      <strong>Evidence Cited: </strong>
                      {evalItem.evidence.map((ev, i) => <code key={i} style={{ margin: '0 0.2rem', fontSize: '0.75rem' }}>{ev}</code>)}
                    </div>
                  )}

                  {evalItem.gap && (
                    <div style={{ fontSize: '0.85rem', color: '#db4437', marginTop: '0.4rem' }}>
                      <strong>Gap: </strong> {evalItem.gap}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Section 3: Suggested Skills catalog constraints */}
          <div className="glass-card" style={{ padding: '2rem', textAlign: 'left' }}>
            <h3 style={{ fontSize: '1.2rem', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.6rem', marginBottom: '1rem' }}>
              Catalog Skills suggestion
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              {finalReport.suggested_skills.map((skill, idx) => (
                <div key={idx} style={{ padding: '1rem', background: 'rgba(0,0,0,0.01)', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                    <strong style={{ color: '#4285f4' }}>{skill.skill_name}</strong>
                    <span style={{ color: '#0f9d58', fontSize: '0.85rem' }}>{Math.round(skill.confidence * 100)}% confidence</span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{skill.rationale}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Section 4: Proctoring Summary report */}
          <div className="glass-card" style={{ padding: '2rem', textAlign: 'left' }}>
            <h3 style={{ fontSize: '1.2rem', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.6rem', marginBottom: '1.2rem' }}>
              Webcam Proctoring Integrity Details
            </h3>

            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.2rem' }}>
              <strong>Narrative: </strong> {finalReport.proctoring_report.narrative}
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>

              <div>
                <h4 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.6rem' }}>Flag Metrics Summary</h4>
                <div style={{ background: 'rgba(0,0,0,0.01)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  {Object.entries(finalReport.proctoring_report.flag_summary).map(([key, val]) => (
                    <div key={key} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '0.3rem 0', borderBottom: '1px solid rgba(0,0,0,0.02)' }}>
                      <span style={{ textTransform: 'capitalize', color: 'var(--text-secondary)' }}>{key.replace(/_/g, ' ')}</span>
                      <span style={{ fontWeight: 'bold', color: val > 0 ? '#db4437' : 'var(--text-secondary)' }}>{val}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.6rem' }}>Session Timeline Events ({finalReport.proctoring_report.flags.length})</h4>
                <div style={{ maxHeight: '200px', overflowY: 'auto', background: 'rgba(0,0,0,0.01)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  {finalReport.proctoring_report.flags.length === 0 ? (
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No anomaly flags occurred.</span>
                  ) : (
                    finalReport.proctoring_report.flags.map((flag, i) => (
                      <div key={i} style={{ fontSize: '0.8rem', padding: '0.3rem 0', borderBottom: '1px solid rgba(0,0,0,0.02)' }}>
                        <span className={`badge badge-${flag.severity}`} style={{ padding: '0.1rem 0.4rem', fontSize: '0.7rem', marginRight: '0.4rem' }}>{flag.severity.toUpperCase()}</span>
                        <strong style={{ color: '#db4437' }}>{flag.type.replace(/_/g, ' ')}</strong>
                        {flag.duration_ms > 0 && <span style={{ color: 'var(--text-secondary)' }}> ({Math.round(flag.duration_ms / 1000)}s)</span>}
                      </div>
                    ))
                  )}
                </div>
              </div>

            </div>

          {/* Section 5: Viva Grading */}
          {finalReport.viva_grading && finalReport.viva_grading.graded_answers && finalReport.viva_grading.graded_answers.length > 0 && (
            <div className="glass-card" style={{ padding: '2rem', textAlign: 'left', marginTop: '1.5rem' }}>
              <h3 style={{ fontSize: '1.2rem', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.6rem', marginBottom: '1.2rem', display: 'flex', justifyContent: 'space-between' }}>
                <span>Viva Performance Evaluation</span>
                <span style={{ color: '#4285f4' }}>{Math.round(finalReport.viva_grading.viva_score * 100)}%</span>
              </h3>
              
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', fontStyle: 'italic', marginBottom: '1.5rem' }}>
                "{finalReport.viva_grading.viva_narrative}"
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {finalReport.viva_grading.graded_answers.map((ans, idx) => (
                  <div key={idx} style={{ background: 'rgba(0,0,0,0.02)', padding: '1.2rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
                      <span style={{ fontWeight: '500', fontSize: '0.95rem', color: 'var(--text-primary)' }}>Q: {ans.question}</span>
                      <span className={`badge badge-${ans.score >= 7 ? 'low' : ans.score >= 5 ? 'medium' : 'high'}`}>
                        {ans.score}/{ans.max_score}
                      </span>
                    </div>
                    
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.8rem' }}>
                      <strong>Student Answer:</strong> {ans.student_answer}
                    </div>
                    
                    <div style={{ fontSize: '0.85rem', color: '#0f9d58', marginBottom: '0.8rem' }}>
                      <strong>Feedback:</strong> {ans.feedback}
                    </div>

                    <div style={{ fontSize: '0.85rem', color: '#4285f4', background: 'rgba(66,133,244,0.1)', padding: '0.5rem', borderRadius: '4px' }}>
                      <strong>Expected Concept:</strong> {ans.correct_concept}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Metadata logs */}
            <div style={{ display: 'flex', gap: '1.5rem', color: 'var(--text-muted)', fontSize: '0.8rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
              <span>Files analyzed: <strong>{finalReport.metadata.files_analyzed}</strong></span>
              <span>Extraction time: <strong>{finalReport.metadata.extraction_time_ms}ms</strong></span>
              <span>Model tokens used: <strong>{finalReport.metadata.model_tokens_used}</strong></span>
              <span>Processing time: <strong>{finalReport.processing_time_ms}ms</strong></span>
            </div>

          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '1rem', flexWrap: 'wrap' }}>
            <button className="btn btn-secondary" onClick={() => setShowRawJson(!showRawJson)}>
              {showRawJson ? 'Hide JSON' : 'View Raw JSON'}
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => {
                const blob = new Blob([JSON.stringify(finalReport, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `AIvaluate-report-${finalReport.project_title || 'session'}.json`;
                a.click();
                URL.revokeObjectURL(url);
              }}
            >
              Download JSON Report
            </button>
            <button
              className="btn btn-primary"
              onClick={() => window.print()}
            >
              Download PDF Report
            </button>
          </div>

          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1rem' }}>
            <button className="btn btn-secondary" onClick={handleReset}>Grade Another Project</button>
          </div>

        </div>
      )}

      {/* Footer */}
      <footer style={{ marginTop: '4rem', padding: '1.5rem 0', borderTop: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '0.8rem', textAlign: 'center' }}>
        AIvaluate
      </footer>

    </div>
  );
}
