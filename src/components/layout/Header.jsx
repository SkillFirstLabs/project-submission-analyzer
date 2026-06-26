import React from 'react';
import { useProject } from '../../contexts/ProjectContext';
import { User } from 'lucide-react';

const Header = () => {
  const { currentStage, setCurrentStage } = useProject();

  const stages = [
    { id: 1, label: 'Upload' },
    { id: 2, label: 'Analysis' },
    { id: 3, label: 'Viva' },
    { id: 4, label: 'Report' }
  ];

  // Helper to check if navigation is allowed (only backwards or if already completed)
  const handleStageClick = (stageId) => {
    if (stageId < currentStage) {
      setCurrentStage(stageId);
    }
  };

  return (
    <header className="w-full bg-dark-950 border-b border-dark-600/30 sticky top-0 z-50 px-8 py-4 backdrop-blur-md bg-dark-950/80">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand Logo */}
        <div className="flex items-center gap-2">
          <span className="font-extrabold text-2xl text-white tracking-wider font-sans select-none">
            AIPSA
          </span>
        </div>

        {/* Tab Navigation (Matching Stitch exactly) */}
        <nav className="flex items-center gap-8">
          {stages.map((stage) => {
            const isActive = currentStage === stage.id;
            const isClickable = stage.id < currentStage;
            
            return (
              <button
                key={stage.id}
                onClick={() => handleStageClick(stage.id)}
                disabled={!isClickable}
                className={`relative py-1 font-medium text-sm transition-all duration-300 font-sans tracking-wide ${
                  isActive 
                    ? 'text-white' 
                    : isClickable 
                      ? 'text-dark-300 hover:text-white cursor-pointer' 
                      : 'text-dark-400 cursor-not-allowed'
                }`}
              >
                {stage.label}
                {isActive && (
                  <span className="absolute bottom-[-17px] left-0 right-0 h-[2px] bg-white rounded-full" />
                )}
              </button>
            );
          })}
        </nav>

        {/* User Icon Widget */}
        <div className="flex items-center justify-center w-9 h-9 rounded-full border border-dark-600 bg-dark-800 hover:border-brand-500 transition-colors duration-300 cursor-pointer text-dark-300 hover:text-white">
          <User className="w-4 h-4" />
        </div>
      </div>
    </header>
  );
};

export default Header;
