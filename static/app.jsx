// Recap — Bold Editorial UI
// Ported from the design bundle (direction-editorial.jsx) and wired to the
// real FastAPI backend at /api/patients and /api/answer. Single-instance
// app (no canvas), full-window, light + dark.

const { useState, useEffect, useMemo, useRef } = React;

const PALETTE = {
  light: {
    bg: '#f4ede2', paper: '#fbf7ef',
    ink: '#1a1410', inkSoft: '#3a2e25',
    muted: '#6b5c4a', faint: '#a8967f',
    rule: '#d6c8b4', ruleSoft: '#e8ddc9',
    accent: '#b8412e', accentSoft: '#f3dcd0',
    mark: '#d4af37',
  },
  dark: {
    bg: '#1a1410', paper: '#221a14',
    ink: '#f4ede2', inkSoft: '#d6c8b4',
    muted: '#a8967f', faint: '#6b5c4a',
    rule: '#3a2e25', ruleSoft: '#2a2017',
    accent: '#e8755e', accentSoft: '#2a1814',
    mark: '#e0c060',
  },
};

const CAT = {
  diagnosis: { glyph: '※' },
  visit:     { glyph: '◇' },
  lab:       { glyph: '▲' },
  report:    { glyph: '▭' },
  scan:      { glyph: '◐' },
  procedure: { glyph: '✦' },
  med:       { glyph: '℞' },
  note:      { glyph: '—' },
  photo:     { glyph: '◧' },
  other:     { glyph: '·' },
};

const SERIF = '"Source Serif 4", "GT Sectra", "Tiempos Headline", Charter, Georgia, serif';
const SANS  = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif';
const MONO  = '"JetBrains Mono", "SF Mono", ui-monospace, monospace';

function fmtDate(iso, opts = { y: true }) {
  const d = new Date(iso + (iso.length === 10 ? 'T00:00:00Z' : ''));
  if (opts.short) return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  return d.toLocaleDateString('en-US', {
    year: opts.y ? 'numeric' : undefined,
    month: 'short',
    day: 'numeric',
  });
}

// ─────────────────────────────────────────────────────────────────────
// Suggested questions per patient. Used as starter prompts only —
// actual answers come from /api/answer (real LLM via inference gateway).
const SUGGESTED = {
  sarah: [
    'When did her kidney function start declining?',
    'What medications was she on when CKD was diagnosed?',
    'Summarize her trajectory in 3 sentences.',
  ],
  marcus: [
    'How long from first symptom to diagnosis?',
    'What was the response to R-CHOP?',
    'Summarize this patient\'s journey.',
  ],
  aisha: [
    'What records does she have in foreign languages?',
    'Is her current anemia recurrent or new?',
    'What is her current pregnancy status?',
  ],
  demo: [
    'When did her kidney function start declining?',
    'What was her first abnormal creatinine reading?',
    'What medications was she on when CKD was diagnosed?',
  ],
};

// ─────────────────────────────────────────────────────────────────────
function App() {
  const [patients, setPatients] = useState([]);
  const [patientId, setPatientId] = useState(null);
  const [dark, setDark] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/patients')
      .then((r) => r.json())
      .then((data) => {
        setPatients(data);
        if (data.length > 0) setPatientId(data[0].id);
        setLoading(false);
      })
      .catch((e) => {
        setError(String(e));
        setLoading(false);
      });
  }, []);

  const c = dark ? PALETTE.dark : PALETTE.light;
  const patient = useMemo(
    () => patients.find((p) => p.id === patientId),
    [patients, patientId],
  );

  if (loading) {
    return <Loading c={c} />;
  }
  if (error) {
    return <ErrorView c={c} message={error} />;
  }
  if (!patient) {
    return <ErrorView c={c} message="No patients available." />;
  }

  return (
    <div style={{
      position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
      background: c.bg, color: c.ink, fontFamily: SANS, fontSize: 13,
    }}>
      <Masthead c={c} dark={dark} patient={patient} allPatients={patients}
                onPatientChange={setPatientId}
                onDarkToggle={() => setDark(!dark)} />
      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <Document c={c} patient={patient} />
        <ChatColumn c={c} patient={patient} />
      </div>
    </div>
  );
}

function Loading({ c }) {
  return (
    <div style={{
      position: 'absolute', inset: 0, background: c.bg, color: c.muted,
      display: 'grid', placeItems: 'center', fontFamily: SERIF,
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: 42, color: c.ink, letterSpacing: '-.03em' }}>
          Recap<span style={{ color: c.accent }}>.</span>
        </div>
        <div style={{ fontStyle: 'italic', marginTop: 8 }}>loading the chart…</div>
      </div>
    </div>
  );
}

function ErrorView({ c, message }) {
  return (
    <div style={{
      position: 'absolute', inset: 0, background: c.bg, color: c.ink,
      display: 'grid', placeItems: 'center', fontFamily: SERIF, padding: 24,
    }}>
      <div style={{ textAlign: 'center', maxWidth: 480 }}>
        <div style={{ fontSize: 32, color: c.accent, letterSpacing: '-.02em' }}>
          Something is off.
        </div>
        <div style={{ marginTop: 12, color: c.muted, fontStyle: 'italic' }}>{message}</div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
function Masthead({ c, dark, patient, allPatients, onPatientChange, onDarkToggle }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{
      padding: '14px 28px', borderBottom: `1px solid ${c.rule}`,
      background: c.bg, display: 'flex', alignItems: 'center', gap: 18,
    }}>
      <div style={{
        fontFamily: SERIF, fontSize: 26, fontWeight: 500,
        letterSpacing: '-0.025em', lineHeight: 1, color: c.ink,
      }}>
        Recap<span style={{ color: c.accent }}>.</span>
      </div>
      <div style={{
        paddingLeft: 16, borderLeft: `1px solid ${c.rule}`,
        fontFamily: SERIF, fontStyle: 'italic', fontSize: 13.5, color: c.muted,
        lineHeight: 1.3, maxWidth: 280,
      }}>
        Reads the whole chart so you don't have to.
      </div>
      <div style={{ flex: 1 }} />
      <div style={{ position: 'relative' }}>
        <button onClick={() => setOpen(!open)} style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '6px 12px', border: `1px solid ${c.rule}`, borderRadius: 2,
          background: c.paper, color: c.ink, cursor: 'pointer',
          fontFamily: SANS, fontSize: 12,
        }}>
          <span style={{ fontFamily: MONO, fontSize: 10, color: c.faint, letterSpacing: '0.06em' }}>
            CASE №
          </span>
          <span style={{ fontFamily: SERIF, fontSize: 14, fontWeight: 500, color: c.ink }}>
            {patient.display_name}
          </span>
          <span style={{ color: c.faint }}>▾</span>
        </button>
        {open && (
          <div style={{
            position: 'absolute', top: '110%', right: 0, width: 320, marginTop: 4,
            background: c.paper, border: `1px solid ${c.rule}`, borderRadius: 2,
            padding: 4, zIndex: 10,
            boxShadow: dark ? '0 8px 32px rgba(0,0,0,.5)' : '0 8px 32px rgba(0,0,0,.12)',
          }}>
            {allPatients.map((p, i) => (
              <button key={p.id}
                      onClick={() => { onPatientChange(p.id); setOpen(false); }}
                      style={{
                        width: '100%', textAlign: 'left', padding: '10px 12px',
                        borderRadius: 2, border: 'none', cursor: 'pointer',
                        background: p.id === patient.id ? c.accentSoft : 'transparent',
                        color: c.ink, fontFamily: 'inherit',
                      }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                  <span style={{
                    fontFamily: MONO, fontSize: 10, color: c.faint, letterSpacing: '0.06em',
                  }}>{String(i + 1).padStart(2, '0')}</span>
                  <span style={{ fontFamily: SERIF, fontSize: 16, fontWeight: 500 }}>
                    {p.display_name}
                  </span>
                  {p.age != null && (
                    <span style={{ fontSize: 11, color: c.muted }}>· {p.age}y</span>
                  )}
                </div>
                <div style={{
                  fontSize: 11.5, color: c.muted, marginTop: 4, lineHeight: 1.45,
                  fontStyle: 'italic', fontFamily: SERIF,
                }}>
                  {p.summary}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
      <BackendBadge c={c} />
      <button onClick={onDarkToggle} style={{
        width: 28, height: 28, borderRadius: 2,
        border: `1px solid ${c.rule}`, background: c.paper,
        color: c.muted, cursor: 'pointer', fontSize: 14,
      }}>{dark ? '☀' : '☾'}</button>
    </div>
  );
}

function BackendBadge({ c }) {
  const [info, setInfo] = useState({ backend: '...' });
  useEffect(() => {
    fetch('/api/health').then((r) => r.json()).then(setInfo).catch(() => {});
  }, []);
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      padding: '4px 10px', border: `1px solid ${c.rule}`, borderRadius: 2,
      background: c.paper,
      fontFamily: MONO, fontSize: 10, color: c.muted, letterSpacing: '0.04em',
    }}>
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: c.accent }} />
      AMD MI300X · 192 GB · {info.backend}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
function Document({ c, patient }) {
  const events = patient.events;
  const groups = {};
  events.forEach((e) => {
    const y = e.date.slice(0, 4);
    (groups[y] = groups[y] || []).push(e);
  });
  const years = Object.keys(groups).sort();

  return (
    <div style={{
      flex: 1.4, minWidth: 0, overflowY: 'auto',
      background: c.paper, borderRight: `1px solid ${c.rule}`,
    }}>
      <div style={{ padding: '32px 36px 24px', borderBottom: `1px solid ${c.rule}` }}>
        <div style={{
          fontFamily: MONO, fontSize: 10, color: c.faint, letterSpacing: '0.12em',
          textTransform: 'uppercase', marginBottom: 12,
        }}>
          Patient Dossier · {events.length} events · {years.length} year{years.length === 1 ? '' : 's'} on record
        </div>
        <h1 style={{
          fontFamily: SERIF, fontSize: 48, fontWeight: 500,
          letterSpacing: '-0.03em', lineHeight: 1.05, color: c.ink,
          margin: '0 0 12px',
        }}>
          {patient.display_name}<span style={{ color: c.accent }}>.</span>
        </h1>
        <div style={{
          fontFamily: SERIF, fontStyle: 'italic', fontSize: 18, color: c.muted,
          lineHeight: 1.45, maxWidth: 620, textWrap: 'pretty',
        }}>
          {patient.summary}
        </div>
        <div style={{ display: 'flex', gap: 24, marginTop: 22, alignItems: 'baseline' }}>
          {patient.age != null && <Stat c={c} value={patient.age} label="years old" />}
          {patient.gender && <Stat c={c} value={patient.gender} label="gender" />}
          {patient.mrn && <Stat c={c} value={patient.mrn} label="MRN" mono />}
          <Stat c={c} value={new Set(events.map((e) => e.source)).size} label="source docs" />
        </div>
        {patient.tags && patient.tags.length > 0 && (
          <div style={{ display: 'flex', gap: 8, marginTop: 20, flexWrap: 'wrap' }}>
            {patient.tags.map((t) => (
              <span key={t} style={{
                fontFamily: SANS, fontSize: 11, color: c.inkSoft,
                padding: '3px 10px', border: `1px solid ${c.rule}`, borderRadius: 2,
                background: c.bg,
              }}>{t}</span>
            ))}
          </div>
        )}
      </div>

      <div style={{ padding: '24px 36px 48px' }}>
        {years.map((y, yi) => (
          <YearSection key={y} c={c} year={y} events={groups[y]} first={yi === 0} />
        ))}
      </div>
    </div>
  );
}

function Stat({ c, value, label, mono }) {
  return (
    <div>
      <div style={{
        fontFamily: mono ? MONO : SERIF,
        fontSize: mono ? 14 : 22, fontWeight: 500, color: c.ink, lineHeight: 1,
      }}>{value}</div>
      <div style={{
        fontFamily: MONO, fontSize: 9.5, color: c.faint, letterSpacing: '0.1em',
        textTransform: 'uppercase', marginTop: 5,
      }}>{label}</div>
    </div>
  );
}

function YearSection({ c, year, events, first }) {
  const [activeId, setActiveId] = useState(null);
  return (
    <div style={{ position: 'relative', marginBottom: 32 }}>
      <div style={{
        display: 'flex', alignItems: 'baseline', gap: 14,
        marginBottom: 8, paddingBottom: 8,
        borderBottom: `1px solid ${c.ruleSoft}`, marginLeft: 80,
      }}>
        <h2 style={{
          fontFamily: SERIF, fontSize: 32, fontWeight: 500, letterSpacing: '-0.02em',
          color: c.ink, margin: 0, lineHeight: 1,
        }}>{year}</h2>
        <div style={{
          fontFamily: MONO, fontSize: 10, color: c.faint, letterSpacing: '0.1em',
          textTransform: 'uppercase',
        }}>
          {events.length} {events.length === 1 ? 'event' : 'events'}
        </div>
      </div>

      <div style={{
        position: 'absolute', left: 84, top: 56, bottom: 0,
        width: 1, background: c.rule,
      }} />

      {events.map((e, ei) => (
        <DocEvent key={e.id} c={c} e={e} index={ei}
                  active={activeId === e.id}
                  onClick={() => setActiveId(activeId === e.id ? null : e.id)} />
      ))}
    </div>
  );
}

function DocEvent({ c, e, index, active, onClick }) {
  const cat = CAT[e.category] || CAT.other;
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start',
      padding: '12px 0', position: 'relative',
    }}>
      <div style={{
        width: 76, flexShrink: 0, paddingRight: 8, paddingTop: 2, textAlign: 'right',
      }}>
        <div style={{
          fontFamily: SERIF, fontSize: 14, color: c.ink, fontWeight: 500,
          letterSpacing: '-0.01em',
        }}>
          {fmtDate(e.date, { y: false, short: true })}
        </div>
        <div style={{
          fontFamily: MONO, fontSize: 9.5, color: c.faint, letterSpacing: '0.06em',
          marginTop: 2,
        }}>
          {String(index + 1).padStart(2, '0')}
        </div>
      </div>

      <div style={{
        width: 16, flexShrink: 0, display: 'flex', justifyContent: 'center',
        paddingTop: 4, position: 'relative', zIndex: 1,
      }}>
        <div style={{
          width: active ? 22 : 14, height: active ? 22 : 14,
          borderRadius: e.category === 'diagnosis' ? 2 : '50%',
          background: active ? c.accent : c.paper,
          border: `1px solid ${active ? c.accent : c.rule}`,
          display: 'grid', placeItems: 'center',
          color: active ? c.paper : c.muted, fontSize: 9, fontFamily: SANS,
          transition: 'all .2s',
        }}>{cat.glyph}</div>
      </div>

      <button onClick={onClick} style={{
        flex: 1, marginLeft: 18, textAlign: 'left',
        background: active ? c.accentSoft : 'transparent',
        padding: active ? '10px 14px' : '0',
        marginTop: active ? -4 : 0, marginBottom: active ? -4 : 0,
        border: 'none', cursor: 'pointer', color: c.ink, fontFamily: 'inherit',
        borderRadius: 2,
      }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' }}>
          <span style={{
            fontFamily: MONO, fontSize: 9.5, color: c.faint,
            textTransform: 'uppercase', letterSpacing: '0.1em',
          }}>{e.category}</span>
          {e.flag === 'critical' && (
            <span style={{
              fontFamily: MONO, fontSize: 9.5, color: c.accent,
              textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600,
            }}>· Critical</span>
          )}
          {(e.flag === 'high' || e.flag === 'low') && (
            <span style={{
              fontFamily: MONO, fontSize: 9.5, color: c.mark,
              textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600,
            }}>· {e.flag === 'high' ? 'High' : 'Low'}</span>
          )}
        </div>
        <div style={{
          fontFamily: SERIF, fontSize: 17, fontWeight: 500, color: c.ink,
          letterSpacing: '-0.012em', lineHeight: 1.3, marginTop: 3, textWrap: 'balance',
        }}>{e.title}</div>
        {e.body && e.body !== e.title && (active || e.flag === 'critical') && (
          <div style={{
            fontFamily: SERIF, fontSize: 14, color: c.inkSoft, lineHeight: 1.5,
            marginTop: 6, fontStyle: 'italic', maxWidth: 540, textWrap: 'pretty',
          }}>{e.body}</div>
        )}
        {active && (
          <div style={{
            marginTop: 10, paddingTop: 8, borderTop: `1px solid ${c.rule}`,
            fontFamily: MONO, fontSize: 10.5, color: c.muted,
            display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
          }}>
            <span>Source: <span style={{ color: c.ink }}>{e.source}</span></span>
            {e.page && <span>Page {e.page}</span>}
            {e.snippet && (
              <span style={{
                fontStyle: 'italic', fontFamily: SERIF, fontSize: 12.5, color: c.inkSoft,
              }}>"{e.snippet}"</span>
            )}
          </div>
        )}
      </button>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
function ChatColumn({ c, patient }) {
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState('');
  const [thinking, setThinking] = useState(false);
  const scroller = useRef(null);

  useEffect(() => {
    setHistory([]);
    setInput('');
  }, [patient.id]);

  useEffect(() => {
    if (scroller.current) scroller.current.scrollTop = scroller.current.scrollHeight;
  }, [history, thinking]);

  const send = async (text) => {
    const q = (text || input).trim();
    if (!q) return;
    setInput('');
    setHistory((h) => [...h, { role: 'user', text: q }]);
    setThinking(true);
    try {
      const r = await fetch('/api/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: patient.id, question: q }),
      });
      const data = await r.json();
      if (data.error) {
        setHistory((h) => [...h, { role: 'assistant', text: `Error: ${data.error}`, citations: [] }]);
      } else {
        setHistory((h) => [...h, {
          role: 'assistant',
          text: data.text,
          citations: data.citations || [],
        }]);
      }
    } catch (err) {
      setHistory((h) => [...h, {
        role: 'assistant',
        text: `Network error: ${String(err)}`,
        citations: [],
      }]);
    } finally {
      setThinking(false);
    }
  };

  const examples = SUGGESTED[patient.id] || SUGGESTED.demo || [];

  return (
    <div style={{
      flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', background: c.bg,
    }}>
      <div style={{ padding: '20px 24px 14px', borderBottom: `1px solid ${c.rule}` }}>
        <div style={{
          fontFamily: MONO, fontSize: 10, color: c.faint, letterSpacing: '0.12em',
          textTransform: 'uppercase', marginBottom: 6,
        }}>
          The Reading Room
        </div>
        <div style={{
          fontFamily: SERIF, fontSize: 22, fontWeight: 500,
          letterSpacing: '-0.02em', color: c.ink, lineHeight: 1.15,
        }}>
          Ask a question.<br />
          <span style={{ fontStyle: 'italic', color: c.muted }}>Get a cited answer.</span>
        </div>
      </div>

      <div ref={scroller} style={{ flex: 1, overflowY: 'auto', padding: '18px 24px' }}>
        {history.length === 0 && (
          <div>
            <div style={{
              fontFamily: MONO, fontSize: 10, color: c.faint, letterSpacing: '0.1em',
              textTransform: 'uppercase', marginBottom: 12,
            }}>Suggested</div>
            {examples.map((ex, i) => (
              <button key={ex} onClick={() => send(ex)} style={{
                display: 'flex', gap: 12, alignItems: 'flex-start',
                width: '100%', textAlign: 'left',
                padding: '14px 0',
                borderTop: i === 0 ? `1px solid ${c.rule}` : 'none',
                borderBottom: `1px solid ${c.rule}`,
                background: 'transparent', border: 'none', cursor: 'pointer',
                borderRadius: 0, color: c.ink, fontFamily: 'inherit',
              }}>
                <span style={{
                  fontFamily: MONO, fontSize: 10, color: c.faint, letterSpacing: '0.1em',
                  width: 22, paddingTop: 4, flexShrink: 0,
                }}>0{i + 1}</span>
                <span style={{
                  flex: 1, fontFamily: SERIF, fontSize: 16, lineHeight: 1.4,
                  color: c.ink, fontWeight: 500, letterSpacing: '-0.01em',
                }}>{ex}</span>
                <span style={{ color: c.accent, fontSize: 16, marginTop: 1 }}>→</span>
              </button>
            ))}
          </div>
        )}

        {history.map((m, i) => (
          <div key={i} style={{ marginBottom: 22 }}>
            {m.role === 'user' ? (
              <div>
                <div style={{
                  fontFamily: MONO, fontSize: 9.5, color: c.faint, letterSpacing: '0.1em',
                  textTransform: 'uppercase', marginBottom: 6,
                }}>You asked</div>
                <div style={{
                  fontFamily: SERIF, fontSize: 19, lineHeight: 1.35, color: c.ink,
                  fontWeight: 500, letterSpacing: '-0.015em',
                }}>"{m.text}"</div>
              </div>
            ) : (
              <AssistantMessage c={c} m={m} patient={patient} />
            )}
          </div>
        ))}

        {thinking && (
          <div style={{
            fontFamily: MONO, fontSize: 11, color: c.muted, letterSpacing: '0.04em',
            padding: '8px 0',
          }}>
            <span style={{ animation: 'edit-blink 1s infinite' }}>▌</span>
            {' '}reading {patient.events.length} events…
          </div>
        )}
      </div>

      <div style={{ padding: '14px 24px 18px', borderTop: `1px solid ${c.rule}` }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10,
          border: `1px solid ${c.rule}`, borderRadius: 2,
          background: c.paper, padding: '10px 14px',
        }}>
          <span style={{
            fontFamily: SERIF, color: c.accent, fontSize: 18, fontStyle: 'italic',
          }}>?</span>
          <input value={input} onChange={(e) => setInput(e.target.value)}
                 onKeyDown={(e) => e.key === 'Enter' && send()}
                 placeholder="Ask anything about this chart…"
                 style={{
                   flex: 1, border: 'none', background: 'transparent',
                   color: c.ink, fontSize: 14, outline: 'none',
                   fontFamily: SERIF, padding: '2px 0',
                 }} />
          <button onClick={() => send()} style={{
            padding: '6px 14px', borderRadius: 2,
            background: c.accent, border: 'none', color: c.paper,
            cursor: 'pointer', fontSize: 12, fontWeight: 500,
            fontFamily: SANS, letterSpacing: '0.02em',
          }}>Ask →</button>
        </div>
      </div>
    </div>
  );
}

// Render markdown-ish bold + inline citation markers like [src:foo.pdf#p2].
function AssistantMessage({ c, m, patient }) {
  // Replace [src:foo.pdf#p2] with superscript clickable cite numbers.
  const citationsByKey = {};
  let counter = 0;
  const text = (m.text || '').replace(/\[src:([^\]#]+)(?:#p(\d+))?\]/g, (_match, src, page) => {
    const key = `${src}|${page || ''}`;
    if (!(key in citationsByKey)) {
      counter += 1;
      citationsByKey[key] = { n: counter, src, page: page ? parseInt(page, 10) : null };
    }
    return `‹CITE:${citationsByKey[key].n}›`;
  });

  // Now split on the placeholders + bold markdown.
  const segments = text.split(/(‹CITE:\d+›|\*\*[^*]+\*\*)/g);
  return (
    <div>
      <div style={{
        fontFamily: MONO, fontSize: 9.5, color: c.faint, letterSpacing: '0.1em',
        textTransform: 'uppercase', marginBottom: 8,
      }}>The chart says</div>
      <div style={{
        fontFamily: SERIF, fontSize: 16.5, lineHeight: 1.55, color: c.ink,
        letterSpacing: '-0.005em', textWrap: 'pretty',
      }}>
        {segments.map((seg, i) => {
          if (seg.startsWith('‹CITE:')) {
            const n = parseInt(seg.slice(6, -1), 10);
            return (
              <sup key={i} style={{
                color: c.accent, fontFamily: SERIF, fontStyle: 'italic',
                fontWeight: 700, fontSize: 11, padding: '0 2px',
              }}>{n}</sup>
            );
          }
          if (seg.startsWith('**') && seg.endsWith('**')) {
            return <strong key={i} style={{ fontWeight: 600 }}>{seg.slice(2, -2)}</strong>;
          }
          return <React.Fragment key={i}>{seg}</React.Fragment>;
        })}
      </div>

      {(m.citations && m.citations.length > 0) && (
        <div style={{ marginTop: 16, paddingTop: 12, borderTop: `1px solid ${c.rule}` }}>
          <div style={{
            fontFamily: MONO, fontSize: 9.5, color: c.faint, letterSpacing: '0.1em',
            textTransform: 'uppercase', marginBottom: 8,
          }}>Drawn from</div>
          {m.citations.map((cit, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'baseline', gap: 12, padding: '6px 0',
            }}>
              <span style={{
                fontFamily: SERIF, fontStyle: 'italic', color: c.accent,
                fontSize: 14, width: 18, flexShrink: 0,
              }}>{i + 1}.</span>
              <span style={{ flex: 1, fontSize: 12.5, lineHeight: 1.45 }}>
                {cit.snippet && (
                  <span style={{ fontFamily: SERIF, color: c.ink, fontWeight: 500 }}>
                    {cit.snippet}
                  </span>
                )}
                {cit.snippet && <span style={{ color: c.muted }}> · </span>}
                <span style={{ fontFamily: MONO, fontSize: 10.5, color: c.muted }}>
                  {cit.source_id}{cit.page ? ` p.${cit.page}` : ''}
                </span>
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Blinking cursor keyframes
if (!document.getElementById('edit-keyframes')) {
  const s = document.createElement('style');
  s.id = 'edit-keyframes';
  s.textContent = `@keyframes edit-blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }`;
  document.head.appendChild(s);
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
