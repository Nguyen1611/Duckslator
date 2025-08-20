import React, { useState, useRef } from 'react';
import './App.css'


// // List of available languages with flags
// const LANGUAGES = [
//   "English 🇬🇧", "Spanish 🇪🇸", "French 🇫🇷", "German 🇩🇪", "Chinese 🇨🇳",
//   "Japanese 🇯🇵", "Russian 🇷🇺", "Portuguese 🇵🇹", "Italian 🇮🇹", "Arabic 🇸🇦",
//   "Hindi 🇮🇳", "Bengali 🇧🇩", "Korean 🇰🇷", "Turkish 🇹🇷", "Dutch 🇳🇱",
//   "Polish 🇵🇱", "Swedish 🇸🇪",
// ];

// export default function DuckslatorApp() {
//   // State to store the uploaded file for processing
//   const [uploadedFile, setUploadedFile] = useState(null);
//   // State for language selected by user
//   const [selectedLanguage, setSelectedLanguage] = useState(LANGUAGES[0]);
//   // Flag for when the translated output file is ready
//   const [outputReady, setOutputReady] = useState(false);
//   // URL for previewing the translated output file
//   const [outputFileUrl, setOutputFileUrl] = useState('');
//   // Ref to hidden file input to trigger browse dialog
//   const fileInputRef = useRef();

//   /**
//    * Handle file selection from the hidden input.
//    * Updates state and clears any previous output.
//    */
//   const handleFileChange = (e) => {
//     setUploadedFile(e.target.files[0]);
//     setOutputReady(false);
//     setOutputFileUrl('');
//   };

//   /**
//    * Sends the uploaded file and chosen language to backend for processing.
//    * If successful, stores URL of translated file for playback and download.
//    */
//   const handleTranslate = async () => {
//     if (!uploadedFile || !selectedLanguage) return;

//     // Remove emoji for backend compatibility
//     const languageId = selectedLanguage.split(' ')[0];
//     const formData = new FormData();
//     formData.append('file', uploadedFile);
//     formData.append('language', languageId);

//     try {
//       const res = await fetch('http://127.0.0.1:8000/process-file/', {
//         method: 'POST',
//         body: formData,
//       });

//       if (res.ok) {
//         const blob = await res.blob();
//         // Create URL for processed file preview/download
//         const url = URL.createObjectURL(blob);
//         setOutputFileUrl(url);
//         setOutputReady(true);
//       } else {
//         setOutputReady(false);
//         alert('Backend error occurred.');
//       }
//     } catch (err) {
//       alert('Upload or processing failed: ' + err.toString());
//     }
//   };

//   /**
//    * Resets all state and clears file input.
//    */
//   const handleReset = () => {
//     setUploadedFile(null);
//     setOutputFileUrl('');
//     setOutputReady(false);
//     if (fileInputRef.current) fileInputRef.current.value = '';
//   };

//   return (
//     <div className="flex h-screen w-screen bg-[#FFF9DC]">
//       {/* Sidebar fixed to the left */}
//       <aside className="fixed top-0 left-0 bottom-0 w-[370px] min-w-[300px] h-full px-8 py-10 bg-[#f3faff] border-r border-gray-100 overflow-auto flex flex-col justify-between">
//         <div>
//           {/* Logo and Title */}
//           <div className="flex items-center gap-2 mb-1">
//             <span className="text-2xl">🦆</span>
//             <span className="font-bold text-2xl text-gray-700">Duckslator</span>
//           </div>

//           {/* Subtitle */}
//           <p className="mb-7 text-gray-700 font-medium text-base">
//             The Ultimate Translator For Video And Audio.
//           </p>

//           {/* Settings Section Header */}
//           <div className="flex items-center gap-2 mb-2">
//             <span className="text-xl">🛠️</span>
//             <span className="font-semibold text-xl text-gray-600">Settings</span>
//           </div>

//           {/* Instructions */}
//           <div className="text-sm text-gray-900 mb-3 font-medium">
//             Upload an audio or video file.
//           </div>

//           {/* Drag and drop / Browse Files section */}
//           <div className="bg-yellow-100 rounded-lg px-4 py-4 mb-4 w-full shadow-sm">
//             <p className="font-semibold text-gray-700 mb-1">Drag and drop file here</p>
//             <p className="text-xs text-gray-500 mb-3">Limit 1GB per file • WAV, MP4, MOV, MPEG4</p>
//             <label className="block w-full">
//               {/* Hidden file input */}
//               <input
//                 ref={fileInputRef}
//                 type="file"
//                 accept=".mp4,.mov,.wav"
//                 onChange={handleFileChange}
//                 className="sr-only"
//               />
//               {/* Custom styled browse button */}
//               <button
//                 type="button"
//                 className="inline-block px-4 py-2 rounded-full bg-white text-gray-700 border border-gray-300 font-semibold w-full hover:bg-blue-50 transition"
//                 onClick={() => fileInputRef.current && fileInputRef.current.click()}
//               >
//                 Browse files
//               </button>
//             </label>
//           </div>

//           {/* Clear uploaded file button */}
//           <button
//             onClick={handleReset}
//             className="flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-gray-200 text-gray-700 font-semibold mb-4 shadow-sm hover:bg-blue-50 transition"
//           >
//             <span className="text-lg">🗑️</span>
//             Clear Uploaded File
//           </button>

//           {/* Language selection label */}
//           <label className="text-[1rem] font-semibold mb-2 text-gray-700">
//             Choose your language
//           </label>

//           {/* Language dropdown selector */}
//           <select
//             value={selectedLanguage}
//             onChange={(e) => setSelectedLanguage(e.target.value)}
//             className="w-full px-3 py-2 rounded-lg bg-yellow-100 font-semibold mb-5 border border-gray-200 text-gray-900"
//           >
//             {LANGUAGES.map((lang) => (
//               <option key={lang} value={lang}>
//                 {lang.split(' ')[0]} {lang.split(' ')[1]}
//               </option>
//             ))}
//           </select>

//           {/* Translate file button */}
//           <button
//             onClick={handleTranslate}
//             className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-full text-gray-800 font-semibold transition hover:bg-blue-50 mb-3 shadow-sm"
//           >
//             <span className="text-lg">⏳</span>
//             Translate File
//           </button>

//           {/* Reset all button */}
//           <button
//             onClick={handleReset}
//             className="flex items-center gap-2 px-4 py-2 bg-white border border-blue-300 rounded-full text-blue-700 font-semibold transition hover:bg-blue-100 shadow-sm"
//           >
//             <span className="text-lg">🔄</span>
//             Reset All
//           </button>
//         </div>
//       </aside>

//       {/* Main content: duck animation with margin to avoid sidebar */}
//       <main className="flex-1 h-full ml-[370px] flex items-center justify-center bg-[#FFF9DC] overflow-auto">
//         <img
//           src="/gif2.gif"
//           alt="Duckslator Duck"
//           className="max-h-[80vh] max-w-[90vw] h-auto scale-150"
//         />
//       </main>
//     </div>
//   );
// }

// const LANGUAGES = [
//   "English 🇬🇧", "Spanish 🇪🇸", "French 🇫🇷", "German 🇩🇪", "Chinese 🇨🇳",
//   "Japanese 🇯🇵", "Russian 🇷🇺", "Portuguese 🇵🇹", "Italian 🇮🇹", "Arabic 🇸🇦",
//   "Hindi 🇮🇳", "Bengali 🇧🇩", "Korean 🇰🇷", "Turkish 🇹🇷", "Dutch 🇳🇱",
//   "Polish 🇵🇱", "Swedish 🇸🇪",
// ];

// export default function DuckslatorModern() {
//   // State and handlers
//   const [uploadedFile, setUploadedFile] = useState(null);
//   const [selectedLanguage, setSelectedLanguage] = useState(LANGUAGES[0]);
//   const [outputReady, setOutputReady] = useState(false);
//   const [outputFileUrl, setOutputFileUrl] = useState('');
//   const [loading, setLoading] = useState(false);
//   const fileInputRef = useRef();

//   const handleFileChange = (e) => {
//     setUploadedFile(e.target.files);
//     setOutputReady(false);
//     setOutputFileUrl('');
//   };

//   const handleTranslate = async () => {
//     if (!uploadedFile || !selectedLanguage) return;
//     setLoading(true);
//     const languageId = selectedLanguage.split(' ');
//     const formData = new FormData();
//     formData.append('file', uploadedFile);
//     formData.append('language', languageId);

//     try {
//       const res = await fetch('http://127.0.0.1:8000/process-file/', {
//         method: 'POST',
//         body: formData,
//       });
//       if (res.ok) {
//         const blob = await res.blob();
//         const url = URL.createObjectURL(blob);
//         setOutputFileUrl(url);
//         setOutputReady(true);
//       } else {
//         setOutputReady(false);
//         alert('Backend error occurred.');
//       }
//     } catch (err) {
//       alert('Upload or processing failed: ' + err.toString());
//     }
//     setLoading(false);
//   };

//   const handleReset = () => {
//     setUploadedFile(null);
//     setOutputFileUrl('');
//     setOutputReady(false);
//     setLoading(false);
//     if (fileInputRef.current) fileInputRef.current.value = '';
//   };

//   return (
//     <div className="min-h-screen min-w-full flex justify-center items-center bg-gradient-to-br from-[#fffbe6] via-[#ffe7ba] to-[#fff9dc]">
//       {/* Responsive Card */}
//       <div className="backdrop-blur-lg bg-white/70 rounded-3xl shadow-2xl max-w-4xl w-[96vw] mx-auto flex flex-col md:flex-row overflow-hidden">
//         {/* Sidebar - branding, form, controls */}
//         <div className="w-full md:w-1/3 px-8 py-8 flex flex-col gap-6 bg-gradient-to-b from-white/85 to-[#f9fafb]">
//           {/* Brand */}
//           <div className="flex items-center gap-3 mb-2">
//             <span className="text-3xl">🦆</span>
//             <h1 className="font-extrabold text-2xl text-gray-800 tracking-tight drop-shadow">Duckslator</h1>
//           </div>
//           <p className="text-sm text-gray-500 font-medium mb-3">
//             The Ultimate Translator For Video & Audio.
//           </p>

//           {/* Upload Form */}
//           <div>
//             <label className="font-semibold text-gray-700 flex items-center gap-2 mb-2">
//               <span className="text-lg">🛠️</span>Settings
//             </label>
//             <div className="mb-4">
//               <label className="block mb-2 text-xs font-semibold text-gray-600">
//                 Upload an audio or video file
//               </label>
//               {/* Dropzone */}
//               <div className="relative group bg-yellow-50 border-2 border-dashed border-yellow-200 px-3 py-5 rounded-xl">
//                 <input
//                   ref={fileInputRef}
//                   type="file"
//                   accept=".mp4,.mov,.wav"
//                   onChange={handleFileChange}
//                   className="absolute top-0 left-0 w-full h-full opacity-0 cursor-pointer"
//                   aria-label="File Upload"
//                 />
//                 <div className="text-center pointer-events-none">
//                   <div className="flex flex-col items-center gap-1">
//                     <span className="text-base font-medium text-yellow-400">
//                       {uploadedFile ? uploadedFile.name : "Drag or browse file"}
//                     </span>
//                     <span className="text-xs text-gray-800">
//                       Up to 1GB: WAV, MP4, MOV
//                     </span>
//                   </div>
//                 </div>
//               </div>
//             </div>

//           {uploadedFile && (
//             <div className="mt-2 mb-2 bg-gray-50 border border-gray-400 rounded-lg px-3 py-2 text-sm text-gray-800 flex items-center justify-between gap-2">
//               <div className="flex items-center gap-2">
//                 <span className="material-icons text-base text-gray-500">insert_drive_file</span>
//                 <span className="truncate max-w-[140px]">{uploadedFile.name}</span>
//               </div>
//               <button
//                 onClick={handleReset}
//                 className="hover:bg-gray-200 rounded-full p-1 transition"
//                 aria-label="Remove file"
//                 type="button"
//               >
//                 <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
//                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
//                 </svg>
//               </button>
//             </div>
//           )}

//             <button
//               type="button"
//               onClick={handleReset}
//               className="mt-1 w-full py-2 rounded-lg bg-white border border-gray-200 hover:bg-gray-100 text-gray-700 font-semibold flex items-center justify-center gap-2 transition"
//             >
//               <span className="material-icons text-base">Clear File</span>
              
//             </button>
//           </div>

//           {/* Language */}
//           <div>
//             <label className="font-semibold text-gray-700 block mb-2 mt-2">
//               Choose your language
//             </label>
//             <select
//               value={selectedLanguage}
//               onChange={e => setSelectedLanguage(e.target.value)}
//               className="w-full px-3 py-2 rounded-xl bg-yellow-50 border border-gray-200 text-gray-700 font-medium outline-none focus:ring focus:ring-yellow-100 transition"
//             >
//               {LANGUAGES.map(lang => (
//                 <option key={lang} value={lang}>{lang}</option>
//               ))}
//             </select>
//           </div>

//           {/* Action Buttons */}
//           <div className="flex gap-2 flex-col mt-2">
//             <button
//               onClick={handleTranslate}
//               disabled={loading || !uploadedFile}
//               className={`w-full py-2 transition rounded-xl flex justify-center items-center gap-1 font-semibold
//                 ${loading || !uploadedFile
//                   ? "bg-yellow-100 text-yellow-400 cursor-not-allowed"
//                   : "bg-gradient-to-r from-yellow-200 to-yellow-400 hover:from-yellow-100 hover:to-yellow-300 text-gray-900"}`}
//             >
//               <span className="material-icons text-lg"></span>
//               {loading ? "Translating..." : "Translate File"}
//             </button>
//             <button
//               onClick={handleReset}
//               className="w-full py-2 rounded-xl border border-blue-300 bg-blue-50 text-blue-500 hover:bg-blue-100 flex items-center gap-1 justify-center font-semibold transition"
//             >
//               <span className="material-icons text-lg"></span>
//               Reset All
//             </button>
//           </div>
//         </div>

//         {/* Main section - image/preview */}
//         <div className="flex-1 bg-[#FFF9DC] flex flex-col items-center justify-center p-6 min-h-[350px]">
//           {/* If translated output, show playback & download */}
//           {outputReady ? (
//             <div className="w-full max-w-md mx-auto flex flex-col items-center gap-4">
//               <div className="text-gray-800 text-lg font-semibold mb-2">Processed File:</div>
//               {outputFileUrl.endsWith('.mp4') ? (
//                 <video src={outputFileUrl} controls className="w-full rounded-xl shadow-lg" />
//               ) : (
//                 <audio src={outputFileUrl} controls className="w-full rounded-xl shadow-lg" />
//               )}
//               <a
//                 href={outputFileUrl}
//                 download={uploadedFile ? "translated_" + uploadedFile.name : "translated_file"}
//                 className="inline-block mt-2 px-5 py-2 rounded-xl bg-blue-500 text-white font-bold hover:bg-blue-600 transition shadow"
//               >
//                 Download Translated File
//               </a>
//             </div>
//           ) : (
//             // Otherwise, show the duck
//             <img
//               src="/gif2.gif"
//               alt="Duckslator Duck"
//               className="w-[380px] max-w-full h-auto mx-auto drop-shadow-lg scale-80"
//             />
//           )}
//         </div>
//       </div>
//     </div>
//   );
// }


const LANGUAGES = [
  "English 🇬🇧", "Spanish 🇪🇸", "French 🇫🇷", "German 🇩🇪", "Chinese 🇨🇳",
  "Japanese 🇯🇵", "Russian 🇷🇺", "Portuguese 🇵🇹", "Italian 🇮🇹", "Arabic 🇸🇦",
  "Hindi 🇮🇳", "Bengali 🇧🇩", "Korean 🇰🇷", "Turkish 🇹🇷", "Dutch 🇳🇱",
  "Polish 🇵🇱", "Swedish 🇸🇪",
];

export default function DuckslatorModern() {
  // State and handlers
  const [uploadedFile, setUploadedFile] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState(LANGUAGES[0]);
  const [outputReady, setOutputReady] = useState(false);
  const [outputFileUrl, setOutputFileUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef();

  const handleFileChange = (e) => {
    setUploadedFile(e.target.files);
    setOutputReady(false);
    setOutputFileUrl('');
  };

  const handleTranslate = async () => {
    if (!uploadedFile || !selectedLanguage) return;
    setLoading(true);
    const languageId = selectedLanguage.split(' ');
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
    setLoading(false);
  };

  const handleReset = () => {
    setUploadedFile(null);
    setOutputFileUrl('');
    setOutputReady(false);
    setLoading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="min-h-screen min-w-full bg-gradient-to-br from-[#fffbe6] via-[#ffe7ba] to-[#fff9dc] flex justify-center items-center">
      <div className="backdrop-blur-xl bg-white/70 rounded-3xl shadow-2xl max-w-2xl w-full p-12 flex flex-col items-center gap-10">
        <div className="flex flex-col items-center px-8 pt-8 pb-4">
  <div className="flex items-center gap-4 mb-2 select-none">
    {/* <span className="text-5xl drop-shadow-lg transform scale-110">🦆</span> */}
    <h1 className="font-extrabold text-4xl md:text-5xl text-gradient bg-gradient-to-r from-yellow-400 via-yellow-300 to-yellow-500 bg-clip-text text-transparent tracking-wide">
      Duckslator
    </h1>
  </div>
  <p className="text-lg md:text-xl font-medium text-blue-gray-700 tracking-wide max-w-full leading-relaxed whitespace-nowrap">
  The Ultimate Translator for Video & Audio.
  </p>
</div>


        {/* Upload box */}
        <div className="w-full max-w-lg">
          <label className="block text-xl font-semibold text-gray-700 mb-3">
            Upload an audio or video file
          </label>
          <div className="relative group bg-yellow-50 border-2 border-dashed border-yellow-200 px-6 py-8 rounded-2xl text-lg mb-6">
            <input
              ref={fileInputRef}
              type="file"
              accept=".mp4,.mov,.wav"
              onChange={handleFileChange}
              className="absolute top-0 left-0 w-full h-full opacity-0 cursor-pointer"
              aria-label="File Upload"
            />
            <div className="text-center pointer-events-none">
              <div className="flex flex-col items-center gap-2">
                <span className="material-icons text-4xl text-yellow-400"></span>
                <span className="text-lg font-medium text-gray-900">
                  {uploadedFile ? uploadedFile.name : "Drag or browse file"}
                </span>
                <span className="text-lg text-gray-400 ">
                  Up to 1GB: WAV, MP4, MOV
                </span>
              </div>
            </div>
          </div>
          {/* Show uploaded file with X button to remove */}
          {uploadedFile && (
            <div className="mt-2 mb-4 bg-gray-50 border border-gray-100 rounded-xl px-4 py-3 text-base text-gray-800 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="material-icons text-lg text-gray-500">insert_drive_file</span>
                <span className="truncate max-w-[200px]">{uploadedFile.name}</span>
              </div>
              <button
                onClick={handleReset}
                className="hover:bg-gray-200 rounded-full p-2 transition"
                aria-label="Remove file"
                type="button"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}
        </div>

        {/* Language selection */}
        <div className="w-full max-w-lg">
          <label className="text-lg font-semibold text-gray-700 block mb-2">
            Choose your language
          </label>
          <select
            value={selectedLanguage}
            onChange={e => setSelectedLanguage(e.target.value)}
            className="w-full px-4 py-3 rounded-2xl bg-yellow-50 border border-gray-200 text-gray-700 font-medium outline-none focus:ring focus:ring-yellow-100 transition text-lg mb-6"
          >
            {LANGUAGES.map(lang => (
              <option key={lang} value={lang}>{lang}</option>
            ))}
          </select>
        </div>

        {/* Action buttons */}
        <div className="flex w-full max-w-lg gap-5">
          <button
            onClick={handleTranslate}
            disabled={loading || !uploadedFile}
            className={`flex-1 text-lg py-3 rounded-2xl font-bold flex justify-center items-center gap-2 transition shadow
              ${loading || !uploadedFile
                ? "bg-yellow-100 text-yellow-400 cursor-not-allowed"
                : "bg-gradient-to-r from-yellow-100 to-yellow-400 hover:from-yellow-200 hover:to-yellow-300 text-gray-900"}`}
          >
            {loading ? "Translating..." : "Translate"}
          </button>
          <button
            onClick={handleReset}
            className="flex-1 text-lg py-3 rounded-2xl border border-gray-300 bg-gray-50 text-gray-700 hover:bg-gray-100 font-bold flex items-center gap-2 justify-center transition shadow"
          >
            
            Reset
          </button>
        </div>

        {/* Output preview (if ready) */}
        {outputReady && (
          <div className="w-full max-w-lg mt-6 flex flex-col items-center gap-5">
            <div className="text-gray-800 text-2xl font-semibold">Processed File</div>
            {outputFileUrl.endsWith('.mp4') ? (
              <video src={outputFileUrl} controls className="w-full rounded-xl shadow-lg" />
            ) : (
              <audio src={outputFileUrl} controls className="w-full rounded-xl shadow-lg" />
            )}
            <a
              href={outputFileUrl}
              download={uploadedFile ? "translated_" + uploadedFile.name : "translated_file"}
              className="inline-block mt-2 px-6 py-3 rounded-2xl bg-gray-500 text-white text-lg font-bold hover:bg-gray-600 transition shadow"
            >
              Download
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
