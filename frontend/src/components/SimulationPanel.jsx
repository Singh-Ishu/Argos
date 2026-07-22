import React from 'react';

const CORRIDORS = ['Strait of Hormuz', 'Red Sea / Bab-el-Mandeb', 'Malacca Strait'];
const REFINERIES = ['Jamnagar & IOCL Complex', 'IOCL Paradip Refinery', 'Kochi Refinery', 'Mangalore Refinery'];

export default function SimulationPanel({
  corridor, setCorridor,
  severity, setSeverity,
  duration, setDuration,
  refineryName, setRefineryName,
  minApiGravity, setMinApiGravity,
  maxSulfurPct, setMaxSulfurPct,
  onExecute, running
}) {
  
  const C = {
    cyan: '#06B6D4',
    cyan10: 'rgba(6, 182, 212, 0.10)',
    cyan30: 'rgba(6, 182, 212, 0.30)',
    border: '#1E2638',
    bg: '#0A0C10',
    ink: '#E2E8F0',
    muted: '#64748B'
  };

  return (
    <div className="panel" style={{ flexShrink: 0 }}>
      <div className="panel-hd">
        <span>Simulation Control Panel</span>
        <span className="font-mono text-cyan" style={{ letterSpacing: '0.08em' }}>
          {running ? 'AGENT EXECUTING' : 'AGENT READY'}
        </span>
      </div>
      <div className="panel-body flex flex-col gap-3">
        {/* Select Corridor */}
        <div>
          <label htmlFor="sim-corridor" className="font-mono uppercase text-xs text-muted" style={{ display: 'block', marginBottom: '4px', letterSpacing: '0.1em' }}>
            Select Corridor
          </label>
          <select
            id="sim-corridor"
            value={corridor}
            onChange={e => setCorridor(e.target.value)}
            className="w-full"
          >
            {CORRIDORS.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        {/* Severity Slider */}
        <div>
          <div className="flex justify-between" style={{ marginBottom: '4px' }}>
            <label htmlFor="sim-severity" className="font-mono uppercase text-xs text-muted" style={{ letterSpacing: '0.1em' }}>
              Closure Severity
            </label>
            <span className="font-mono text-cyan font-semibold text-md">{severity}%</span>
          </div>
          <input
            id="sim-severity"
            type="range"
            min="0"
            max="100"
            value={severity}
            onChange={e => setSeverity(parseInt(e.target.value))}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={severity}
            aria-label={`Closure severity ${severity}%`}
          />
          <div className="flex justify-between font-mono text-xs text-muted" style={{ marginTop: '2px' }}>
            <span>0%</span><span>50%</span><span>100%</span>
          </div>
        </div>

        {/* Duration Inputs */}
        <div className="flex gap-2 w-full">
          <div style={{ flex: 1 }}>
            <label htmlFor="sim-duration" className="font-mono uppercase text-xs text-muted" style={{ display: 'block', marginBottom: '4px', letterSpacing: '0.1em' }}>
              Duration (Days)
            </label>
            <input
              id="sim-duration"
              type="number"
              min="1"
              max="90"
              value={duration}
              onChange={e => setDuration(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-full"
            />
          </div>
          <div style={{ flex: 1.5 }}>
            <label htmlFor="sim-refinery" className="font-mono uppercase text-xs text-muted" style={{ display: 'block', marginBottom: '4px', letterSpacing: '0.1em' }}>
              Target Refinery
            </label>
            <select
              id="sim-refinery"
              value={refineryName}
              onChange={e => setRefineryName(e.target.value)}
              className="w-full"
              style={{ padding: '6px 20px 6px 10px', height: '31px' }}
            >
              {REFINERIES.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
        </div>

        {/* Refinery Specs */}
        <div className="flex gap-2 w-full">
          <div style={{ flex: 1 }}>
            <label htmlFor="sim-api" className="font-mono uppercase text-xs text-muted" style={{ display: 'block', marginBottom: '4px', letterSpacing: '0.08em' }}>
              Min API Gravity
            </label>
            <input
              id="sim-api"
              type="number"
              step="0.1"
              min="20"
              max="45"
              value={minApiGravity}
              onChange={e => setMinApiGravity(parseFloat(e.target.value) || 28.0)}
              className="w-full"
            />
          </div>
          <div style={{ flex: 1 }}>
            <label htmlFor="sim-sulfur" className="font-mono uppercase text-xs text-muted" style={{ display: 'block', marginBottom: '4px', letterSpacing: '0.08em' }}>
              Max Sulfur %
            </label>
            <input
              id="sim-sulfur"
              type="number"
              step="0.05"
              min="0.1"
              max="5.0"
              value={maxSulfurPct}
              onChange={e => setMaxSulfurPct(parseFloat(e.target.value) || 2.0)}
              className="w-full"
            />
          </div>
        </div>

        {/* Trigger Button */}
        <button
          onClick={onExecute}
          disabled={running}
          aria-busy={running}
          aria-label={running ? 'Agent simulation executing' : 'Execute agent simulation'}
          className="flex justify-center items-center gap-2"
          style={{
            width: '100%', padding: '9px', borderRadius: '4px', border: `1px solid ${C.cyan30}`,
            background: running ? 'rgba(6,182,212,.05)' : C.cyan10,
            color: running ? C.muted : C.cyan,
            fontFamily: 'ui-monospace,monospace', fontSize: '10px', letterSpacing: '.14em',
            textTransform: 'uppercase', cursor: running ? 'not-allowed' : 'pointer',
            transition: 'background .2s, color .2s',
            pointerEvents: running ? 'none' : 'auto',
          }}
        >
          {running ? (
            <>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                className="spin-anim" style={{ flexShrink: 0 }}>
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
              EXECUTING AGENTS...
            </>
          ) : (
            <>
              <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" style={{ flexShrink: 0 }}>
                <polygon points="5,3 19,12 5,21"/>
              </svg>
              EXECUTE AGENT SIMULATION
            </>
          )}
        </button>
      </div>
    </div>
  );
}
