import React from 'react';
import { useProject } from '../../contexts/ProjectContext';
import Card from '../../components/common/Card';
import VivaQuestionCard from '../../components/viva/VivaQuestionCard';
import LiveAnalyticsSidebar from '../../components/viva/LiveAnalyticsSidebar';
import { ResponsiveContainer, RadialBarChart, RadialBar, Cell } from 'recharts';
import { ShieldCheck, Award } from 'lucide-react';

const VivaPage = () => {
  const {
    projectDetails,
    selectedProjectTemplate,
    vivaQuestions,
    currentQuestionIdx,
    vivaAnswers,
    vivaGrades,
    revealedExpected,
    countdownTimer,
    vivaScores,
    suspicionLogs,
    vivaCompletedCount,
    saveAnswerDraft,
    revealExpected,
    gradeAnswer,
    skipQuestion,
    generateReport
  } = useProject();

  const currentQuestion = vivaQuestions[currentQuestionIdx];
  const isVivaFinished = vivaCompletedCount >= vivaQuestions.length;

  // Mini gauge for header skill confidence circular display
  const renderMiniConfidenceGauge = (value) => {
    const data = [
      { name: 'Value', value: value, fill: '#818cf8' },
      { name: 'Back', value: 100 - value, fill: '#1e293b' }
    ];

    return (
      <div className="flex items-center gap-3 bg-dark-900 border border-dark-600/35 rounded-xl px-4 py-2 flex-shrink-0">
        <div className="relative w-12 h-12 flex items-center justify-center">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart
              cx="50%"
              cy="50%"
              innerRadius="70%"
              outerRadius="95%"
              barSize={4}
              data={data}
              startAngle={90}
              endAngle={-270}
            >
              <RadialBar minAngle={15} background clockWise dataKey="value" cornerRadius={10}>
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </RadialBar>
            </RadialBarChart>
          </ResponsiveContainer>
          <span className="absolute text-xs font-black text-white font-mono">{value}%</span>
        </div>
        <div className="flex flex-col text-left select-none">
          <span className="text-[9px] font-bold text-dark-400 uppercase tracking-widest leading-none mb-0.5">Skill Confidence</span>
          <span className="text-xs font-bold text-brand-300">High Probability</span>
        </div>
      </div>
    );
  };

  return (
    <div className="w-full flex flex-col gap-8 py-6 select-none max-w-6xl mx-auto">
      {/* Title Header with Widget Counters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-2">
        <div className="text-left max-w-xl">
          <span className="text-xs font-bold font-sans tracking-wide text-brand-300 uppercase select-none">
            Step 3 of 4: Viva Mode
          </span>
          <h1 className="text-3xl md:text-4xl font-extrabold font-sans text-white tracking-tight leading-tight mt-1 mb-2">
            Project: {projectDetails.title || selectedProjectTemplate?.rawTitle || 'Nexus Core Migration'}
          </h1>
          <p className="text-xs md:text-sm text-dark-300 font-sans leading-relaxed select-text">
            Live evaluation room. Validate technical depth and uncover potential AI assistance artifacts through targeted questioning.
          </p>
        </div>

        {/* Authenticity and Confidence header widgets (Screen 3 style) */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Authenticity Widget */}
          <div className="bg-dark-900 border border-dark-600/35 rounded-xl px-5 py-2 flex flex-col items-center justify-center flex-shrink-0 select-none">
            <span className="text-[9px] font-bold text-dark-400 uppercase tracking-widest mb-0.5 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-brand-400" />
              Authenticity Score
            </span>
            <span className="text-xl font-black text-white font-mono">{selectedProjectTemplate?.authenticityScore || 78}%</span>
          </div>

          {/* Skill Confidence Circle Widget */}
          {renderMiniConfidenceGauge(selectedProjectTemplate?.confidence || 85)}
        </div>
      </div>

      {/* Centered Single Column Layout */}
      <div className="max-w-3xl mx-auto w-full flex flex-col gap-6">
        {!isVivaFinished && currentQuestion ? (
          <VivaQuestionCard
            question={currentQuestion}
            currentIndex={currentQuestionIdx}
            totalQuestions={vivaQuestions.length}
            timer={countdownTimer}
            userAnswer={vivaAnswers[currentQuestion.id] || ''}
            isRevealed={!!revealedExpected[currentQuestion.id]}
            onAnswerChange={saveAnswerDraft}
            onReveal={revealExpected}
            onGrade={gradeAnswer}
            onSkip={skipQuestion}
          />
        ) : (
          <Card className="text-center py-16 px-6 border-brand-500/25 bg-brand-500/5 select-none">
            <Award className="w-16 h-16 text-brand-400 mx-auto mb-4 animate-pulse-ring" />
            <h2 className="text-2xl font-bold text-white mb-2">Viva Session Completed</h2>
            <p className="text-sm text-dark-300 max-w-md mx-auto mb-6">
              All questions have been evaluated. Please proceed to the final step to view the complete diagnostics report.
            </p>
            <button
              type="button"
              onClick={generateReport}
              className="px-6 py-3 rounded-xl text-xs font-bold tracking-wider text-white bg-brand-500 hover:bg-brand-600 hover:glow-button-shadow transition-all duration-300"
            >
              Generate Final Report
            </button>
          </Card>
        )}
      </div>
    </div>
  );
};

export default VivaPage;
