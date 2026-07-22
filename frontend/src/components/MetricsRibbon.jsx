import React from 'react';

export default function MetricsRibbon({ dailyDeficit = 2.2, sprCover = 18.2, costPremium = 14.80, gdpImpact = -0.28 }) {
  const C = {
    crimson: '#EF4444',
    crimson10: 'rgba(239, 68, 68, 0.10)',
    crimson30: 'rgba(239, 68, 68, 0.30)',
    amber: '#F59E0B',
    amber10: 'rgba(245, 158, 11, 0.10)',
    amber30: 'rgba(245, 158, 11, 0.30)',
    ink: '#E2E8F0',
    muted: '#64748B',
    card: '#12161F',
    border: '#1E2638',
  };

  const METRICS = [
    {
      label: 'Daily Crude Deficit',
      value: dailyDeficit.toFixed(2),
      unit: 'MBPD',
      sub: `${((dailyDeficit / 5.0) * 100).toFixed(1)}% of India Total Imports`,
      color: C.crimson,
      trend: '▲ CRITICAL',
    },
    {
      label: 'SPR Runway Cover',
      value: sprCover.toFixed(1),
      unit: 'Days',
      sub: '30.0 MB Available / Floor: 25%',
      color: C.amber,
      trend: '▼ DECLINING',
    },
    {
      label: 'Landed Cost Premium',
      value: `+$${costPremium.toFixed(2)}`,
      unit: '/bbl',
      sub: 'Weighted Spot + Freight Surge',
      color: C.amber,
      trend: '▲ ELEVATED',
    },
    {
      label: 'Projected GDP Impact',
      value: `${gdpImpact > 0 ? '-' : ''}${Math.abs(gdpImpact).toFixed(2)}`,
      unit: '%',
      sub: 'Quarterly Macro Drag Forecast',
      color: C.crimson,
      trend: '▼ RISK',
    },
  ];

  return (
    <div className="grid flex-shrink-0" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '8px', padding: '0 8px 8px' }}>
      {METRICS.map((m, i) => (
        <div key={i} className="panel" style={{
          background: C.card, border: `1px solid ${C.border}`, borderLeft: `3px solid ${m.color}`,
          borderRadius: '6px', padding: '10px 14px',
        }}>
          <div className="font-mono text-xs uppercase text-muted letter-spacing-2" style={{ marginBottom: '4px' }}>
            {m.label}
          </div>
          <div className="font-mono text-3xl font-bold" style={{ color: m.color, lineHeight: 1.1 }}>
            {m.value}
            <span className="text-xs font-semibold text-muted" style={{ marginLeft: '3px' }}>{m.unit}</span>
          </div>
          <div className="flex items-center justify-between" style={{ marginTop: '5px' }}>
            <div className="font-mono text-xs text-muted" style={{ maxWidth: '70%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {m.sub}
            </div>
            <div className="font-mono text-xs" style={{ color: m.color, letterSpacing: '.08em', opacity: 0.7 }}>
              {m.trend}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
