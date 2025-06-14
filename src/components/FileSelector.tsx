import React from "react";

interface FileSelectorProps {
  files: FileList | null;
  loading: boolean;
  onFileChange: (fileList: FileList | null) => void;
}

const FileSelector: React.FC<FileSelectorProps> = ({ files, loading, onFileChange }) => {
  return (
    <div className="mb-4">
      <div className="d-flex justify-content-center">
        <div style={{ width: "100%", maxWidth: 400 }}>
          <label
            htmlFor="file-upload"
            className="w-100"
            style={{
              cursor: loading ? "not-allowed" : "pointer",
              userSelect: "none",
            }}
          >
            <div
              className="d-flex align-items-center justify-content-center"
              style={{
                background: "#fff",
                color: "#222",
                border: "1.5px solid #ced4da",
                borderRadius: "0.5rem",
                fontWeight: 500,
                fontSize: "1.08rem",
                padding: "0.75rem 1.5rem",
                boxShadow: "0 1px 4px #0001",
                pointerEvents: loading ? "none" : "auto",
              }}
            >
              <i className="bi bi-upload" style={{ fontSize: 20, color: "#333" }}></i>
              <span
                style={{
                  flex: 1,
                  textAlign: "center",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  maxWidth: "calc(100% - 40px)", // Ajusta dinámicamente el ancho
                }}
              >
                {files && files.length > 0
                  ? `${files.length} archivo${files.length > 1 ? "s" : ""} seleccionado${files.length > 1 ? "s" : ""}`
                  : "Seleccionar archivos PDF"}
              </span>
            </div>
            <input
              id="file-upload"
              type="file"
              accept=".pdf"
              multiple
              style={{ display: "none" }}
              disabled={loading}
              onChange={(e) => onFileChange(e.target.files)}
            />
          </label>
          {files && files.length > 0 && (
            <div
              style={{
                marginTop: "0.75rem",
                background: "#f8f9fa",
                border: "1px solid #e3e6ea",
                borderRadius: "0.5rem",
                padding: "0.5rem 1rem",
                fontSize: "0.98rem",
                color: "#333",
                maxHeight: 120,
                overflowY: "auto",
              }}
            >
              <div style={{ fontWeight: 600, marginBottom: 4 }}>Archivos seleccionados:</div>
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {Array.from(files).map((file, idx) => (
                  <li key={idx} style={{ wordBreak: "break-all" }}>
                    <i className="bi bi-file-earmark-pdf me-1" style={{ color: "#333" }}></i>
                    {file.name}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileSelector;
