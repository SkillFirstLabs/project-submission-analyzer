import React, { useState, useEffect } from 'react';
import { HelpCircle, Clock, AlertTriangle, CheckCircle2, XCircle, ArrowRight, Eye, ThumbsUp, ThumbsDown, Minus } from 'lucide-react';

const VivaQuestionCard = ({
  question,
  currentIndex,
  totalQuestions,
  timer,
  userAnswer = '',
  isRevealed = false,
  onAnswerChange,
  onReveal,
  onGrade,
  onSkip
}) => {
  const [answerDraft, setAnswerDraft] = useState(userAnswer);

  // Sync draft answer state when question changes
  useEffect(() => {
    setAnswerDraft(userAnswer || '');
  }, [question, userAnswer]);

  const handleTextChange = (e) => {
    setAnswerDraft(e.target.value);
    onAnswerChange(question.id, e.target.value);
  };

  // Convert seconds to MM:SS format
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="card-gradient rounded-2xl p-8 border border-dark-600/35 relative flex flex-col gap-6 w-full">
      {/* Top Header Row */}
      <div className="flex items-center justify-between flex-wrap gap-4 border-b border-dark-600/30 pb-4 select-none">
        <div className="flex items-center gap-2.5">
          <span className="px-3 py-1 text-xs font-bold font-sans tracking-wide text-brand-300 bg-brand-500/10 border border-brand-500/20 rounded-full flex items-center gap-1">
            <HelpCircle className="w-3.5 h-3.5" />
            Question {currentIndex + 1} / {totalQuestions}
          </span>
          <span className="px-3 py-1 text-xs font-medium font-sans text-dark-300 bg-dark-800 border border-dark-600/30 rounded-full">
            Difficulty: {question.difficulty}
          </span>
          <span className="px-3 py-1 text-xs font-medium font-sans text-brand-400 bg-brand-500/5 border border-brand-500/10 rounded-full">
            Type: {question.type}
          </span>
        </div>

        {/* Timer countdown */}
        <div className="flex items-center gap-2 font-mono text-sm text-dark-200">
          <Clock className="w-4 h-4 text-dark-300" />
          <span>{formatTime(timer)}</span>
        </div>
      </div>

      {/* Question Text */}
      <div>
        <h2 className="text-xl md:text-2xl font-bold font-sans text-white leading-relaxed tracking-tight select-text">
          "{question.question}"
        </h2>
      </div>

      {/* Answer Area */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-bold text-dark-400 uppercase tracking-widest select-none">
          Your Answer
        </label>
        <textarea
          value={answerDraft}
          onChange={handleTextChange}
          placeholder="Formulate your detailed answer here based on the codebase implementation..."
          className="w-full h-32 px-4 py-3 text-sm font-sans rounded-xl bg-dark-950 border border-dark-600 text-white placeholder-dark-400 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 resize-none"
        />
      </div>

      {/* Code reference file metadata */}
      <div className="flex items-center gap-2.5 px-4 py-3 rounded-lg bg-dark-900/50 border border-dark-600/20 text-xs font-mono text-dark-300 select-text">
        <svg className="w-4 h-4 text-brand-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <span>Ref: {question.refFile} - Lines {question.refLines}</span>
      </div>

      {/* Grading Controls Footer */}
      <div className="flex items-center justify-between border-t border-dark-600/30 pt-6 mt-2 flex-wrap gap-4 select-none">
        {/* Skip button */}
        <button
          type="button"
          onClick={() => onSkip(question.id)}
          className="px-5 py-2.5 rounded-lg text-xs font-bold text-dark-300 hover:text-white border border-dark-600 bg-dark-950 hover:bg-dark-800 transition-all duration-300 flex items-center gap-1.5"
        >
          <ArrowRight className="w-3.5 h-3.5 rotate-18 rotate-180 flipped" />
          Skip Question
        </button>

        {/* Scoring evaluation buttons */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => onGrade(question.id, 'Fail')}
            disabled={!answerDraft.trim()}
            className="px-5 py-2.5 rounded-lg text-xs font-bold text-white bg-red-800/80 border border-red-700/60 hover:bg-red-700 transition-all duration-300 flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed shadow-[0_0_10px_rgba(239,68,68,0.1)]"
          >
            <ThumbsDown className="w-4 h-4" />
            Fail
          </button>
          
          <button
            type="button"
            onClick={() => onGrade(question.id, 'Partial')}
            disabled={!answerDraft.trim()}
            className="px-5 py-2.5 rounded-lg text-xs font-bold text-dark-200 bg-dark-800 border border-dark-600 hover:bg-dark-700 transition-all duration-300 flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Minus className="w-4 h-4" />
            Partial
          </button>
          
          <button
            type="button"
            onClick={() => onGrade(question.id, 'Approve')}
            disabled={!answerDraft.trim()}
            className="px-5 py-2.5 rounded-lg text-xs font-bold text-white bg-brand-500 hover:bg-brand-600 hover:glow-button-shadow transition-all duration-300 flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ThumbsUp className="w-4 h-4" />
            Approve
          </button>
        </div>
      </div>
    </div>
  );
};

export default VivaQuestionCard;
