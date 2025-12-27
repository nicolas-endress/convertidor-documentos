"use client";

import React, { memo, useState, useEffect, useCallback } from "react";
import { PERFORMANCE_CONFIG, type ResultsToolbarProps } from "@/types/results";

/**
 * Toolbar para la tabla de resultados.
 * Incluye: búsqueda global, contador de filas, botón de descarga y expandir.
 */
const ResultsToolbar = memo(function ResultsToolbar({
  totalRows,
  filteredRows,
  globalFilter,
  onGlobalFilterChange,
  onDownload,
  onExpand,
  isLoading = false,
}: ResultsToolbarProps) {
  // Debounce del filtro para mejor performance
  const [localFilter, setLocalFilter] = useState(globalFilter);

  useEffect(() => {
    const timeout = setTimeout(() => {
      onGlobalFilterChange(localFilter);
    }, PERFORMANCE_CONFIG.FILTER_DEBOUNCE);

    return () => clearTimeout(timeout);
  }, [localFilter, onGlobalFilterChange]);

  // Sincronizar cuando cambia desde fuera
  useEffect(() => {
    setLocalFilter(globalFilter);
  }, [globalFilter]);

  const handleClearFilter = useCallback(() => {
    setLocalFilter("");
    onGlobalFilterChange("");
  }, [onGlobalFilterChange]);

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "12px",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 16px",
        backgroundColor: "#f8fafc",
        borderRadius: "8px",
        marginBottom: "12px",
        border: "1px solid #e5e7eb",
      }}
    >
      {/* Sección izquierda: Búsqueda */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px", flex: 1 }}>
        <div style={{ position: "relative", minWidth: "250px", maxWidth: "400px", flex: 1 }}>
          <input
            type="text"
            placeholder="Buscar en todos los campos..."
            value={localFilter}
            onChange={(e) => setLocalFilter(e.target.value)}
            style={{
              width: "100%",
              padding: "8px 36px 8px 36px",
              border: "1px solid #d1d5db",
              borderRadius: "6px",
              fontSize: "0.875rem",
              outline: "none",
              transition: "border-color 0.2s, box-shadow 0.2s",
            }}
            onFocus={(e) => {
              e.target.style.borderColor = "#3b82f6";
              e.target.style.boxShadow = "0 0 0 3px rgba(59, 130, 246, 0.1)";
            }}
            onBlur={(e) => {
              e.target.style.borderColor = "#d1d5db";
              e.target.style.boxShadow = "none";
            }}
          />
          {/* Icono de búsqueda */}
          <svg
            style={{
              position: "absolute",
              left: "10px",
              top: "50%",
              transform: "translateY(-50%)",
              width: "18px",
              height: "18px",
              color: "#9ca3af",
            }}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          {/* Botón limpiar */}
          {localFilter && (
            <button
              onClick={handleClearFilter}
              style={{
                position: "absolute",
                right: "8px",
                top: "50%",
                transform: "translateY(-50%)",
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: "4px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#6b7280",
              }}
              title="Limpiar búsqueda"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Sección central: Contador */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          padding: "6px 12px",
          backgroundColor: "#fff",
          borderRadius: "6px",
          border: "1px solid #e5e7eb",
          fontSize: "0.875rem",
          color: "#374151",
        }}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <span>
          <strong>{filteredRows.toLocaleString()}</strong>
          {filteredRows !== totalRows && (
            <span style={{ color: "#9ca3af" }}> de {totalRows.toLocaleString()}</span>
          )}
          <span style={{ color: "#6b7280" }}> filas</span>
        </span>
        {isLoading && (
          <div
            className="animate-spin"
            style={{
              width: "14px",
              height: "14px",
              border: "2px solid #e5e7eb",
              borderTopColor: "#3b82f6",
              borderRadius: "50%",
            }}
          />
        )}
      </div>

      {/* Sección derecha: Botones */}
      <div style={{ display: "flex", gap: "8px" }}>
        {/* Botón Expandir */}
        {onExpand && (
          <button
            onClick={onExpand}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "8px 14px",
              backgroundColor: "#fff",
              border: "1px solid #d1d5db",
              borderRadius: "6px",
              fontSize: "0.875rem",
              fontWeight: 500,
              color: "#374151",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "#f9fafb";
              e.currentTarget.style.borderColor = "#9ca3af";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "#fff";
              e.currentTarget.style.borderColor = "#d1d5db";
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
              />
            </svg>
            Expandir
          </button>
        )}

        {/* Botón Descargar */}
        {onDownload && (
          <button
            onClick={onDownload}
            disabled={isLoading}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "8px 14px",
              backgroundColor: isLoading ? "#9ca3af" : "#10b981",
              border: "none",
              borderRadius: "6px",
              fontSize: "0.875rem",
              fontWeight: 500,
              color: "#fff",
              cursor: isLoading ? "not-allowed" : "pointer",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              if (!isLoading) {
                e.currentTarget.style.backgroundColor = "#059669";
              }
            }}
            onMouseLeave={(e) => {
              if (!isLoading) {
                e.currentTarget.style.backgroundColor = "#10b981";
              }
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
              />
            </svg>
            Descargar Excel
          </button>
        )}
      </div>
    </div>
  );
});

export default ResultsToolbar;
