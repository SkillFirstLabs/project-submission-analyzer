import React, { useRef, useState } from 'react';
import { UploadCloud, File, X, CheckCircle2 } from 'lucide-react';

const ZipUpload = ({ onFileSelected, selectedFile, onFileCleared }) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const validateAndProcessFile = (file) => {
    if (!file) return;

    // Check file extension
    const isZip = file.name.endsWith('.zip') || file.type === 'application/x-zip-compressed' || file.type === 'application/zip';
    if (!isZip) {
      setError('Please upload a valid ZIP archive.');
      return;
    }

    // Check file size (50MB limit)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      setError('File is too large. Max allowed size is 50MB.');
      return;
    }

    setError('');
    onFileSelected({
      name: file.name,
      size: (file.size / (1024 * 1024)).toFixed(2), // MB
      type: file.type
    });
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndProcessFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndProcessFile(e.target.files[0]);
    }
  };

  const triggerInputClick = () => {
    fileInputRef.current.click();
  };

  return (
    <div className="w-full">
      <label className="block text-xs font-bold tracking-widest text-dark-400 mb-2 uppercase select-none">
        Source Code Repository
      </label>
      
      {!selectedFile ? (
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={triggerInputClick}
          className={`w-full py-12 rounded-xl border-2 border-dashed flex flex-col items-center justify-center cursor-pointer transition-all duration-300 ${
            isDragActive 
              ? 'border-brand-500 bg-brand-500/5' 
              : 'border-dark-600 bg-dark-950 hover:border-brand-500/50 hover:bg-dark-900/40'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip"
            onChange={handleChange}
            className="hidden"
          />

          <div className="w-14 h-14 rounded-full bg-dark-800 border border-dark-600 flex items-center justify-center text-dark-300 mb-4 transition-transform duration-300 hover:scale-105">
            <UploadCloud className="w-6 h-6 text-dark-300" />
          </div>

          <h3 className="text-white font-bold text-lg mb-1 font-sans">
            Drag & Drop ZIP file
          </h3>
          <p className="text-dark-300 text-sm mb-4">
            or click to browse
          </p>
          <span className="text-[10px] font-bold tracking-wider text-dark-400 font-sans uppercase">
            Max 50MB
          </span>

          {error && (
            <p className="text-red-500 text-xs mt-3 bg-red-500/10 px-3 py-1 rounded-md border border-red-500/20">
              {error}
            </p>
          )}
        </div>
      ) : (
        <div className="w-full p-6 rounded-xl border border-brand-500/30 bg-brand-500/5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-400">
              <File className="w-5 h-5" />
            </div>
            <div>
              <p className="text-white text-sm font-semibold truncate max-w-[200px] sm:max-w-md">
                {selectedFile.name}
              </p>
              <p className="text-dark-300 text-xs mt-0.5">
                {selectedFile.size} MB
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 text-emerald-500 text-xs bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Ready
            </span>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onFileCleared();
              }}
              className="p-1 rounded-full text-dark-300 hover:text-white hover:bg-dark-800 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ZipUpload;
