import React, { useState } from 'react';

// Refineries: [label, cx, cy, short]
const REFINERIES = [
  ['Jamnagar', 66, 108, 'JAM'],
  ['Mangalore', 80, 192, 'MNG'],
  ['Paradip', 190, 98, 'PRD'],
  ['Kochi', 88, 218, 'KCH'],
  ['Haldia', 196, 80, 'HLD'],
];

// Chokepoints
const CHOKE = [
  { id: 'hormuz', cx: 18, cy: 92, label: 'HORMUZ', color: '#EF4444' },
  { id: 'bab', cx: 18, cy: 140, label: 'BAB EL-MANDEB', color: '#F59E0B' },
  { id: 'malacca', cx: 260, cy: 166, label: 'MALACCA', color: '#10B981' },
];

// Shipping lanes
const LANES = [
  { id: 'hormuz', label: 'Hormuz', points: [[8, 88], [40, 96], [60, 108], [66, 108]], color: '#EF4444', dash: '5,4', width: 1.5 },
  { id: 'redsea', label: 'Red Sea / Bab-el-Mandeb', points: [[8, 148], [28, 136], [44, 120], [58, 106], [66, 108]], color: '#F59E0B', dash: '4,3', width: 1.5 },
  { id: 'malacca', label: 'Malacca Strait', points: [[272, 168], [240, 158], [210, 148], [190, 138], [180, 128], [175, 108], [165, 98], [148, 94]], color: '#10B981', dash: '', width: 1.5 },
  { id: 'cape', label: 'Cape Alt Route', points: [[8, 220], [20, 240], [30, 260], [50, 272], [80, 270], [100, 265], [120, 264], [140, 265]], color: '#06B6D4', dash: '6,4', width: 1 },
];

// Tankers
const TANKERS = [
  { cx: 30, cy: 100, color: '#EF4444', lane: 'hormuz' },
  { cx: 22, cy: 145, color: '#F59E0B', lane: 'redsea' },
  { cx: 255, cy: 162, color: '#10B981', lane: 'malacca' },
  { cx: 50, cy: 260, color: '#06B6D4', lane: 'cape' },
];

// India map path definition
const INDIA_PATH = "M 98,8 L 112,6 L 128,10 L 145,8 L 162,14 L 175,12 L 190,20 L 200,30 L 208,44 L 210,58 L 218,70 L 222,82 L 215,94 L 220,108 L 225,118 L 230,130 L 228,145 L 220,158 L 210,168 L 196,178 L 185,190 L 175,204 L 168,218 L 162,232 L 154,244 L 148,256 L 140,265 L 134,270 L 128,262 L 122,250 L 116,238 L 108,226 L 98,215 L 88,204 L 80,192 L 74,180 L 70,166 L 66,152 L 64,138 L 68,124 L 64,110 L 60,96 L 56,82 L 60,68 L 66,56 L 72,44 L 80,34 L 90,24 Z";

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

  // Helper to check if a specific corridor is active in the simulator
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
        <svg viewBox="0 0 280 290" width="100%" height="100%" style={{ display: 'block' }}>
          {/* sea background */}
          <rect width="280" height="290" fill="#080b11" />

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

          {/* India landmass */}
          <path d={INDIA_PATH} fill="#0e1520" stroke="#1E2638" strokeWidth="1" />

          {/* Render chokepoints */}
          {showChoke && CHOKE.map(ch => {
            const isActive = isCorridorActive(ch.id);
            const chColor = isActive ? (severity > 70 ? C.crimson : C.amber) : ch.color;
            return (
              <g key={ch.id}>
                {isActive && (
                  <circle cx={ch.cx} cy={ch.cy} r="8" fill="none" stroke={chColor} strokeWidth="1.5" className={severity > 70 ? 'pulse-crimson' : 'pulse-amber'} />
                )}
                <circle cx={ch.cx} cy={ch.cy} r="4" fill="none" stroke={chColor} strokeWidth="1" opacity=".8" />
                <circle cx={ch.cx} cy={ch.cy} r="2" fill={chColor} opacity=".9" />
                <text x={ch.cx + 8} y={ch.cy + 3} fill={chColor} fontSize="8" fontFamily="ui-monospace,monospace" fontWeight={isActive ? 'bold' : 'normal'} letterSpacing=".06em">
                  {ch.label} {isActive ? `(${severity}%)` : ''}
                </text>
              </g>
            );
          })}

          {/* Render refineries */}
          {showRefineries && REFINERIES.map(([name, cx, cy, short]) => (
            <g key={name}>
              <polygon
                points={`${cx},${cy - 7} ${cx - 5},${cy + 4} ${cx + 5},${cy + 4}`}
                fill="#06B6D4" stroke="#06B6D4" strokeWidth=".5" opacity=".9"
              />
              <text x={cx + 7} y={cy + 2} fill="#06B6D4" fontSize="8" fontFamily="ui-monospace,monospace" fontWeight="600">
                {short}
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
                points={`${tk.cx},${tk.cy - 5} ${tk.cx - 4},${tk.cy + 3} ${tk.cx + 4},${tk.cy + 3}`}
                fill={tkColor}
                opacity={isActive ? 1.0 : 0.75}
                className={isActive ? 'blink' : ''}
              />
            );
          })}

          {/* map legend */}
          <g transform="translate(6,270)">
            {[
              [C.crimson, 'HORMUZ - BLOCKADE'],
              [C.amber, 'RED SEA - RISK'],
              [C.emerald, 'MALACCA - SECURE'],
              [C.cyan, 'CAPE ALT ROUTE'],
            ].map(([col, lbl], i) => (
              <g key={i} transform={`translate(${i * 68},0)`}>
                <line x1="0" y1="3" x2="10" y2="3" stroke={col} strokeWidth="1.5" />
                <text x="13" y="6" fill={col} fontSize="7" fontFamily="ui-monospace,monospace">{lbl}</text>
              </g>
            ))}
          </g>
        </svg>
      </div>
    </div>
  );
}
