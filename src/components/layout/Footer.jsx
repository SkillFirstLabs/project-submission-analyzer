import React from 'react';

const Footer = () => {
  return (
    <footer className="w-full bg-dark-950 border-t border-dark-600/30 px-8 py-5 mt-auto">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-xs font-sans text-dark-400">
        <div>
          <span>© 2024 AIPSA Lab. Precision Diagnostic Engine.</span>
        </div>
        
        <div className="flex items-center gap-6">
          <a href="#docs" className="hover:text-white transition-colors duration-200">Documentation</a>
          <a href="#support" className="hover:text-white transition-colors duration-200">Support</a>
          <a href="#privacy" className="hover:text-white transition-colors duration-200">Privacy</a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
