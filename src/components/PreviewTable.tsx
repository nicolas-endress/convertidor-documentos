"use client";

import React, { useCallback } from "react";
import { saveAs } from "file-saver";
import { VirtualizedResultsTable } from "./results";

interface PreviewTableProps {
  memoizedHeaders: string[];
  memoizedRows: (string | number | null)[][];
  setIsExpanded: (value: boolean) => void;
  excelBlob: Blob | null;
  fileName: string;
}

/**
 * Componente PreviewTable que usa el nuevo sistema de virtualización
 * con TanStack Table + TanStack Virtual para mejor rendimiento.
 */
const PreviewTable: React.FC<PreviewTableProps> = ({
  memoizedHeaders,
  memoizedRows,
  setIsExpanded,
  excelBlob,
  fileName,
}) => {
  const handleDownload = useCallback(() => {
    if (excelBlob) {
      saveAs(excelBlob, fileName);
    }
  }, [excelBlob, fileName]);

  const handleExpand = useCallback(() => {
    setIsExpanded(true);
  }, [setIsExpanded]);

  // Si no hay datos, mostrar mensaje
  if (!memoizedHeaders.length || !memoizedRows.length) {
    return (
      <div className="mt-4">
        <div
          className="d-flex align-items-center justify-content-center"
          style={{
            height: "200px",
            backgroundColor: "#f8f9fa",
            borderRadius: "8px",
            border: "1px dashed #dee2e6",
          }}
        >
          <p className="text-muted mb-0">No hay datos para mostrar</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4">
      <h5 className="mb-3 text-center fw-bold">
        <i className="bi bi-table me-2"></i>
        Vista Previa del Excel
        <span
          className="badge bg-secondary ms-2"
          style={{ fontSize: "0.7rem", verticalAlign: "middle" }}
        >
          {memoizedRows.length.toLocaleString()} filas
        </span>
      </h5>

      <VirtualizedResultsTable
        headers={memoizedHeaders}
        rows={memoizedRows}
        height={420}
        excelBlob={excelBlob}
        fileName={fileName}
        onDownload={handleDownload}
        onExpand={handleExpand}
        showToolbar={true}
      />
    </div>
  );
};

export default PreviewTable;
