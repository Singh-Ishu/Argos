import React from 'react';

// Status badge component and style mapper
const C = {
  bg: '#0A0C10',
  card: '#12161F',
  border: '#1E2638',
  ink: '#E2E8F0',
  muted: '#64748B',
  emerald: '#10B981',
  amber: '#F59E0B',
  crimson: '#EF4444',
  cyan: '#06B6D4',
  
  crimson10: 'rgba(239, 68, 68, 0.10)',
  crimson30: 'rgba(239, 68, 68, 0.30)',
  amber10: 'rgba(245, 158, 11, 0.10)',
  amber30: 'rgba(245, 158, 11, 0.30)',
  emerald10: 'rgba(16, 185, 129, 0.10)',
  emerald30: 'rgba(16, 185, 129, 0.30)',
  cyan10: 'rgba(6, 182, 212, 0.10)',
  cyan30: 'rgba(6, 182, 212, 0.30)',
  muted10: 'rgba(100, 116, 139, 0.10)',
  muted30: 'rgba(100, 116, 139, 0.30)'
};

function statusStyle(s) {
  const norm = s ? s.toUpperCase() : 'NOMINAL';
  if (norm === 'CRITICAL' || norm === 'BLOCKED' || norm === 'HIGH RISK') {
    return { color: C.crimson, bg: C.crimson10, border: C.crimson30, dot: C.crimson };
  }
  if (norm === 'HIGH' || norm === 'ELEVATED' || norm === 'MONITOR' || norm === 'AMBER') {
    return { color: C.amber, bg: C.amber10, border: C.amber30, dot: C.amber };
  }
  if (norm === 'NOMINAL' || norm === 'OPTIMAL' || norm === 'OK') {
    return { color: C.emerald, bg: C.emerald10, border: C.emerald30, dot: C.emerald };
  }
  if (norm === 'FEASIBLE') {
    return { color: C.cyan, bg: C.cyan10, border: C.cyan30, dot: C.cyan };
  }
  return { color: C.muted, bg: C.muted10, border: C.muted30, dot: C.muted };
}

function StatusBadge({ status, small }) {
  const ss = statusStyle(status);
  const sz = small ? '9px' : '10px';
  const px = small ? '6px' : '8px';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '4px',
      fontFamily: 'ui-monospace,monospace', fontSize: sz, letterSpacing: '.12em',
      padding: `2px ${px}`, borderRadius: '3px',
      color: ss.color, background: ss.bg, border: `1px solid ${ss.border}`,
    }}>
      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: ss.dot, flexShrink: 0 }} />
      {status}
    </span>
  );
}

export default function ThreatFeed({ corridorRisks = [], onRefresh, refreshing }) {
  return (
    <div className="panel" style={{ flex: 1 }}>
      <div className="panel-hd">
        <span>Active Corridor Threat Feed</span>
        <button
          onClick={onRefresh}
          disabled={refreshing}
          className="flex items-center gap-1"
          style={{
            fontFamily: 'ui-monospace,monospace', fontSize: '9px', letterSpacing: '.08em',
            padding: '2px 6px', borderRadius: '3px', cursor: 'pointer', border: `1px solid ${C.border}`,
            background: refreshing ? 'rgba(6,182,212,.05)' : 'transparent',
            color: refreshing ? C.muted : C.cyan,
          }}
        >
          {refreshing ? (
            <>
              <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="spin-anim" style={{ flexShrink: 0 }}>
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
              REFRESHING...
            </>
          ) : (
            'REFRESH'
          )}
        </button>
      </div>
      <div className="panel-body flex flex-col gap-2">
        {corridorRisks.length === 0 ? (
          <div className="font-mono text-xs text-muted" style={{ padding: '8px 0', opacity: 0.5, textAlign: 'center' }}>
            -- NO THREAT DATA AVAILABLE --
          </div>
        ) : (
          corridorRisks.map((t, idx) => {
            const ss = statusStyle(t.threat_level);
            const probPct = Math.round(t.risk_score * 100);
            return (
              <div key={idx} style={{ borderLeft: `2px solid ${ss.dot}`, background: 'rgba(14,21,32,.6)', padding: '8px 10px' }}>
                <div className="flex justify-between items-center" style={{ marginBottom: '3px' }}>
                  <span className="font-mono text-sm text-ink font-semibold">{t.corridor_name}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-lg font-bold" style={{ color: ss.color, lineHeight: 1 }}>
                      {probPct}<span className="text-xs" style={{ opacity: 0.6 }}>%</span>
                    </span>
                    <StatusBadge status={t.threat_level} small />
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="font-mono text-xs text-muted" style={{ flex: 1 }}>{t.primary_driver}</div>
                </div>
                <div style={{ marginTop: '5px', height: '2px', background: C.border, borderRadius: '1px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', background: ss.dot, width: `${probPct}%`, transition: 'width .6s', opacity: 0.7 }} />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
