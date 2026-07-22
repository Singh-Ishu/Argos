import React, { useState } from 'react';

// Refineries: [label, cx, cy, short, textOffsetX, textOffsetY]
const REFINERIES = [
  { name: 'Jamnagar', cx: 1395, cy: 352, short: 'JAM', tx: 12, ty: 4 },
  { name: 'Mangalore', cx: 1426, cy: 395, short: 'MNG', tx: -46, ty: 2 },
  { name: 'Paradip', cx: 1472, cy: 370, short: 'PRD', tx: 12, ty: 5 },
  { name: 'Kochi', cx: 1432, cy: 409, short: 'KCH', tx: 12, ty: 4 },
  { name: 'Haldia', cx: 1485, cy: 357, short: 'HLD', tx: 12, ty: -6 },
];

// Chokepoints
const CHOKE = [
  { id: 'hormuz', cx: 1305, cy: 332, label: 'HORMUZ', color: '#EF4444' },
  { id: 'bab', cx: 1238, cy: 368, label: 'BAB EL-MANDEB', color: '#F59E0B' },
  { id: 'malacca', cx: 1566, cy: 486, label: 'MALACCA', color: '#10B981' },
];

// Shipping lanes
const LANES = [
  { id: 'hormuz', label: 'Hormuz', points: [[1305, 332], [1335, 340], [1365, 348], [1395, 352]], color: '#EF4444', dash: '8,6', width: 2.2 },
  { id: 'redsea', label: 'Red Sea / Bab-el-Mandeb', points: [[1238, 368], [1280, 380], [1330, 390], [1380, 400], [1426, 395]], color: '#F59E0B', dash: '8,6', width: 2.2 },
  { id: 'malacca', label: 'Malacca Strait', points: [[1610, 500], [1566, 486], [1525, 430], [1472, 370]], color: '#10B981', dash: '', width: 2.2 },
  { id: 'cape', label: 'Cape Alt Route', points: [[1120, 720], [1200, 680], [1280, 610], [1360, 520], [1432, 409]], color: '#06B6D4', dash: '10,6', width: 1.6 },
];

// Tankers
const TANKERS = [
  { cx: 1350, cy: 344, color: '#EF4444', lane: 'hormuz' },
  { cx: 1330, cy: 390, color: '#F59E0B', lane: 'redsea' },
  { cx: 1545, cy: 458, color: '#10B981', lane: 'malacca' },
  { cx: 1240, cy: 650, color: '#06B6D4', lane: 'cape' },
];

export default function TacticalMap({ selectedCorridor = 'Strait of Hormuz', severity = 45 }) {
  const [activeToggle, setActiveToggle] = useState('All');
  const toggles = ['All', 'Shipping', 'Choke Pts', 'Refineries'];

  const showShipping = activeToggle === 'All' || activeToggle === 'Shipping';
  const showChoke = activeToggle === 'All' || activeToggle === 'Choke Pts';
  const showRefineries = activeToggle === 'All' || activeToggle === 'Refineries';

  const C = {
    cyan: '#06B6D4',
    cyan10: 'rgba(6, 182, 212, 0.10)',
    border: '#1E2638',
    muted: '#64748B',
    amber: '#F59E0B',
    crimson: '#EF4444',
    emerald: '#10B981'
  };

  const isCorridorActive = (laneId) => {
    if (laneId === 'hormuz' && selectedCorridor === 'Strait of Hormuz') return true;
    if (laneId === 'redsea' && selectedCorridor === 'Red Sea / Bab-el-Mandeb') return true;
    if (laneId === 'malacca' && selectedCorridor === 'Malacca Strait') return true;
    return false;
  };

  return (
    <div className="panel" style={{ flex: 1 }}>
      <div className="panel-hd">
        <span>Geospatial Supply Corridor Monitor</span>
        <div className="flex gap-1">
          {toggles.map(t => (
            <button
              key={t}
              onClick={() => setActiveToggle(t)}
              style={{
                fontFamily: 'ui-monospace,monospace', fontSize: '8px', letterSpacing: '.08em',
                padding: '2px 6px', borderRadius: '3px', cursor: 'pointer', border: '1px solid',
                borderColor: activeToggle === t ? C.cyan : C.border,
                background: activeToggle === t ? C.cyan10 : 'transparent',
                color: activeToggle === t ? C.cyan : C.muted,
              }}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="map-wrap" style={{ flex: 1, margin: '8px' }}>
        <div className="scan-line" />
        {/* Render at high resolution vector coordinate space focused on Afro-Eurasia / Indian Ocean */}
        <svg viewBox="1060 280 560 450" width="100%" height="100%" style={{ display: 'block' }}>
          {/* Background Vector Map Image */}
          <image href="/world.svg" x="0" y="0" width="2000" height="857" />

          {/* Render shipping lanes */}
          {showShipping && LANES.map(ln => {
            const isActive = isCorridorActive(ln.id);
            const strokeColor = isActive ? (severity > 70 ? C.crimson : C.amber) : ln.color;
            const strokeW = isActive ? ln.width * 2.2 : ln.width;
            return (
              <g key={ln.id}>
                {isActive && (
                  <polyline
                    points={ln.points.map(p => p.join(',')).join(' ')}
                    fill="none"
                    stroke={strokeColor}
                    strokeWidth={strokeW * 2}
                    opacity="0.15"
                    className="pulse-amber"
                  />
                )}
                <polyline
                  points={ln.points.map(p => p.join(',')).join(' ')}
                  fill="none"
                  stroke={strokeColor}
                  strokeWidth={strokeW}
                  strokeDasharray={ln.dash}
                  opacity={isActive ? 1.0 : 0.65}
                />
              </g>
            );
          })}

          {/* Render chokepoints */}
          {showChoke && CHOKE.map(ch => {
            const isActive = isCorridorActive(ch.id);
            const chColor = isActive ? (severity > 70 ? C.crimson : C.amber) : ch.color;
            return (
              <g key={ch.id}>
                {isActive && (
                  <circle cx={ch.cx} cy={ch.cy} r="14" fill="none" stroke={chColor} strokeWidth="1.8" className={severity > 70 ? 'pulse-crimson' : 'pulse-amber'} />
                )}
                <circle cx={ch.cx} cy={ch.cy} r="6" fill="none" stroke={chColor} strokeWidth="1.2" opacity=".8" />
                <circle cx={ch.cx} cy={ch.cy} r="3" fill={chColor} opacity=".9" />
                <text x={ch.cx + 10} y={ch.cy + 4} fill={chColor} fontSize="13" fontFamily="ui-monospace,monospace" fontWeight={isActive ? 'bold' : 'normal'} letterSpacing=".04em">
                  {ch.label} {isActive ? `(${severity}%)` : ''}
                </text>
              </g>
            );
          })}

          {/* Render refineries */}
          {showRefineries && REFINERIES.map(ref => (
            <g key={ref.name}>
              <polygon
                points={`${ref.cx},${ref.cy - 9} ${ref.cx - 7},${ref.cy + 5} ${ref.cx + 7},${ref.cy + 5}`}
                fill="#06B6D4" stroke="#06B6D4" strokeWidth="0.8" opacity=".9"
              />
              <text x={ref.cx + ref.tx} y={ref.cy + ref.ty} fill="#06B6D4" fontSize="13" fontFamily="ui-monospace,monospace" fontWeight="600">
                {ref.short}
              </text>
            </g>
          ))}

          {/* Render tankers */}
          {showShipping && TANKERS.map((tk, i) => {
            const isActive = isCorridorActive(tk.lane);
            const tkColor = isActive ? (severity > 70 ? C.crimson : C.amber) : tk.color;
            return (
              <polygon
                key={i}
                points={`${tk.cx},${tk.cy - 7} ${tk.cx - 6},${tk.cy + 4} ${tk.cx + 6},${tk.cy + 4}`}
                fill={tkColor}
                opacity={isActive ? 1.0 : 0.75}
                className={isActive ? 'blink' : ''}
              />
            );
          })}
        </svg>
      </div>

      {/* Map Legend: HTML outer container for perfect vector sharp layout */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-around',
        padding: '8px 12px',
        borderTop: `1px solid ${C.border}`,
        background: 'rgba(10, 12, 16, 0.5)',
        flexWrap: 'wrap',
        gap: '8px'
      }}>
        {[
          [C.crimson, 'HORMUZ - BLOCKADE'],
          [C.amber, 'RED SEA - RISK'],
          [C.emerald, 'MALACCA - SECURE'],
          [C.cyan, 'CAPE ALT ROUTE'],
        ].map(([col, lbl], i) => (
          <div key={i} className="flex items-center gap-2" style={{ fontFamily: 'ui-monospace,monospace', fontSize: '9px' }}>
            <span style={{ display: 'inline-block', width: '12px', height: '2px', background: col }} />
            <span style={{ color: col, letterSpacing: '0.06em' }}>{lbl}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
