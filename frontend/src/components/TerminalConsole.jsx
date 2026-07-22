import React, { useState, useEffect, useRef } from 'react';

const C = {
  border: '#1E2638',
  muted: '#64748B',
  cyan: '#06B6D4',
  emerald: '#10B981',
  amber: '#F59E0B',
  crimson: '#EF4444',
  ink: '#E2E8F0',
  card: '#12161F'
};

const levelColor = {
  INFO: C.cyan,
  SUCCESS: C.emerald,
  WARN: C.amber,
  ERROR: C.crimson
};

export default function TerminalConsole({ logs = [] }) {
  const [open, setOpen] = useState(true);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (open && bottomRef.current) {
      const parent = bottomRef.current.parentElement;
      if (parent) parent.scrollTop = parent.scrollHeight;
    }
  }, [logs, open]);

  return (
    <div className="flex-shrink-0" style={{ background: C.card, borderTop: `1px solid ${C.border}` }}>
      {/* Console Header / Toggle */}
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 w-full"
        style={{
          padding: '6px 16px', background: 'none', border: 'none', cursor: 'pointer',
        }}
      >
        <span className="font-mono text-xs uppercase letter-spacing-2 text-muted">
          {open ? '▼' : '▶'} Agent System Execution Stream
        </span>
        <span className="pulse-dot" style={{ display: 'inline-block', width: '5px', height: '5px', borderRadius: '50%', background: C.emerald }} />
        <span className="font-mono text-xs text-muted margin-auto">
          {open ? '▲ COLLAPSE' : '▼ EXPAND'}
        </span>
      </button>

      {/* Scrolling Console log lines */}
      {open && (
        <div
          style={{ height: '100px', overflowY: 'auto', padding: '4px 16px 8px', background: 'rgba(0,0,0,.3)' }}
          role="log"
          aria-live="polite"
          aria-label="Agent system execution stream"
        >
          {logs.length === 0 ? (
            <div className="font-mono text-sm text-muted" style={{ lineHeight: 1.7, padding: '8px 0', opacity: 0.5 }}>
              -- NO LOG ENTRIES --
            </div>
          ) : (
            logs.map((l, i) => (
              <div
                key={i}
                className="log-anim font-mono text-sm"
                style={{ lineHeight: 1.7, color: C.muted, display: 'flex', gap: '10px' }}
              >
                <span style={{ color: 'rgba(100,116,139,.5)' }}>[{l.ts}]</span>
                <span style={{ color: levelColor[l.level] || C.muted, minWidth: '50px', display: 'inline-block' }}>
                  {l.level}
                </span>
                <span style={{ color: l.level === 'WARN' ? C.amber : l.level === 'ERROR' ? C.crimson : C.ink }}>
                  {l.msg}
                </span>
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
