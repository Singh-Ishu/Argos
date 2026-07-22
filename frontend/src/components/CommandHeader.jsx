import React, { useState, useEffect } from 'react';

function useUtcClock() {
  const [time, setTime] = useState(() => new Date().toUTCString().slice(17, 25));
  useEffect(() => {
    const id = setInterval(() => setTime(new Date().toUTCString().slice(17, 25)), 1000);
    return () => clearInterval(id);
  }, []);
  return time;
}

export default function CommandHeader({ disruption = 72.4, sprCover = 18.2, brentPrice = 103.40, activeFeedsCount = 12 }) {
  const utc = useUtcClock();

  // Color constants (matches index.css design system)
  const C = {
    crimson: '#EF4444',
    crimson10: 'rgba(239, 68, 68, 0.10)',
    crimson30: 'rgba(239, 68, 68, 0.30)',
    amber: '#F59E0B',
    amber10: 'rgba(245, 158, 11, 0.10)',
    amber30: 'rgba(245, 158, 11, 0.30)',
    emerald: '#10B981',
    cyan: '#06B6D4',
    cyan10: 'rgba(6, 182, 212, 0.10)',
    cyan30: 'rgba(6, 182, 212, 0.30)',
    border: '#1E2638',
    muted: '#64748B',
    ink: '#E2E8F0',
    card: '#12161F'
  };

  return (
    <header className="flex-shrink-0" style={{ borderBottom: `1px solid ${C.border}`, background: 'rgba(10,12,16,.97)', zIndex: 50 }}>
      {/* alert banner */}
      <div className="flex items-center gap-2" style={{ background: C.crimson10, borderBottom: `1px solid ${C.crimson30}`, padding: '4px 16px' }}>
        <span className="pulse-crimson flex-shrink-0" style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: C.crimson }} />
        <span className="font-mono uppercase text-xs text-crimson letter-spacing-2">
          ALERT: ENERGY SYSTEM RESILIENCE ACTIVE - CORRIDOR THREAT DETECTED IN SIMULATION
        </span>
        <span className="font-mono text-xs margin-auto" style={{ color: 'rgba(239,68,68,.6)', whiteSpace: 'nowrap' }}>
          UTC {utc}
        </span>
      </div>

      {/* main brand row */}
      <div className="flex items-center gap-3 flex-wrap" style={{ padding: '10px 16px' }}>
        {/* Brand/logo block */}
        <div className="flex items-center gap-3" style={{ marginRight: 'auto' }}>
          <div style={{ position: 'relative', flexShrink: 0 }}>
            <div className="flex items-center justify-center" style={{ width: '32px', height: '32px', border: `1px solid ${C.cyan30}`, borderRadius: '4px', background: C.cyan10 }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={C.cyan} strokeWidth="1.5">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
            <span className="pulse-dot" style={{ position: 'absolute', top: '-4px', right: '-4px', width: '8px', height: '8px', borderRadius: '50%', background: C.emerald }} />
          </div>
          <div>
            <div className="font-mono text-base font-semibold letter-spacing-1 text-ink">
              ARGOS <span className="text-muted">//</span> C4I DEFENSE ENERGY RESILIENCE PLATFORM
            </div>
            <div className="font-mono text-xs letter-spacing-1 text-muted" style={{ marginTop: '2px' }}>
              SYSTEM ONLINE &nbsp;//&nbsp; NODE: INDIA-SOUTH-1 &nbsp;//&nbsp; 12.8310° N, 80.0520° E
            </div>
          </div>
        </div>

        {/* Tactical status pills */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Disruption Index status */}
          <div className="flex items-center gap-3" style={{ border: `1px solid ${C.crimson30}`, borderRadius: '4px', padding: '6px 12px', background: C.crimson10 }}>
            <div>
              <div className="font-mono text-xs text-muted uppercase letter-spacing-1">Global Disruption Index</div>
              <div className="font-mono text-2xl font-bold text-crimson" style={{ lineHeight: 1 }}>
                {disruption.toFixed(1)}
              </div>
            </div>
            <div className="align-right">
              <span className="font-mono uppercase text-xs" style={{
                display: 'inline-flex', alignItems: 'center', gap: '4px',
                padding: '2px 6px', borderRadius: '3px', color: C.crimson,
                background: C.crimson10, border: `1px solid ${C.crimson30}`
              }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: C.crimson }} />
                HIGH RISK
              </span>
              <div style={{ marginTop: '6px', width: '64px', height: '4px', background: C.border, borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ height: '100%', background: C.crimson, borderRadius: '2px', width: `${disruption}%`, transition: 'width .5s' }} />
              </div>
            </div>
          </div>

          {/* SPR Runway */}
          <div style={{ border: `1px solid ${C.amber30}`, borderRadius: '4px', padding: '6px 12px', background: C.amber10 }}>
            <div className="font-mono text-xs text-muted uppercase letter-spacing-1">SPR Cover</div>
            <div className="font-mono text-xl font-bold text-amber" style={{ lineHeight: 1 }}>
              {sprCover.toFixed(1)} <span className="text-xs text-muted">Days</span>
            </div>
          </div>

          {/* Brent Spot */}
          <div style={{ border: `1px solid ${C.border}`, borderRadius: '4px', padding: '6px 12px', background: C.card }}>
            <div className="font-mono text-xs text-muted uppercase letter-spacing-1">Brent Spot</div>
            <div className="font-mono text-xl font-bold text-ink" style={{ lineHeight: 1 }}>
              ${brentPrice.toFixed(2)} <span className="text-xs text-crimson">▲ 14.8%</span>
            </div>
          </div>

          {/* Active Data Feeds */}
          <div className="flex items-center gap-2" style={{ border: `1px solid ${C.cyan30}`, borderRadius: '4px', padding: '6px 12px', background: C.cyan10 }}>
            <span className="pulse-dot" style={{ width: '6px', height: '6px', borderRadius: '50%', background: C.cyan }} />
            <div>
              <div className="font-mono text-xs text-muted uppercase letter-spacing-1">Active Data Feeds</div>
              <div className="font-mono text-lg font-bold text-cyan" style={{ lineHeight: 1 }}>
                {activeFeedsCount} <span className="text-xs text-muted">LIVE</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
