import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

const ACCEPTED = { "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"], "text/plain": [".txt"] };

export default function UploadZone({ onUpload, loading }) {
  const [error, setError] = useState("");

  const onDrop = useCallback((accepted, rejected) => {
    setError("");
    if (rejected.length > 0) {
      setError("Only PDF, DOCX, and TXT files under 10 MB are accepted.");
      return;
    }
    if (accepted.length > 0) onUpload(accepted[0]);
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
    disabled: loading,
  });

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-200
          ${isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50"}
          ${loading ? "opacity-50 cursor-not-allowed" : ""}`}
      >
        <input {...getInputProps()} />
        <div className="text-5xl mb-4">📄</div>
        {isDragActive ? (
          <p className="text-blue-600 font-medium text-lg">Drop your contract here...</p>
        ) : (
          <>
            <p className="text-gray-700 font-medium text-lg mb-1">
              Drag & drop your contract here
            </p>
            <p className="text-gray-400 text-sm mb-4">or click to browse files</p>
            <div className="flex gap-2 justify-center">
              {["PDF", "DOCX", "TXT"].map((t) => (
                <span key={t} className="px-3 py-1 bg-white border border-gray-200 rounded-full text-xs text-gray-500 font-medium">
                  {t}
                </span>
              ))}
            </div>
            <p className="text-gray-400 text-xs mt-2">Max 10 MB</p>
          </>
        )}
      </div>
      {error && (
        <p className="mt-2 text-red-600 text-sm text-center">{error}</p>
      )}
    </div>
  );
}
