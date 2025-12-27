"use client";

import React, { useEffect, useState, useCallback } from "react";
import { VirtualizedResultsTable } from "./results";

interface ExpandedViewProps {
  memoizedHeaders: string[];
  memoizedRows: (string | number | null)[][];
  listHeight: number;
  setIsExpanded: (value: boolean) => void;
  excelBlob?: Blob | null;
  fileName?: string;
}

/**
 * Vista expandida de la tabla con virtualización completa.
 * Usa TanStack Table + TanStack Virtual para máximo rendimiento.
 */
const ExpandedView: React.FC<ExpandedViewProps> = ({
  memoizedHeaders,
  memoizedRows,
  setIsExpanded,
  excelBlob,
  fileName = "consolidado.xlsx",
}) => {
  const [dynamicHeight, setDynamicHeight] = useState(500);

  // Ajustar dinámicamente el alto según la ventana
  useEffect(() => {
    const updateHeight = () => {
      // Restar espacio para header (60px) y padding (40px)
      const availableHeight = window.innerHeight - 160;
      setDynamicHeight(Math.max(400, availableHeight));
    };

    updateHeight();
    window.addEventListener("resize", updateHeight);
    return () => window.removeEventListener("resize", updateHeight);
  }, []);

  // Bloquear scroll del body
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
    };
  }, []);

  // Manejar tecla Escape para cerrar
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsExpanded(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [setIsExpanded]);

  const handleClose = useCallback(() => {
    setIsExpanded(false);
  }, [setIsExpanded]);

  const handleDownload = useCallback(() => {
    if (excelBlob) {
      const url = URL.createObjectURL(excelBlob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  }, [excelBlob, fileName]);

  return (
    <div
      className="position-fixed top-0 start-0 w-100 h-100"
      style={{
        zIndex: 3000,
        background: "rgba(0, 0, 0, 0.85)",
        backdropFilter: "blur(4px)",
        display: "flex",
        flexDirection: "column",
        padding: "20px",
        animation: "fadeIn 0.2s ease-out",
      }}
      onClick={(e) => {
        // Cerrar al hacer click fuera del contenido
        if (e.target === e.currentTarget) {
          handleClose();
        }
      }}
    >
      {/* Header con botón cerrar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "16px",
          flexShrink: 0,
        }}
      >
        <h4 style={{ color: "#fff", margin: 0, display: "flex", alignItems: "center", gap: "8px" }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 3h18v18H3zM9 3v18M15 3v18M3 9h18M3 15h18" />
          </svg>
          Vista Expandida
          <span
            style={{
              fontSize: "0.875rem",
              backgroundColor: "rgba(255,255,255,0.2)",
              padding: "4px 12px",
              borderRadius: "20px",
              marginLeft: "8px",
            }}
          >
            {memoizedRows.length.toLocaleString()} filas
          </span>
        </h4>
        <button
          onClick={handleClose}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "10px 20px",
            backgroundColor: "#ef4444",
            border: "none",
            borderRadius: "8px",
            color: "#fff",
            fontSize: "0.9rem",
            fontWeight: 600,
            cursor: "pointer",
            transition: "background-color 0.2s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#dc2626")}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#ef4444")}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
          Cerrar (Esc)
        </button>
      </div>

      {/* Contenedor de la tabla */}
      <div
        style={{
          flex: 1,
          backgroundColor: "#fff",
          borderRadius: "12px",
          overflow: "hidden",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ flex: 1, padding: "16px", overflow: "hidden" }}>
          <VirtualizedResultsTable
            headers={memoizedHeaders}
            rows={memoizedRows}
            height={dynamicHeight}
            excelBlob={excelBlob}
            fileName={fileName}
            onDownload={excelBlob ? handleDownload : undefined}
            showToolbar={true}
          />
        </div>
      </div>

      {/* Estilos de animación */}
      <style jsx global>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};

export default ExpandedView;
