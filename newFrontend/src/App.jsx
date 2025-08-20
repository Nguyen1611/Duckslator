import React, { useState, useRef } from 'react';
import './App.css'


// List of available languages with flags
const LANGUAGES = [
  "English 🇬🇧", "Spanish 🇪🇸", "French 🇫🇷", "German 🇩🇪", "Chinese 🇨🇳",
  "Japanese 🇯🇵", "Russian 🇷🇺", "Portuguese 🇵🇹", "Italian 🇮🇹", "Arabic 🇸🇦",
  "Hindi 🇮🇳", "Bengali 🇧🇩", "Korean 🇰🇷", "Turkish 🇹🇷", "Dutch 🇳🇱",
  "Polish 🇵🇱", "Swedish 🇸🇪",
];

export default function DuckslatorApp() {
  // State to store the uploaded file for processing
  const [uploadedFile, setUploadedFile] = useState(null);
  // State for language selected by user
  const [selectedLanguage, setSelectedLanguage] = useState(LANGUAGES[0]);
  // Flag for when the translated output file is ready
  const [outputReady, setOutputReady] = useState(false);
  // URL for previewing the translated output file
  const [outputFileUrl, setOutputFileUrl] = useState('');
  // Ref to hidden file input to trigger browse dialog
  const fileInputRef = useRef();

  /**
   * Handle file selection from the hidden input.
   * Updates state and clears any previous output.
   */
  const handleFileChange = (e) => {
    setUploadedFile(e.target.files[0]);
    setOutputReady(false);
    setOutputFileUrl('');
  };

  /**
   * Sends the uploaded file and chosen language to backend for processing.
   * If successful, stores URL of translated file for playback and download.
   */
  const handleTranslate = async () => {
    if (!uploadedFile || !selectedLanguage) return;

    // Remove emoji for backend compatibility
    const languageId = selectedLanguage.split(' ')[0];
    const formData = new FormData();
    formData.append('file', uploadedFile);
    formData.append('language', languageId);

    try {
      const res = await fetch('http://127.0.0.1:8000/process-file/', {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        const blob = await res.blob();
        // Create URL for processed file preview/download
        const url = URL.createObjectURL(blob);
        setOutputFileUrl(url);
        setOutputReady(true);
      } else {
        setOutputReady(false);
        alert('Backend error occurred.');
      }
    } catch (err) {
      alert('Upload or processing failed: ' + err.toString());
    }
  };

  /**
   * Resets all state and clears file input.
   */
  const handleReset = () => {
    setUploadedFile(null);
    setOutputFileUrl('');
    setOutputReady(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="flex h-screen w-screen bg-[#FFF9DC]">
      {/* Sidebar fixed to the left */}
      <aside className="fixed top-0 left-0 bottom-0 w-[370px] min-w-[300px] h-full px-8 py-10 bg-[#f3faff] border-r border-gray-100 overflow-auto flex flex-col justify-between">
        <div>
          {/* Logo and Title */}
          <div className="flex items-center gap-2 mb-1">
            <span className="text-2xl">🦆</span>
            <span className="font-bold text-2xl text-gray-700">Duckslator</span>
          </div>

          {/* Subtitle */}
          <p className="mb-7 text-gray-700 font-medium text-base">
            The Ultimate Translator For Video And Audio.
          </p>

          {/* Settings Section Header */}
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xl">🛠️</span>
            <span className="font-semibold text-xl text-gray-600">Settings</span>
          </div>

          {/* Instructions */}
          <div className="text-sm text-gray-900 mb-3 font-medium">
            Upload an audio or video file.
          </div>

          {/* Drag and drop / Browse Files section */}
          <div className="bg-yellow-100 rounded-lg px-4 py-4 mb-4 w-full shadow-sm">
            <p className="font-semibold text-gray-700 mb-1">Drag and drop file here</p>
            <p className="text-xs text-gray-500 mb-3">Limit 1GB per file • WAV, MP4, MOV, MPEG4</p>
            <label className="block w-full">
              {/* Hidden file input */}
              <input
                ref={fileInputRef}
                type="file"
                accept=".mp4,.mov,.wav"
                onChange={handleFileChange}
                className="sr-only"
              />
              {/* Custom styled browse button */}
              <button
                type="button"
                className="inline-block px-4 py-2 rounded-full bg-white text-gray-700 border border-gray-300 font-semibold w-full hover:bg-blue-50 transition"
                onClick={() => fileInputRef.current && fileInputRef.current.click()}
              >
                Browse files
              </button>
            </label>
          </div>

          {/* Clear uploaded file button */}
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-gray-200 text-gray-700 font-semibold mb-4 shadow-sm hover:bg-blue-50 transition"
          >
            <span className="text-lg">🗑️</span>
            Clear Uploaded File
          </button>

          {/* Language selection label */}
          <label className="text-[1rem] font-semibold mb-2 text-gray-700">
            Choose your language
          </label>

          {/* Language dropdown selector */}
          <select
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-yellow-100 font-semibold mb-5 border border-gray-200 text-gray-900"
          >
            {LANGUAGES.map((lang) => (
              <option key={lang} value={lang}>
                {lang.split(' ')[0]} {lang.split(' ')[1]}
              </option>
            ))}
          </select>

          {/* Translate file button */}
          <button
            onClick={handleTranslate}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-full text-gray-800 font-semibold transition hover:bg-blue-50 mb-3 shadow-sm"
          >
            <span className="text-lg">⏳</span>
            Translate File
          </button>

          {/* Reset all button */}
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-blue-300 rounded-full text-blue-700 font-semibold transition hover:bg-blue-100 shadow-sm"
          >
            <span className="text-lg">🔄</span>
            Reset All
          </button>
        </div>
      </aside>

      {/* Main content: duck animation with margin to avoid sidebar */}
      <main className="flex-1 h-full ml-[370px] flex items-center justify-center bg-[#FFF9DC] overflow-auto">
        <img
          src="/gif2.gif"
          alt="Duckslator Duck"
          className="max-h-[80vh] max-w-[90vw] h-auto scale-150"
        />
      </main>
    </div>
  );
}
