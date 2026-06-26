import React, { useEffect, useRef } from 'react';
import { Terminal, ShieldCheck, Cpu, Code2, Layers, AlertCircle } from 'lucide-react';

const LiveFindings = ({ progress, logs, filesCount, projectTemplate }) => {
  const logTerminalEndRef = useRef(null);

  // Auto scroll console logs to bottom
  useEffect(() => {
    logTerminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Fallback info if template is not loaded yet
  const techStack = projectTemplate?.techStack || { frontend: [], backend: [] };
  const dependencies = projectTemplate?.dependencies || [];
  const architecture = projectTemplate?.architecture || 'Pending Detection';
  const confidence = projectTemplate?.confidence || 0;
  const confidenceLabel = projectTemplate?.confidenceLabel || 'Calculating';

  const allTechs = [...(techStack.frontend || []), ...(techStack.backend || [])];

  return (
    <div className="w-full flex flex-col gap-6">
      {/* Streaming Console Logs */}
      <div>
        <h3 className="text-xs font-bold text-dark-400 tracking-widest uppercase mb-2 select-none flex items-center gap-1.5">
          <Terminal className="w-3.5 h-3.5" />
          Live Diagnostics Console
        </h3>
        
        <div className="w-full h-44 rounded-xl border border-dark-600/50 bg-dark-950 p-4 font-mono text-[11px] leading-relaxed text-emerald-400 overflow-y-auto shadow-inner select-text">
          <div className="flex flex-col gap-1">
            {logs.map((log, index) => (
              <div key={index} className="flex gap-2 items-start">
                <span className="text-dark-400 shrink-0 select-none">&gt;</span>
                <span>{log}</span>
              </div>
            ))}
            {progress < 100 && (
              <div className="flex gap-2 items-center text-brand-400 animate-pulse mt-0.5">
                <span className="text-dark-400 shrink-0 select-none">&gt;</span>
                <span>Running analytical processes...</span>
                <span className="w-1.5 h-3.5 bg-brand-400 inline-block animate-blink" />
              </div>
            )}
            <div ref={logTerminalEndRef} />
          </div>
        </div>
      </div>

      {/* Stats Dashboard Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {/* Files Analyzed */}
        <div className="p-4 rounded-xl border border-dark-600/20 bg-dark-900/30 flex flex-col justify-between">
          <span className="text-[10px] font-bold text-dark-400 uppercase tracking-wider mb-2 block">
            Files Analyzed
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white tracking-tight">
              {filesCount}
            </span>
            <span className="text-xs text-dark-400 font-mono">items</span>
          </div>
        </div>

        {/* Confidence Score */}
        <div className="p-4 rounded-xl border border-dark-600/20 bg-dark-900/30 flex flex-col justify-between">
          <span className="text-[10px] font-bold text-dark-400 uppercase tracking-wider mb-2 block">
            Confidence
          </span>
          <div className="flex flex-col">
            <span className="text-2xl font-bold text-brand-400 tracking-tight flex items-center gap-1.5">
              {progress < 80 ? 'Calculating...' : `${confidence}%`}
            </span>
            {progress >= 80 && (
              <span className="text-[10px] text-emerald-400 font-medium font-sans flex items-center gap-0.5 mt-0.5">
                <ShieldCheck className="w-3 h-3" />
                {confidenceLabel}
              </span>
            )}
          </div>
        </div>

        {/* Architecture */}
        <div className="p-4 rounded-xl border border-dark-600/20 bg-dark-900/30 flex flex-col justify-between col-span-2 md:col-span-1">
          <span className="text-[10px] font-bold text-dark-400 uppercase tracking-wider mb-2 block">
            Architecture Detected
          </span>
          <div>
            <span className="text-sm font-bold text-white truncate block">
              {progress < 70 ? 'Detecting...' : architecture}
            </span>
            <span className="text-[9px] text-dark-400 uppercase font-bold tracking-wider mt-1 block">
              Pattern Model
            </span>
          </div>
        </div>
      </div>

      {/* Tech and Dependencies Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Technologies card */}
        <div className="p-5 rounded-xl border border-dark-600/30 bg-dark-900/50">
          <h4 className="text-xs font-bold text-dark-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Code2 className="w-4 h-4 text-brand-400" />
            Detected Technologies
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {progress < 60 ? (
              <span className="text-xs text-dark-400 italic">Scanning files...</span>
            ) : allTechs.length > 0 ? (
              allTechs.map((tech) => (
                <span
                  key={tech}
                  className="px-2.5 py-1 rounded bg-dark-800 border border-dark-600 text-xs font-medium text-white"
                >
                  {tech}
                </span>
              ))
            ) : (
              <span className="text-xs text-dark-400">None detected</span>
            )}
          </div>
        </div>

        {/* Dependencies card */}
        <div className="p-5 rounded-xl border border-dark-600/30 bg-dark-900/50">
          <h4 className="text-xs font-bold text-dark-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-brand-400" />
            Core Dependencies
          </h4>
          <div className="flex flex-col gap-1.5 max-h-24 overflow-y-auto pr-1">
            {progress < 50 ? (
              <span className="text-xs text-dark-400 italic">Reading package.json...</span>
            ) : dependencies.length > 0 ? (
              dependencies.slice(0, 4).map((dep) => (
                <div key={dep.name} className="flex justify-between items-center text-xs">
                  <span className="font-mono text-dark-200">{dep.name}</span>
                  <span className="text-dark-400 text-[10px] font-mono">{dep.version}</span>
                </div>
              ))
            ) : (
              <span className="text-xs text-dark-400">No project manifests found</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveFindings;
