import React, { useEffect } from 'react';
import { useProject } from '../../contexts/ProjectContext';
import Card from '../../components/common/Card';
import PipelineProgress from '../../components/analysis/PipelineProgress';
import LiveFindings from '../../components/analysis/LiveFindings';
import { ArrowRight, Loader2, Award } from 'lucide-react';

const AnalysisPage = () => {
  const {
    analysisProgress,
    analysisLogs,
    isAnalysisComplete,
    filesAnalyzed,
    selectedProjectTemplate,
    proceedToViva
  } = useProject();

  // Determine active step index in pipeline (0 to 8 based on progress ranges)
  const getActiveStepIndex = () => {
    if (analysisProgress >= 100) return 9; // All complete
    if (analysisProgress >= 90) return 8; // Preparing Evaluation
    if (analysisProgress >= 80) return 7; // Generating Viva
    if (analysisProgress >= 70) return 6; // Authenticity Analysis
    if (analysisProgress >= 60) return 5; // Verifying Outcomes
    if (analysisProgress >= 55) return 4; // Detecting Skills
    if (analysisProgress >= 40) return 3; // Building Evidence
    if (analysisProgress >= 25) return 2; // Reading Code
    if (analysisProgress >= 10) return 1; // Extracting Files
    return 0; // ZIP Uploaded
  };

  const activeIndex = getActiveStepIndex();

  return (
    <div className="w-full flex flex-col gap-8 py-6 select-none max-w-5xl mx-auto">
      {/* Title Header */}
      <div className="text-center md:text-left select-none">
        <span className="text-xs font-bold font-sans tracking-wide text-brand-300 uppercase">
          Step 2 of 4: Deep Scan
        </span>
        <h1 className="text-3xl md:text-4xl font-extrabold font-sans text-white tracking-tight leading-tight mt-1 mb-2">
          AI Extraction & Analysis
        </h1>
        <p className="text-xs md:text-sm text-dark-300 font-sans max-w-2xl leading-relaxed">
          Running structural parsing, dependency map construction, and outcome correlation vectors.
        </p>
      </div>

      {/* Global Progress Dashboard Bar */}
      <Card className="w-full py-5 px-6 flex flex-col md:flex-row md:items-center justify-between gap-4 border-brand-500/25 bg-brand-500/5">
        <div className="flex-grow">
          <div className="flex justify-between text-xs font-bold text-dark-300 tracking-wider uppercase mb-2">
            <span>Overall Progress</span>
            <span className="font-mono text-white text-sm">{analysisProgress}%</span>
          </div>
          <div className="w-full h-3 bg-dark-950 rounded-full overflow-hidden p-0.5 border border-dark-600/30">
            <div
              className="h-full bg-gradient-to-right bg-brand-500 rounded-full transition-all duration-300 animate-progress-loading"
              style={{ width: `${analysisProgress}%` }}
            />
          </div>
        </div>

        {/* Action Button shown when completed */}
        <div className="shrink-0 flex items-center justify-end select-none">
          {isAnalysisComplete ? (
            <button
              onClick={proceedToViva}
              className="px-6 py-3 rounded-xl text-xs font-bold tracking-wider text-white bg-brand-500 hover:bg-brand-600 hover:glow-button-shadow transition-all duration-300 flex items-center gap-2 animate-bounce-slow"
            >
              Start Interactive Viva
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <div className="flex items-center gap-2.5 text-dark-300 font-sans text-xs bg-dark-900 border border-dark-600/30 px-4.5 py-3.5 rounded-xl font-medium">
              <Loader2 className="w-4 h-4 text-brand-400 animate-spin" />
              Executing pipeline routines...
            </div>
          )}
        </div>
      </Card>

      {/* Split layout: Pipeline flow on left, Live metrics dashboard on right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column - Pipeline Progress Steps */}
        <div className="lg:col-span-5 w-full">
          <Card className="p-6">
            <PipelineProgress activeIndex={activeIndex} progress={analysisProgress} />
          </Card>
        </div>

        {/* Right Column - Live findings statistics */}
        <div className="lg:col-span-7 w-full">
          <Card className="p-6">
            <LiveFindings
              progress={analysisProgress}
              logs={analysisLogs}
              filesCount={filesAnalyzed}
              projectTemplate={selectedProjectTemplate}
            />
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AnalysisPage;
