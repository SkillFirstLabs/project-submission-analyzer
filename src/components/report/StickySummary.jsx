import React from 'react';
import { OverallScoreGauge } from '../charts/ReportGauges';
import { Download, FileJson, RefreshCw, Award, CheckCircle2, ShieldAlert } from 'lucide-react';

const StickySummary = ({ metrics, onDownloadJson, onDownloadReport, onReset }) => {
  const getBadgeStyles = (classification) => {
    switch (classification) {
      case 'Production Ready':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25';
      case 'Mostly Complete':
        return 'bg-brand-500/10 text-brand-300 border-brand-500/25';
      case 'Frontend Heavy':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/25';
      case 'Superficial':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/25';
      default:
        return 'bg-dark-800 text-dark-300 border-dark-600/30';
    }
  };

  return (
    <div className="w-full bg-dark-900 border border-dark-600/30 rounded-2xl p-6 flex flex-col gap-6 sticky top-24 select-none">
      {/* Overall Score Dial */}
      <div className="flex justify-center py-2">
        <OverallScoreGauge score={metrics.overallScore} />
      </div>

      {/* Subscores Grid */}
      <div className="grid grid-cols-2 gap-3 border-t border-b border-dark-600/20 py-4">
        <div className="bg-dark-950/40 rounded-xl p-3 border border-dark-600/10 text-center">
          <span className="text-xs text-dark-300 block mb-0.5">Authenticity</span>
          <span className="text-lg font-bold text-white font-mono">{metrics.authenticityScore}%</span>
        </div>
        <div className="bg-dark-950/40 rounded-xl p-3 border border-dark-600/10 text-center">
          <span className="text-xs text-dark-300 block mb-0.5">Viva Score</span>
          <span className="text-lg font-bold text-white font-mono">{metrics.vivaScore}%</span>
        </div>
      </div>

      {/* Final Verdict Details */}
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <span className="text-[10px] font-bold text-dark-400 uppercase tracking-widest">
            AI Verdict
          </span>
          <div className={`px-4 py-2 border rounded-lg text-center text-sm font-bold tracking-wide ${getBadgeStyles(metrics.classification)}`}>
            {metrics.classification}
          </div>
        </div>

        <div className="flex items-center justify-between text-xs pt-1">
          <span className="text-dark-300">Confidence:</span>
          <span className="font-semibold text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            {metrics.confidenceLabel}
          </span>
        </div>
      </div>

      {/* Export & Command Triggers */}
      <div className="flex flex-col gap-2.5 pt-4 border-t border-dark-600/20">
        <button
          type="button"
          onClick={onDownloadReport}
          className="w-full py-2.5 px-4 rounded-lg bg-brand-500 hover:bg-brand-600 hover:glow-button-shadow text-white font-semibold text-xs flex items-center justify-center gap-2 transition-all duration-300"
        >
          <Download className="w-4 h-4" />
          Download PDF Report
        </button>

        <button
          type="button"
          onClick={onDownloadJson}
          className="w-full py-2.5 px-4 rounded-lg bg-dark-950 border border-dark-600 hover:bg-dark-800 text-dark-200 font-semibold text-xs flex items-center justify-center gap-2 transition-all duration-300"
        >
          <FileJson className="w-4 h-4 text-dark-400" />
          Export JSON Schema
        </button>

        <button
          type="button"
          onClick={onReset}
          className="w-full py-2.5 px-4 rounded-lg border border-dashed border-dark-500 hover:border-brand-500 hover:bg-brand-500/5 text-dark-300 hover:text-white font-semibold text-xs flex items-center justify-center gap-2 transition-all duration-300 mt-2"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Analyze Another Project
        </button>
      </div>
    </div>
  );
};

export default StickySummary;
