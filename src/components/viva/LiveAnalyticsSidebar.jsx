import React from 'react';
import { BarChart3, AlertTriangle, CheckSquare, Award, ArrowRight } from 'lucide-react';

const LiveAnalyticsSidebar = ({
  scores,
  suspicionLogs = [],
  completedCount,
  totalQuestions,
  onGenerateReport,
  isVivaFinished
}) => {
  // Get the most recent suspicion indicator
  const latestSuspicion = suspicionLogs[suspicionLogs.length - 1];

  return (
    <div className="w-full flex flex-col gap-5 select-none">
      {/* 1. Live Analytics Panel */}
      <div className="card-gradient rounded-2xl p-6 border border-dark-600/30">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-5 flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-brand-400" />
          Live Analytics
        </h3>

        <div className="flex flex-col gap-4">
          {/* Technical Depth */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between items-center text-xs">
              <span className="text-dark-300 font-medium">Technical Depth</span>
              <span className="font-semibold text-white font-mono">{scores.technical}/10</span>
            </div>
            <div className="w-full h-2 bg-dark-950 rounded-full overflow-hidden">
              <div 
                className="h-full bg-brand-500 rounded-full transition-all duration-500" 
                style={{ width: `${scores.technical * 10}%` }}
              />
            </div>
          </div>

          {/* Communication */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between items-center text-xs">
              <span className="text-dark-300 font-medium">Communication</span>
              <span className="font-semibold text-white font-mono">{scores.communication}/10</span>
            </div>
            <div className="w-full h-2 bg-dark-950 rounded-full overflow-hidden">
              <div 
                className="h-full bg-indigo-400 rounded-full transition-all duration-500" 
                style={{ width: `${scores.communication * 10}%` }}
              />
            </div>
          </div>

          {/* Confidence */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between items-center text-xs">
              <span className="text-dark-300 font-medium">Confidence</span>
              <span className="font-semibold text-white font-mono">{scores.confidence}/10</span>
            </div>
            <div className="w-full h-2 bg-dark-950 rounded-full overflow-hidden">
              <div 
                className="h-full bg-sky-400 rounded-full transition-all duration-500" 
                style={{ width: `${scores.confidence * 10}%` }}
              />
            </div>
          </div>
        </div>

        {/* Suspicion Indicator Box */}
        <div className="mt-6 pt-5 border-t border-dark-600/30">
          <div className="rounded-xl bg-amber-500/5 border border-amber-500/25 p-4 flex gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
            <div className="flex flex-col gap-0.5">
              <span className="text-[10px] font-bold text-amber-400 uppercase tracking-widest">
                Suspicion Indicator
              </span>
              <p className="text-xs text-dark-300 leading-normal select-text">
                {latestSuspicion || "Candidate behavior matches expected profile. No anomalies detected."}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Session Progress Grid */}
      <div className="card-gradient rounded-2xl p-6 border border-dark-600/30">
        <h3 className="text-xs font-bold text-dark-400 uppercase tracking-widest mb-4">
          Session Progress
        </h3>

        <div className="grid grid-cols-2 gap-4">
          {/* Completed Box */}
          <div className="bg-dark-950/60 rounded-xl p-4 border border-dark-600/20 text-center">
            <span className="text-2xl font-bold text-white block font-mono">
              {completedCount}
            </span>
            <span className="text-[9px] font-bold text-dark-400 uppercase tracking-wider mt-1 block">
              Completed
            </span>
          </div>

          {/* Average Score Box */}
          <div className="bg-dark-950/60 rounded-xl p-4 border border-dark-600/20 text-center">
            <span className="text-2xl font-bold text-white block font-mono">
              {scores.avgScore}
            </span>
            <span className="text-[9px] font-bold text-dark-400 uppercase tracking-wider mt-1 block">
              Avg Score
            </span>
          </div>
        </div>
      </div>

      {/* 3. Action Navigation Trigger */}
      <button
        type="button"
        onClick={onGenerateReport}
        disabled={!isVivaFinished}
        className={`w-full py-4 px-6 rounded-xl border flex items-center justify-between transition-all duration-300 ${
          isVivaFinished
            ? 'bg-dark-950 border-brand-500 hover:bg-brand-500/10 text-white font-semibold cursor-pointer'
            : 'bg-dark-950/40 border-dark-600/40 text-dark-400 cursor-not-allowed'
        }`}
      >
        <span className="text-sm font-sans tracking-wide">
          {isVivaFinished ? 'Generate Final Report' : 'Complete All Questions to Finish'}
        </span>
        <ArrowRight className={`w-4 h-4 shrink-0 transition-transform duration-300 ${isVivaFinished ? 'text-brand-400 group-hover:translate-x-1' : 'text-dark-500'}`} />
      </button>
    </div>
  );
};

export default LiveAnalyticsSidebar;
