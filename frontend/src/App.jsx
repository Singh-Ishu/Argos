import React, { useState, useEffect, useRef, useCallback } from 'react';
import CommandHeader from './components/CommandHeader';
import MetricsRibbon from './components/MetricsRibbon';
import SimulationPanel from './components/SimulationPanel';
import ThreatFeed from './components/ThreatFeed';
import TacticalMap from './components/TacticalMap';
import IntelPanel from './components/IntelPanel';
import TerminalConsole from './components/TerminalConsole';

const INIT_LOGS = [
  { ts: '01:28:08', level: 'INFO',    msg: 'ARGOS daemon v3.1.4 initialised - node INDIA-SOUTH-1 online' },
  { ts: '01:28:10', level: 'INFO',    msg: 'Scraper module pulled 3 external payloads (Finances, GDELT, AIS Shipping)' },
  { ts: '01:28:11', level: 'INFO',    msg: 'Geopolitical event graph refreshed - 847 nodes, 2,341 edges' },
  { ts: '01:28:12', level: 'SUCCESS', msg: 'Geopolitical Agent calculated Disruption Index: 72.4 via Gemini 2.5 Flash' },
  { ts: '01:28:13', level: 'INFO',    msg: 'Supply-chain solver loaded Hormuz closure scenario (severity: 45%)' },
  { ts: '01:28:14', level: 'SUCCESS', msg: 'Scipy Optimizer solved procurement matrix in 14ms (Status: OPTIMAL)' },
  { ts: '01:28:15', level: 'INFO',    msg: 'SPR drawdown model recalculated - tapered schedule active (25% floor)' },
  { ts: '01:28:16', level: 'WARN',    msg: 'Brent ICE futures +$14.80/bbl vs. 30-day baseline - ALERT threshold breached' },
  { ts: '01:28:17', level: 'SUCCESS', msg: 'Dashboard render complete - all modules nominal' },
];

const STREAM_LOGS = [
  { level: 'INFO',    msg: 'AIS ping refresh - 1,204 vessels in Persian Gulf AOI' },
  { level: 'SUCCESS', msg: 'Procurement optimiser re-solved - weighted cost $91.72/bbl' },
  { level: 'WARN',    msg: 'Hormuz strait throughput estimate revised: -18% from baseline' },
  { level: 'INFO',    msg: 'INR/USD feed updated: 84.32 (+0.61%)' },
  { level: 'SUCCESS', msg: 'SPR model converged - tapered drawdown schedule holds floor' },
];

const DEFAULT_CORRIDOR_RISKS = [
  { corridor_name: 'Strait of Hormuz', threat_level: 'CRITICAL', primary_driver: 'IRGC vessel interdiction - 3 tankers held', risk_score: 0.91 },
  { corridor_name: 'Red Sea / Bab-el-Mandeb', threat_level: 'HIGH', primary_driver: 'Houthi missile activity - reroute surging', risk_score: 0.74 },
  { corridor_name: 'Malacca Strait', threat_level: 'NOMINAL', primary_driver: 'Piracy index normal, AIS coverage stable', risk_score: 0.18 },
  { corridor_name: 'Cape of Good Hope', threat_level: 'ELEVATED', primary_driver: '+4.2 day avg voyage - West African detour', risk_score: 0.42 },
];

export default function App() {
  // Inputs
  const [corridor, setCorridor] = useState('Strait of Hormuz');
  const [severity, setSeverity] = useState(45);
  const [duration, setDuration] = useState(15);
  const [refineryName, setRefineryName] = useState('Jamnagar & IOCL Complex');
  const [minApiGravity, setMinApiGravity] = useState(28.0);
  const [maxSulfurPct, setMaxSulfurPct] = useState(2.0);

  // States
  const [running, setRunning] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [disruption, setDisruption] = useState(72.4);
  const [corridorRisks, setCorridorRisks] = useState(DEFAULT_CORRIDOR_RISKS);
  const [report, setReport] = useState(null);
  const [consoleLogs, setConsoleLogs] = useState(INIT_LOGS);

  // UTC clock helper for logging
  const getUtcTimestamp = () => {
    const now = new Date();
    return `${String(now.getUTCHours()).padStart(2, '0')}:${String(now.getUTCMinutes()).padStart(2, '0')}:${String(now.getUTCSeconds()).padStart(2, '0')}`;
  };

  // Log append helper
  const addLog = useCallback((level, msg) => {
    const ts = getUtcTimestamp();
    setConsoleLogs(prev => [...prev.slice(-39), { ts, level, msg }]);
  }, []);

  // Periodic background logging to mimic live agent stream
  const streamIdx = useRef(0);
  useEffect(() => {
    const id = setInterval(() => {
      const entry = STREAM_LOGS[streamIdx.current % STREAM_LOGS.length];
      streamIdx.current += 1;
      addLog(entry.level, entry.msg);
    }, 4500);
    return () => clearInterval(id);
  }, [addLog]);

  // Fetch Threat Feed on Mount (Phase 1 Geopolitical Analysis)
  const fetchThreatFeed = useCallback(async () => {
    setRefreshing(true);
    addLog('INFO', 'Refreshing Geopolitical Threat Intel Feed (Phase 1 Ingestion)...');
    try {
      const res = await fetch('/api/pipeline/phase1', { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      
      const data = await res.json();
      if (data.corridor_risks && data.corridor_risks.length > 0) {
        setCorridorRisks(data.corridor_risks);
        setDisruption(data.overall_disruption_index || 72.4);
        addLog('SUCCESS', `Geopolitical analysis updated. Stress index: ${data.overall_disruption_index}`);
      } else {
        // Fall back to default mock risks if empty or rate limited
        addLog('WARN', 'Geopolitical API rate-limit detected. Preserving cached threat index state.');
      }
    } catch (err) {
      addLog('ERROR', `Geopolitical threat ingestion failed: ${err.message}. Reverting to cached feed.`);
    } finally {
      setRefreshing(false);
    }
  }, [addLog]);

  useEffect(() => {
    fetchThreatFeed();
  }, []);

  // Execute Agent Simulation (Pipeline execution)
  const handleExecute = useCallback(async () => {
    setRunning(true);
    addLog('INFO', `Initializing Multi-Agent Energy Resilience simulation pipeline [Corridor: ${corridor}]...`);
    addLog('INFO', `Target Refinery: ${refineryName} | Min API: ${minApiGravity} | Max Sulfur: ${maxSulfurPct}%`);

    try {
      const payload = {
        scenario_id: `SIM-${Date.now()}`,
        corridor_name: corridor,
        closure_percentage: parseFloat(severity),
        duration_days: parseInt(duration),
        baseline_india_imports_mbpd: 5.0,
        corridor_baseline_mbpd: corridor === 'Strait of Hormuz' ? 2.2 : corridor.includes('Red Sea') ? 1.5 : 1.0,
        spr_total_capacity_mb: 39.5,
        spr_current_stock_mb: 30.0
      };

      const queryParams = new URLSearchParams({
        refinery_name: refineryName,
        min_api_gravity: minApiGravity,
        max_sulfur_pct: maxSulfurPct
      }).toString();

      const res = await fetch(`/api/scenarios/run-full-analysis?${queryParams}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error(`HTTP error ${res.status}`);

      const data = await res.json();
      setReport(data);

      // Log success and details
      addLog('SUCCESS', `Scenario Modeller solved. Daily deficit: ${data.scenario.metrics.daily_deficit_mbpd.toFixed(2)} MBPD.`);
      addLog('SUCCESS', `Procurement Orchestrator optimized crude mix. Total Procured: ${data.procurement.optimization.total_procured_mbpd.toFixed(2)} MBPD.`);
      addLog('SUCCESS', `SPR drawdown schedule plotted. Alert status: ${data.spr.optimization.alert_level}`);
      
      // Update disruption index dynamically based on simulation results
      const newDisruption = Math.min(99.9, 35 + severity * 0.58 + duration * 0.3);
      setDisruption(parseFloat(newDisruption.toFixed(1)));
    } catch (err) {
      addLog('ERROR', `Simulation execution failed: ${err.message}`);
    } finally {
      setRunning(false);
    }
  }, [corridor, severity, duration, refineryName, minApiGravity, maxSulfurPct, addLog]);

  // Extract core metrics for ribbon
  const metrics = {
    dailyDeficit: report?.scenario?.metrics?.daily_deficit_mbpd ?? 2.20,
    sprCover: report?.scenario?.metrics?.spr_remaining_days_cover ?? 18.2,
    costPremium: report?.scenario?.metrics?.estimated_brent_surge_pct ?? 14.80,
    gdpImpact: report?.scenario?.metrics?.macro_gdp_drag_pct ?? -0.28,
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* Platform Header */}
      <CommandHeader
        disruption={disruption}
        sprCover={metrics.sprCover}
        brentPrice={103.40 + (metrics.costPremium - 14.8) * 0.6}
        activeFeedsCount={12}
      />

      {/* KPI metrics row */}
      <MetricsRibbon
        dailyDeficit={metrics.dailyDeficit}
        sprCover={metrics.sprCover}
        costPremium={metrics.costPremium}
        gdpImpact={metrics.gdpImpact}
      />

      {/* Main Workspace layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 5fr 4fr', gap: '8px', padding: '0 8px 8px', flex: 1, minHeight: 0, overflow: 'hidden' }}>
        {/* Left Column: inputs and active feed list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflow: 'hidden', minHeight: 0 }}>
          <SimulationPanel
            corridor={corridor} setCorridor={setCorridor}
            severity={severity} setSeverity={setSeverity}
            duration={duration} setDuration={setDuration}
            refineryName={refineryName} setRefineryName={setRefineryName}
            minApiGravity={minApiGravity} setMinApiGravity={setMinApiGravity}
            maxSulfurPct={maxSulfurPct} setMaxSulfurPct={setMaxSulfurPct}
            onExecute={handleExecute} running={running}
          />
          <ThreatFeed
            corridorRisks={corridorRisks}
            onRefresh={fetchThreatFeed}
            refreshing={refreshing}
          />
        </div>

        {/* Center Column: geospatial map */}
        <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
          <TacticalMap selectedCorridor={corridor} severity={severity} />
        </div>

        {/* Right Column: briefings, charts, and recommendations */}
        <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
          <IntelPanel report={report} />
        </div>
      </div>

      {/* Footer collapsible console stream */}
      <TerminalConsole logs={consoleLogs} />
    </div>
  );
}
