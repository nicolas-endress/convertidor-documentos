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
 * Totalmente responsivo y adaptable a cualquier tamaño de pantalla.
 */
const ExpandedView: React.FC<ExpandedViewProps> = ({
  memoizedHeaders,
  memoizedRows,
  setIsExpanded,
  excelBlob,
  fileName = "consolidado.xlsx",
}) => {
  const [tableHeight, setTableHeight] = useState(400);

  // Calcular altura disponible para la tabla
  useEffect(() => {
    const updateHeight = () => {
      // Altura total de la ventana
      const windowHeight = window.innerHeight;
      // Restar: padding superior (20) + header expandido (60) + margin (16) +
      //         padding contenedor (32) + toolbar (56) + footer tabla (40) + padding inferior (20)
      const reservedSpace = 20 + 60 + 16 + 32 + 56 + 40 + 20;
      const availableHeight = windowHeight - reservedSpace;
      setTableHeight(Math.max(300, availableHeight));
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
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 3000,
        background: "rgba(0, 0, 0, 0.85)",
        backdropFilter: "blur(4px)",
        display: "flex",
        flexDirection: "column",
        padding: "20px",
        animation: "fadeIn 0.2s ease-out",
      }}
      onClick={(e) => {
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
          height: "40px",
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

      {/* Contenedor de la tabla - sin overflow propio */}
      <div
        style={{
          flex: 1,
          backgroundColor: "#fff",
          borderRadius: "12px",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          minHeight: 0, // Importante para flex
        }}
      >
        <div style={{ flex: 1, padding: "16px", minHeight: 0, display: "flex", flexDirection: "column" }}>
          <VirtualizedResultsTable
            headers={memoizedHeaders}
            rows={memoizedRows}
            height={tableHeight}
            excelBlob={excelBlob}
            fileName={fileName}
            onDownload={excelBlob ? handleDownload : undefined}
            showToolbar={true}
          />
        </div>
      </div>

      {/* Estilos de animación y scrollbar */}
      <style jsx global>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        /* Scrollbar visible y estilizada */
        .virtualized-table-container ::-webkit-scrollbar {
          width: 12px;
          height: 12px;
        }

        .virtualized-table-container ::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 6px;
        }

        .virtualized-table-container ::-webkit-scrollbar-thumb {
          background: #94a3b8;
          border-radius: 6px;
          border: 2px solid #f1f5f9;
        }

        .virtualized-table-container ::-webkit-scrollbar-thumb:hover {
          background: #64748b;
        }

        .virtualized-table-container ::-webkit-scrollbar-corner {
          background: #f1f5f9;
        }
      `}</style>
    </div>
  );
};

export default ExpandedView;
