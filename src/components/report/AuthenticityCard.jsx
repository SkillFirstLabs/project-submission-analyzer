import React from 'react';
import { AuthenticityRadar } from '../charts/ReportGauges';
import { ShieldCheck, SearchCode, EyeOff, Info, ShieldAlert } from 'lucide-react';

const AuthenticityCard = ({ template }) => {
  if (!template) return null;

  const { authenticityScore, authenticityBreakdown, indicators } = template;

  return (
    <div className="card-gradient rounded-2xl p-6 border border-dark-600/30 flex flex-col gap-6">
      {/* Title block */}
      <div className="flex justify-between items-center border-b border-dark-600/20 pb-4">
        <div>
          <h3 className="text-lg font-bold text-white font-sans flex items-center gap-2 select-none">
            <ShieldCheck className="w-5 h-5 text-brand-400" />
            Project Authenticity Summary
          </h3>
          <p className="text-xs text-dark-300 mt-1 select-none">
            Detailed validation metrics comparing original implementations to template codebases.
          </p>
        </div>
        <div className="bg-brand-500/10 border border-brand-500/25 rounded-xl px-4 py-2 text-center select-none">
          <span className="text-[10px] text-brand-300 block font-bold uppercase tracking-wider">Score</span>
          <span className="text-2xl font-black text-white font-mono">{authenticityScore}%</span>
        </div>
      </div>

      {/* Split details layout: chart on left, scores/verdict on right */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-center">
        {/* Radar Map */}
        <div className="flex justify-center bg-dark-950/20 rounded-xl p-3 border border-dark-600/10">
          <AuthenticityRadar breakdown={authenticityBreakdown} />
        </div>

        {/* Text Breakdown */}
        <div className="flex flex-col gap-4">
          <h4 className="text-xs font-bold text-dark-400 uppercase tracking-widest select-none">
            Capability Index
          </h4>
          
          <div className="flex flex-col gap-3">
            {Object.entries(authenticityBreakdown).map(([key, value]) => (
              <div key={key} className="flex flex-col gap-1">
                <div className="flex justify-between text-xs font-sans">
                  <span className="text-dark-200 capitalize">{key.replace(/([A-Z])/g, ' $1')}</span>
                  <span className="font-semibold text-white font-mono">{value}%</span>
                </div>
                <div className="w-full h-1.5 bg-dark-950 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-brand-500/80 rounded-full" 
                    style={{ width: `${value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Real / Missing / Boilerplate Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 border-t border-dark-600/20 pt-6 mt-2 select-text">
        {/* Real Indicators */}
        <div className="rounded-xl border border-emerald-500/15 bg-emerald-500/5 p-4">
          <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-1.5 select-none">
            <SearchCode className="w-4 h-4" />
            Real Indicators
          </h4>
          <ul className="flex flex-col gap-2.5 text-xs text-dark-200 list-disc list-inside">
            {indicators.real.map((item, idx) => (
              <li key={idx} className="leading-relaxed">{item}</li>
            ))}
          </ul>
        </div>

        {/* Missing Indicators */}
        <div className="rounded-xl border border-amber-500/15 bg-amber-500/5 p-4">
          <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-3 flex items-center gap-1.5 select-none">
            <EyeOff className="w-4 h-4" />
            Missing Indicators
          </h4>
          <ul className="flex flex-col gap-2.5 text-xs text-dark-200 list-disc list-inside">
            {indicators.missing.map((item, idx) => (
              <li key={idx} className="leading-relaxed">{item}</li>
            ))}
          </ul>
        </div>

        {/* Boilerplate Indicators */}
        <div className="rounded-xl border border-rose-500/15 bg-rose-500/5 p-4">
          <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider mb-3 flex items-center gap-1.5 select-none">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            Superficial Indicators
          </h4>
          <ul className="flex flex-col gap-2.5 text-xs text-dark-200 list-disc list-inside">
            {indicators.superficial.map((item, idx) => (
              <li key={idx} className="leading-relaxed">{item}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* AI Verdict summary */}
      <div className="rounded-xl bg-dark-950 p-4 border border-dark-600/40 select-text">
        <h4 className="text-xs font-bold text-dark-300 uppercase tracking-wider mb-2 flex items-center gap-1.5 select-none">
          <Info className="w-3.5 h-3.5 text-brand-400" />
          AI Verdict Details
        </h4>
        <p className="text-xs text-dark-200 leading-relaxed font-sans">
          {indicators.verdict}
        </p>
      </div>
    </div>
  );
};

export default AuthenticityCard;
