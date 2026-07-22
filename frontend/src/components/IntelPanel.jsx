import React, { useState } from 'react';

const C = {
  border: '#1E2638',
  border50: 'rgba(30,38,56,.5)',
  cyan: '#06B6D4',
  cyan10: 'rgba(6,182,212,.10)',
  cyan30: 'rgba(6,182,212,.30)',
  muted: '#64748B',
  muted10: 'rgba(100,116,139,.10)',
  muted30: 'rgba(100,116,139,.30)',
  crimson: '#EF4444',
  crimson10: 'rgba(239,68,68,.10)',
  crimson30: 'rgba(239,68,68,.30)',
  amber: '#F59E0B',
  amber10: 'rgba(245,158,11,.10)',
  amber30: 'rgba(245,158,11,.30)',
  emerald: '#10B981',
  emerald10: 'rgba(16,185,129,.10)',
  emerald30: 'rgba(16,185,129,.30)',
  ink: '#E2E8F0',
  card: '#12161F'
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

function Label({ children }) {
  return (
    <div style={{
      fontFamily: 'ui-monospace,monospace', fontSize: '9px', letterSpacing: '.1em',
      textTransform: 'uppercase', color: C.muted, marginBottom: '4px'
    }}>
      {children}
    </div>
  );
}

/* SPR Drawdown SVG Chart */
function SPRChart({ schedule = [], capacity = 39.5 }) {
  if (!schedule || schedule.length === 0) {
    return (
      <div style={{ height: '140px', background: '#080b11', border: `1px solid ${C.border}`, borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: C.muted, fontFamily: 'ui-monospace' }}>
        NO DRAWDOWN SCHEDULE DATA
      </div>
    );
  }

  const w = 300, h = 140, pad = { l: 40, r: 10, t: 15, b: 25 };
  const inner = { w: w - pad.l - pad.r, h: h - pad.t - pad.b };

  const maxVal = capacity;
  const minVal = 0;
  
  const yScale = (val) => pad.t + inner.h - ((val - minVal) / (maxVal - minVal)) * inner.h;
  const xScale = (idx) => pad.l + (idx / (schedule.length - 1)) * inner.w;

  const floorVal = capacity * 0.25;
  const floorY = yScale(floorVal);

  const stockPath = schedule.map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)},${yScale(d.remaining_stock_mb)}`).join(' ');

  // Y Axis ticks: 0, 25%, 50%, 75%, 100% of capacity
  const yTicks = [0, parseFloat((capacity * 0.25).toFixed(1)), parseFloat((capacity * 0.5).toFixed(1)), parseFloat((capacity * 0.75).toFixed(1)), capacity];
  
  // X Axis ticks: Day 1, Middle Day, Final Day
  const totalDays = schedule.length;
  const xTicks = [1, Math.round(totalDays / 2), totalDays];

  return (
    <div style={{ background: '#080b11', border: `1px solid ${C.border}`, borderRadius: '4px', padding: '10px', overflow: 'visible' }}>
      <svg viewBox={`0 0 ${w} ${h}`} width="100%" style={{ display: 'block', overflow: 'visible' }}>
        {/* Y Grid & Labels */}
        {yTicks.map((tick, idx) => {
          const y = yScale(tick);
          return (
            <g key={idx}>
              <line x1={pad.l} x2={pad.l + inner.w} y1={y} y2={y} stroke="#1E2638" strokeWidth=".5" />
              <text x={pad.l - 6} y={y + 3} fill={C.muted} fontSize="8" textAnchor="end" fontFamily="ui-monospace,monospace">{tick}M</text>
            </g>
          );
        })}

        {/* X Grid & Labels */}
        {xTicks.map((tick, idx) => {
          const x = xScale(tick - 1);
          return (
            <g key={idx}>
              <line x1={x} x2={x} y1={pad.t + inner.h} y2={pad.t + inner.h + 4} stroke={C.border} strokeWidth=".5" />
              <text x={x} y={pad.t + inner.h + 14} fill={C.muted} fontSize="8" textAnchor="middle" fontFamily="ui-monospace,monospace">D+{tick}</text>
            </g>
          );
        })}

        {/* 25% National Buffer Floor Line */}
        <line x1={pad.l} x2={pad.l + inner.w} y1={floorY} y2={floorY} stroke={C.crimson} strokeWidth="1" strokeDasharray="3,2" opacity=".7" />
        <text x={pad.l + inner.w - 5} y={floorY - 4} fill={C.crimson} fontSize="7" textAnchor="end" fontFamily="ui-monospace,monospace">25% BUFFER FLOOR</text>

        {/* Simulated Drawdown Curve */}
        <path d={stockPath} fill="none" stroke={C.amber} strokeWidth="2" />

        {/* Legend */}
        <g transform={`translate(${pad.l}, 6)`}>
          <line x1="0" y1="0" x2="14" y2="0" stroke={C.amber} strokeWidth="2" />
          <text x="18" y="3" fill={C.amber} fontSize="7" fontFamily="ui-monospace,monospace">SIMULATED SPR STOCK</text>
        </g>
      </svg>
    </div>
  );
}

export default function IntelPanel({ report }) {
  const [tab, setTab] = useState(0);
  const tabs = ['Scenario Impact', 'Procurement Matrix', 'SPR Drawdown'];

  // Fallback / Initial Mock data if no report is loaded yet
  const mockScenario = {
    executive_briefing: "Select a supply corridor and trigger 'Execute Agent Simulation' to view the automated risk assessment and resilience directives.",
    cascading_impacts: [
      "Select simulation inputs to model crude import deficit impacts.",
      "Projects Brent Crude volatility indices and pricing benchmarks.",
      "Computes potential GDP drag percentages across industrial clusters.",
    ],
    recommended_policy_directives: [
      "Simulate a scenario to generate inter-agency action directives.",
    ]
  };

  const mockProcurement = {
    optimization: {
      allocations: [
        { crude_name: 'Basrah Medium', origin_country: 'Iraq', allocated_mbpd: 0.80, total_landed_cost_usd_bbl: 88.50, lead_time_days: 7, status: 'OPTIMAL' },
        { crude_name: 'Forcados', origin_country: 'Nigeria', allocated_mbpd: 0.60, total_landed_cost_usd_bbl: 92.10, lead_time_days: 18, status: 'FEASIBLE' },
        { crude_name: 'Tupi', origin_country: 'Brazil', allocated_mbpd: 0.40, total_landed_cost_usd_bbl: 94.30, lead_time_days: 22, status: 'FEASIBLE' },
      ],
      total_procured_mbpd: 1.80,
      weighted_cost: 91.72,
      unfilled_deficit_mbpd: 0.00
    },
    refinery_name: "Jamnagar & IOCL Complex"
  };

  const mockSpr = {
    optimization: {
      daily_schedule: Array.from({ length: 15 }, (_, i) => ({
        day: i + 1,
        remaining_stock_mb: parseFloat((30.0 - i * 0.45).toFixed(2)),
      })),
      floor_breached: false,
      alert_level: "NOMINAL"
    },
    policy_briefing: "SPR optimization module will calculate drawdown schedules and verify cavern levels.",
    inter_agency_actions: [
      "Drawdown authorization protocols.",
    ],
    replenishment_strategy: "Post-crisis reserve accumulation guidelines."
  };

  const activeScenario = report?.scenario || mockScenario;
  const activeProcurement = report?.procurement || mockProcurement;
  const activeSpr = report?.spr || mockSpr;

  // Calculate weighted average cost if dynamic report is loaded
  let totalDailyCost = activeProcurement.optimization?.total_daily_cost_usd;
  let totalProcured = activeProcurement.optimization?.total_procured_mbpd;
  let weightedBarrelCost = activeProcurement.optimization?.weighted_cost || 0;
  if (totalDailyCost && totalProcured > 0) {
    weightedBarrelCost = totalDailyCost / (totalProcured * 1e6);
  }

  return (
    <div className="panel" style={{ flex: 1 }}>
      <div className="panel-hd">
        <span>Multi-Agent Intelligence Synthesis</span>
        <div className="flex gap-1">
          {tabs.map((t, i) => (
            <button
              key={i}
              onClick={() => setTab(i)}
              style={{
                fontFamily: 'ui-monospace,monospace', fontSize: '8px', letterSpacing: '.08em',
                padding: '2px 6px', borderRadius: '3px', cursor: 'pointer', border: '1px solid',
                borderColor: tab === i ? C.cyan : C.border,
                background: tab === i ? C.cyan10 : 'transparent',
                color: tab === i ? C.cyan : C.muted,
              }}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="panel-body flex flex-col gap-3">
        {/* Tab 0: Scenario Impact */}
        {tab === 0 && (
          <>
            <div style={{ background: 'rgba(6,182,212,.03)', border: `1px solid ${C.border}`, borderRadius: '4px', padding: '10px' }}>
              <div className="flex justify-between items-center" style={{ marginBottom: '8px' }}>
                <Label>Executive Briefing - LLM Narrative</Label>
                {report && (
                  <div className="flex gap-3">
                    <span className="font-mono text-xs text-crimson">
                      Brent <span style={{ fontSize: '13px', fontWeight: 700 }}>+{report.scenario.metrics.estimated_brent_surge_pct.toFixed(1)}%</span>
                    </span>
                    <span className="font-mono text-xs text-amber">
                      Fuel <span style={{ fontSize: '13px', fontWeight: 700 }}>+{report.scenario.metrics.estimated_domestic_fuel_price_surge_pct.toFixed(1)}%</span>
                    </span>
                  </div>
                )}
              </div>
              <div className="font-mono text-xs" style={{ lineHeight: 1.6, color: C.muted }}>
                {activeScenario.executive_briefing}
              </div>
            </div>

            <div>
              <Label>Cascading Impacts</Label>
              <ul className="font-mono text-xs" style={{ lineHeight: 1.6, color: C.muted, listStyle: 'none' }}>
                {activeScenario.cascading_impacts.map((c, i) => (
                  <li key={i} style={{ paddingLeft: '12px', position: 'relative', marginBottom: '4px' }}>
                    <span style={{ position: 'absolute', left: 0, color: C.amber }}>▸</span>
                    {c}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <Label>Recommended Directives</Label>
              <ul className="font-mono text-xs" style={{ lineHeight: 1.6, color: C.cyan, listStyle: 'none' }}>
                {activeScenario.recommended_policy_directives.map((d, i) => (
                  <li key={i} style={{ paddingLeft: '12px', position: 'relative', marginBottom: '4px' }}>
                    <span style={{ position: 'absolute', left: 0 }}>▸</span>
                    {d}
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}

        {/* Tab 1: Procurement Matrix */}
        {tab === 1 && (
          <>
            <div className="overflow-auto" style={{ maxHeight: '180px' }}>
              <table className="tac-table">
                <thead>
                  <tr>
                    <th className="tac-th">Grade</th>
                    <th className="tac-th">Origin</th>
                    <th className="tac-th" style={{ textAlign: 'right' }}>Vol (MBPD)</th>
                    <th className="tac-th" style={{ textAlign: 'right' }}>Landed Cost</th>
                    <th className="tac-th" style={{ textAlign: 'center' }}>Lead</th>
                  </tr>
                </thead>
                <tbody>
                  {activeProcurement.optimization?.allocations?.map((r, i) => (
                    <tr key={i} className="tac-tr">
                      <td className="tac-td">{r.crude_name}</td>
                      <td className="tac-td" style={{ color: C.muted }}>{r.origin_country}</td>
                      <td className="tac-td" style={{ textAlign: 'right' }}>{parseFloat(r.allocated_mbpd).toFixed(3)}</td>
                      <td className="tac-td" style={{ textAlign: 'right' }}>${parseFloat(r.total_landed_cost_usd_bbl).toFixed(1)}</td>
                      <td className="tac-td" style={{ textAlign: 'center', color: C.muted }}>{r.lead_time_days}d</td>
                    </tr>
                  ))}
                  {(!activeProcurement.optimization?.allocations || activeProcurement.optimization.allocations.length === 0) && (
                    <tr>
                      <td colSpan="5" className="tac-td text-center" style={{ color: C.muted, padding: '12px' }}>
                        No crude allocations (optimization bypassed / zero deficit)
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="grid" style={{ gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', marginTop: '8px' }}>
              <div style={{ background: C.cyan10, border: `1px solid ${C.cyan30}`, borderRadius: '4px', padding: '6px 8px', textAlign: 'center' }}>
                <Label>Total Procured</Label>
                <div className="font-mono font-bold text-lg text-cyan">
                  {totalProcured ? totalProcured.toFixed(2) : '0.00'} MBPD
                </div>
              </div>
              <div style={{ background: C.amber10, border: `1px solid ${C.amber30}`, borderRadius: '4px', padding: '6px 8px', textAlign: 'center' }}>
                <Label>Weighted Cost</Label>
                <div className="font-mono font-bold text-lg text-amber">
                  ${weightedBarrelCost ? weightedBarrelCost.toFixed(2) : '0.00'}/bbl
                </div>
              </div>
              <div style={{ background: C.crimson10, border: `1px solid ${C.crimson30}`, borderRadius: '4px', padding: '6px 8px', textAlign: 'center' }}>
                <Label>Unfilled Deficit</Label>
                <div className="font-mono font-bold text-lg text-crimson">
                  {activeProcurement.optimization?.unfilled_deficit_mbpd ? activeProcurement.optimization.unfilled_deficit_mbpd.toFixed(2) : '0.00'} MBPD
                </div>
              </div>
            </div>
          </>
        )}

        {/* Tab 2: SPR Drawdown */}
        {tab === 2 && (
          <>
            <div>
              <Label>Simulated Reserve Depletion Schedule</Label>
            </div>
            
            <SPRChart
              schedule={activeSpr.optimization?.daily_schedule}
              capacity={report?.scenario?.spr_total_capacity_mb || 39.5}
            />

            <div style={{ background: activeSpr.optimization?.floor_breached ? C.crimson10 : C.amber10, border: `1px solid ${activeSpr.optimization?.floor_breached ? C.crimson30 : C.amber30}`, borderRadius: '4px', padding: '8px 10px', marginTop: '6px' }}>
              <div className="flex items-center gap-2">
                <StatusBadge status={activeSpr.optimization?.alert_level || 'NOMINAL'} small />
                <span className="font-mono text-xs font-semibold" style={{ color: activeSpr.optimization?.floor_breached ? C.crimson : C.amber, letterSpacing: '.08em' }}>
                  STATUS: {activeSpr.optimization?.floor_breached ? 'CRITICAL RESERVE BREACH DETECTED' : 'RESERVE FLOOR PRESERVED'}
                </span>
              </div>
              <div className="font-mono text-xs text-muted" style={{ marginTop: '5px', lineHeight: '1.4' }}>
                {activeSpr.policy_briefing}
              </div>
            </div>

            <div>
              <Label>Inter-Agency Directives</Label>
              <ul className="font-mono text-xs" style={{ lineHeight: 1.6, color: C.muted, listStyle: 'none' }}>
                {activeSpr.inter_agency_actions.map((act, i) => (
                  <li key={i} style={{ paddingLeft: '12px', position: 'relative', marginBottom: '4px' }}>
                    <span style={{ position: 'absolute', left: 0, color: C.cyan }}>▸</span>
                    {act}
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
