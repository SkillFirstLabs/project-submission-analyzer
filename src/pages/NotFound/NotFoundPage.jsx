import React from 'react';
import { useProject } from '../../contexts/ProjectContext';
import { ShieldQuestion, ArrowLeft } from 'lucide-react';

const NotFoundPage = () => {
  const { resetApp } = useProject();

  return (
    <div className="w-full flex flex-col items-center justify-center py-20 text-center select-none font-sans">
      <ShieldQuestion className="w-16 h-16 text-brand-500 mb-4 animate-bounce-slow" />
      <h1 className="text-3xl font-extrabold text-white mb-2">404 - Page Not Found</h1>
      <p className="text-sm text-dark-300 max-w-sm mb-6">
        The stage or route you are looking for does not exist in the analyzer workflow.
      </p>
      <button
        type="button"
        onClick={resetApp}
        className="px-5 py-2.5 rounded-lg text-xs font-bold text-white bg-dark-800 border border-dark-600 hover:border-brand-500 transition-all flex items-center gap-2"
      >
        <ArrowLeft className="w-4 h-4" />
        Return to Upload Stage
      </button>
    </div>
  );
};

export default NotFoundPage;
