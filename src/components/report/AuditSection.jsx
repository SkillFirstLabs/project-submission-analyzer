import React from 'react';
import { 
  FileCheck2, 
  ShieldAlert, 
  Workflow, 
  Sparkles, 
  Construction, 
  Lightbulb, 
  ThumbsDown 
} from 'lucide-react';

const AuditSection = ({ audit }) => {
  if (!audit) return null;

  return (
    <div className="card-gradient rounded-2xl p-6 border border-dark-600/30 flex flex-col gap-6 select-text">
      {/* Title */}
      <div className="border-b border-dark-600/20 pb-4 select-none">
        <h3 className="text-lg font-bold text-white font-sans flex items-center gap-2">
          <FileCheck2 className="w-5 h-5 text-brand-400" />
          Diagnostic Code Audit
        </h3>
        <p className="text-xs text-dark-300 mt-1">
          Detailed inspection notes regarding security vectors, technical debt, and layout heuristics.
        </p>
      </div>

      {/* Grid Layout: Strengths & Weaknesses */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Strengths */}
        <div className="p-5 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
          <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-3 flex items-center gap-1.5 select-none">
            <Sparkles className="w-4 h-4" />
            Core Strengths
          </h4>
          <ul className="list-disc list-inside text-xs text-dark-200 flex flex-col gap-2.5">
            {audit.strengths.map((str, idx) => (
              <li key={idx} className="leading-relaxed">{str}</li>
            ))}
          </ul>
        </div>

        {/* Weaknesses */}
        <div className="p-5 rounded-xl bg-rose-500/5 border border-rose-500/10">
          <h4 className="text-xs font-bold text-rose-400 uppercase tracking-widest mb-3 flex items-center gap-1.5 select-none">
            <ThumbsDown className="w-4 h-4 text-rose-400" />
            Potential Weaknesses
          </h4>
          <ul className="list-disc list-inside text-xs text-dark-200 flex flex-col gap-2.5">
            {audit.weaknesses.map((weak, idx) => (
              <li key={idx} className="leading-relaxed">{weak}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Deep-Dive Categories Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Security Notes */}
        <div className="p-5 rounded-xl bg-dark-950 border border-dark-600/35 flex flex-col gap-2">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 select-none">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            Security & Vuln Assessment
          </h4>
          <p className="text-xs text-dark-300 leading-relaxed font-sans mt-1">
            {audit.security}
          </p>
        </div>

        {/* Architecture Notes */}
        <div className="p-5 rounded-xl bg-dark-950 border border-dark-600/35 flex flex-col gap-2">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 select-none">
            <Workflow className="w-4 h-4 text-brand-400" />
            Architecture & Layout Integrity
          </h4>
          <p className="text-xs text-dark-300 leading-relaxed font-sans mt-1">
            {audit.architecture}
          </p>
        </div>

        {/* Code Smells */}
        <div className="p-5 rounded-xl bg-dark-950 border border-dark-600/35 flex flex-col gap-2">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 select-none">
            <svg className="w-4 h-4 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
            Code Smells
          </h4>
          <p className="text-xs text-dark-300 leading-relaxed font-sans mt-1">
            {audit.codeSmells}
          </p>
        </div>

        {/* Technical Debt */}
        <div className="p-5 rounded-xl bg-dark-950 border border-dark-600/35 flex flex-col gap-2">
          <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 select-none">
            <Construction className="w-4 h-4 text-amber-400" />
            Technical Debt Indexes
          </h4>
          <p className="text-xs text-dark-300 leading-relaxed font-sans mt-1">
            {audit.technicalDebt}
          </p>
        </div>
      </div>

      {/* Recommendations Box */}
      <div className="p-5 rounded-xl bg-brand-500/5 border border-brand-500/20 mt-2">
        <h4 className="text-xs font-bold text-brand-300 uppercase tracking-widest mb-2 flex items-center gap-1.5 select-none">
          <Lightbulb className="w-4 h-4 text-yellow-400" />
          Refactoring & Optimization Heuristics
        </h4>
        <p className="text-xs text-dark-200 leading-relaxed font-sans">
          {audit.recommendations}
        </p>
      </div>
    </div>
  );
};

export default AuditSection;
