import React from "react";
import type { PDFFormat } from "@/types/pdfFormat";

interface FormatSelectorProps {
  pdfFormat: PDFFormat | null;
  loading: boolean;
  onFormatChange: (format: PDFFormat) => void;
}

const formatDescriptions: Record<string, string> = {
  CERTIFICADO_DE_HOMOLOGACION: "Certificado oficial de homologación de vehículos.",
  CRT: "Certificado de revisión técnica (CRT) para vehículos.",
  SOAP: "Seguro Obligatorio de Accidentes Personales (SOAP).",
  PERMISO_CIRCULACION: "Permiso de circulación anual del vehículo.",
};

const formatIcons: Record<string, string> = {
  CERTIFICADO_DE_HOMOLOGACION: "bi-file-earmark-check",
  CRT: "bi-clipboard-check",
  SOAP: "bi-shield-check",
  PERMISO_CIRCULACION: "bi-card-checklist",
};

const FormatSelector: React.FC<FormatSelectorProps> = ({ pdfFormat, loading, onFormatChange }) => {
  return (
    <div className="mb-4">
      <label className="form-label fw-bold fs-5 mb-2">Selecciona el formato de PDF:</label>
      <div className="d-flex flex-wrap justify-content-center gap-2" role="group">
        <button
          type="button"
          className={`btn ${
            pdfFormat === "CERTIFICADO_DE_HOMOLOGACION" ? "btn-dark" : "btn-outline-dark"
          } d-flex align-items-center justify-content-center position-relative`}
          onClick={() => onFormatChange("CERTIFICADO_DE_HOMOLOGACION")}
          disabled={loading}
          style={{
            minWidth: 220,
            minHeight: 48,
            fontWeight: 500,
            fontSize: "1rem",
            flex: "1 1 320px",
            margin: "4px",
          }}
          aria-label={formatDescriptions["CERTIFICADO_DE_HOMOLOGACION"]}
          title={formatDescriptions["CERTIFICADO_DE_HOMOLOGACION"]}
        >
          <i className={`bi ${formatIcons["CERTIFICADO_DE_HOMOLOGACION"]} me-2 fs-5`} style={{ color: "#333" }}></i>
          Certificado de Homologación
          {pdfFormat === "CERTIFICADO_DE_HOMOLOGACION" && (
            <span
              className="position-absolute top-0 end-0 translate-middle badge rounded-pill bg-secondary"
              style={{ fontSize: "0.7rem" }}
            >
              ✓
            </span>
          )}
        </button>
        <button
          type="button"
          className={`btn ${pdfFormat === "CRT" ? "btn-dark" : "btn-outline-dark"} d-flex align-items-center justify-content-center position-relative`}
          onClick={() => onFormatChange("CRT")}
          disabled={loading}
          style={{
            minWidth: 220,
            minHeight: 48,
            fontWeight: 500,
            fontSize: "1rem",
            flex: "1 1 320px",
            margin: "4px",
          }}
          aria-label={formatDescriptions["CRT"]}
          title={formatDescriptions["CRT"]}
        >
          <i className={`bi ${formatIcons["CRT"]} me-2 fs-5`} style={{ color: "#333" }}></i>
          Certificado de Revisión Técnica (CRT)
          {pdfFormat === "CRT" && (
            <span
              className="position-absolute top-0 end-0 translate-middle badge rounded-pill bg-secondary"
              style={{ fontSize: "0.7rem" }}
            >
              ✓
            </span>
          )}
        </button>
        <button
          type="button"
          className={`btn ${pdfFormat === "SOAP" ? "btn-dark" : "btn-outline-dark"} d-flex align-items-center justify-content-center position-relative`}
          onClick={() => onFormatChange("SOAP")}
          disabled={loading}
          style={{
            minWidth: 220,
            minHeight: 48,
            fontWeight: 500,
            fontSize: "1rem",
            flex: "1 1 320px",
            margin: "4px",
          }}
          aria-label={formatDescriptions["SOAP"]}
          title={formatDescriptions["SOAP"]}
        >
          <i className={`bi ${formatIcons["SOAP"]} me-2 fs-5`} style={{ color: "#333" }}></i>
          SOAP (Seguro Obligatorio)
          {pdfFormat === "SOAP" && (
            <span
              className="position-absolute top-0 end-0 translate-middle badge rounded-pill bg-secondary"
              style={{ fontSize: "0.7rem" }}
            >
              ✓
            </span>
          )}
        </button>
        <button
          type="button"
          className={`btn ${
            pdfFormat === "PERMISO_CIRCULACION" ? "btn-dark" : "btn-outline-dark"
          } d-flex align-items-center justify-content-center position-relative`}
          onClick={() => onFormatChange("PERMISO_CIRCULACION")}
          disabled={loading}
          style={{
            minWidth: 220,
            minHeight: 48,
            fontWeight: 500,
            fontSize: "1rem",
            flex: "1 1 320px",
            margin: "4px",
          }}
          aria-label={formatDescriptions["PERMISO_CIRCULACION"]}
          title={formatDescriptions["PERMISO_CIRCULACION"]}
        >
          <i className={`bi ${formatIcons["PERMISO_CIRCULACION"]} me-2 fs-5`} style={{ color: "#333" }}></i>
          Permiso de Circulación
          {pdfFormat === "PERMISO_CIRCULACION" && (
            <span
              className="position-absolute top-0 end-0 translate-middle badge rounded-pill bg-secondary"
              style={{ fontSize: "0.7rem" }}
            >
              ✓
            </span>
          )}
        </button>
      </div>
      <div className="form-text text-muted mt-2 text-center">
        <i className="bi bi-info-circle me-1"></i>
        Pasa el mouse sobre cada opción para ver su descripción.
      </div>
    </div>
  );
};

export default FormatSelector;
