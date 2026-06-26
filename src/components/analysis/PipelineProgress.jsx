import React from 'react';
import { Check, Loader2, Circle } from 'lucide-react';

const PipelineProgress = ({ activeIndex, progress }) => {
  const steps = [
    'ZIP Uploaded',
    'Extracting Files',
    'Reading Code',
    'Building Evidence',
    'Detecting Skills',
    'Verifying Outcomes',
    'Project Authenticity Analysis',
    'Generating Viva',
    'Preparing Evaluation'
  ];

  return (
    <div className="w-full flex flex-col gap-3.5">
      <h3 className="text-xs font-bold text-dark-400 tracking-widest uppercase mb-2 select-none">
        Analysis Pipeline
      </h3>
      
      <div className="flex flex-col gap-2.5">
        {steps.map((step, idx) => {
          const isCompleted = idx < activeIndex;
          const isCurrent = idx === activeIndex;
          const isPending = idx > activeIndex;

          return (
            <div
              key={step}
              className={`flex items-center gap-3.5 px-4 py-2.5 rounded-lg border transition-all duration-300 ${
                isCurrent
                  ? 'bg-brand-500/5 border-brand-500/30 shadow-[0_0_15px_rgba(92,79,229,0.05)]'
                  : isCompleted
                    ? 'bg-dark-900/40 border-dark-600/20'
                    : 'bg-dark-950/20 border-transparent opacity-40'
              }`}
            >
              {/* Icon Status */}
              <div className="flex-shrink-0">
                {isCompleted ? (
                  <div className="w-5 h-5 rounded-full bg-emerald-500/20 border border-emerald-500 flex items-center justify-center text-emerald-400">
                    <Check className="w-3 h-3" />
                  </div>
                ) : isCurrent ? (
                  <div className="w-5 h-5 rounded-full bg-brand-500/20 border border-brand-500 flex items-center justify-center text-brand-400 animate-spin">
                    <Loader2 className="w-3 h-3" />
                  </div>
                ) : (
                  <div className="w-5 h-5 rounded-full border border-dark-600 flex items-center justify-center text-dark-400">
                    <Circle className="w-2 h-2 fill-current text-transparent" />
                  </div>
                )}
              </div>

              {/* Label */}
              <span
                className={`text-sm font-sans font-medium transition-colors duration-300 ${
                  isCurrent
                    ? 'text-white font-bold'
                    : isCompleted
                      ? 'text-dark-300'
                      : 'text-dark-400'
                }`}
              >
                {step}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PipelineProgress;
