import axios from "axios";

const apiBaseUrl = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000" : "");

const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 120000,
});

export const uploadContract = (file, onProgress) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/api/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => onProgress?.(Math.round((e.loaded * 100) / e.total)),
  });
};

export const getStatus = (documentId) =>
  api.get(`/api/status/${documentId}`);

export const getAnalysis = (documentId) =>
  api.get(`/api/analysis/${documentId}`);

export const askQuestion = (documentId, question) =>
  api.post("/api/qa", { document_id: documentId, question });

export const getReportUrl = (documentId) =>
  `${apiBaseUrl}/api/report/${documentId}`;

export const checkHealth = () => api.get("/api/health");

export const compareContracts = (fileA, fileB) => {
  const form = new FormData();
  form.append("file_a", fileA);
  form.append("file_b", fileB);
  return api.post("/api/compare", form, { headers: { "Content-Type": "multipart/form-data" } });
};

export const getCompareStatus = (comparisonId) =>
  api.get(`/api/compare/status/${comparisonId}`);

export const getCompareResult = (comparisonId) =>
  api.get(`/api/compare/result/${comparisonId}`);
