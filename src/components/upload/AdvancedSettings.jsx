import React, { useState } from 'react';
import { ChevronRight, ChevronDown } from 'lucide-react';

const AdvancedSettings = ({ questionsCount, setQuestionsCount, focusAreas, setFocusAreas }) => {
  const [isOpen, setIsOpen] = useState(false);

  const availableAreas = ['Frontend', 'Backend', 'Database', 'Security', 'Architecture'];

  const toggleArea = (area) => {
    if (focusAreas.includes(area)) {
      if (focusAreas.length > 1) {
        setFocusAreas(focusAreas.filter(a => a !== area));
      }
    } else {
      setFocusAreas([...focusAreas, area]);
    }
  };

  return (
    <div className="w-full border-t border-dark-600/30 pt-4">
      {/* Header Toggle Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-xs font-bold tracking-widest text-dark-400 hover:text-white uppercase transition-colors duration-200 select-none"
      >
        {isOpen ? <ChevronDown className="w-4 h-4 text-dark-400" /> : <ChevronRight className="w-4 h-4 text-dark-400" />}
        Advanced Settings
      </button>

      {/* Collapsible Content */}
      {isOpen && (
        <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-8 pl-6 animate-fadeIn">
          {/* Questions slider */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-dark-300 tracking-wider font-sans uppercase">
                Questions per skill
              </label>
              <span className="text-sm font-semibold text-brand-400 font-sans">
                {questionsCount} questions
              </span>
            </div>
            <input
              type="range"
              min="3"
              max="10"
              value={questionsCount}
              onChange={(e) => setQuestionsCount(parseInt(e.target.value))}
              className="w-full h-1 bg-dark-800 rounded-lg appearance-none cursor-pointer accent-brand-500 mt-2"
            />
            <div className="flex justify-between text-[10px] text-dark-400 font-bold px-1 mt-1 uppercase">
              <span>3 Min</span>
              <span>10 Max</span>
            </div>
          </div>

          {/* Focus Areas Selection */}
          <div className="flex flex-col gap-2">
            <label className="text-xs font-bold text-dark-300 tracking-wider font-sans uppercase mb-1">
              Analysis Focus Areas
            </label>
            <div className="flex flex-wrap gap-2">
              {availableAreas.map((area) => {
                const isSelected = focusAreas.includes(area);
                return (
                  <button
                    key={area}
                    type="button"
                    onClick={() => toggleArea(area)}
                    className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-all duration-300 ${
                      isSelected
                        ? 'border-brand-500 bg-brand-500/10 text-white font-semibold'
                        : 'border-dark-600 bg-dark-950 text-dark-300 hover:border-dark-400 hover:text-white'
                    }`}
                  >
                    {area}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedSettings;
