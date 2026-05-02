import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";

const ACCEPT = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  "text/plain": [".txt"],
};

function FileDropzone({ label, file, onFile, letter, color }) {
  const onDrop = useCallback((accepted) => {
    if (accepted[0]) onFile(accepted[0]);
  }, [onFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPT,
    maxFiles: 1,
  });

  return (
    <div
      {...getRootProps()}
      className={`flex-1 border-2 border-dashed rounded-2xl p-8 cursor-pointer transition-all text-center
        ${isDragActive ? `border-${color}-400 bg-${color}-50` : `border-gray-200 hover:border-${color}-300 bg-white`}`}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-3">
        <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold text-white
          ${color === "blue" ? "bg-blue-500" : "bg-purple-500"}`}>
          {letter}
        </div>
        {file ? (
          <div className="text-center">
            <p className="font-medium text-gray-800 text-sm break-all max-w-48 mx-auto">{file.name}</p>
            <p className="text-xs text-green-500 mt-1">✓ Ready</p>
          </div>
        ) : (
          <>
            <p className="text-gray-700 font-medium text-sm">{label}</p>
            <p className="text-xs text-gray-400">Drop PDF, DOCX, or TXT here</p>
            <p className="text-xs text-gray-400">or click to browse</p>
          </>
        )}
      </div>
    </div>
  );
}

export default function CompareUploadZone({ onCompare, loading }) {
  const [fileA, setFileA] = useState(null);
  const [fileB, setFileB] = useState(null);

  const canCompare = fileA && fileB && !loading;

  return (
    <div className="flex flex-col items-center gap-6 w-full max-w-2xl">
      <div className="flex gap-4 w-full items-stretch">
        <FileDropzone
          label="Contract A (baseline)"
          file={fileA}
          onFile={setFileA}
          letter="A"
          color="blue"
        />
        <div className="flex items-center justify-center px-2">
          <span className="text-gray-300 text-xl font-light">vs</span>
        </div>
        <FileDropzone
          label="Contract B (compare to)"
          file={fileB}
          onFile={setFileB}
          letter="B"
          color="purple"
        />
      </div>

      <button
        onClick={() => canCompare && onCompare(fileA, fileB)}
        disabled={!canCompare}
        className={`w-full py-3 rounded-xl font-semibold text-sm transition-colors
          ${canCompare
            ? "bg-blue-600 hover:bg-blue-700 text-white"
            : "bg-gray-100 text-gray-400 cursor-not-allowed"}`}
      >
        {loading ? "Comparing..." : "Compare Contracts →"}
      </button>

      {(!fileA || !fileB) && (
        <p className="text-xs text-gray-400">Upload both contracts to enable comparison</p>
      )}
    </div>
  );
}
