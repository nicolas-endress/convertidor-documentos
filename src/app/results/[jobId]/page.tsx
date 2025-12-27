"use client";

import { useState, useEffect, useMemo } from "react";
import { VirtualizedResultsTable } from "@/components/results";

interface ResultsPageProps {
  params: Promise<{
    jobId: string;
  }>;
}

// Datos de ejemplo para testing
function generateMockData(rowCount: number) {
  const headers = [
    "Nombre PDF",
    "Placa Única",
    "Código SII",
    "Valor Permiso",
    "Total a pagar",
    "Fecha de emisión",
    "Fecha de vencimiento",
    "Estado",
  ];

  const rows: (string | number | null)[][] = [];

  for (let i = 0; i < rowCount; i++) {
    rows.push([
      `documento_${i + 1}.pdf`,
      `AA-${String(i).padStart(4, "0")}`,
      `SII${100000 + i}`,
      Math.floor(Math.random() * 500000) + 50000,
      Math.floor(Math.random() * 100000) + 10000,
      `${String(Math.floor(Math.random() * 28) + 1).padStart(2, "0")}/12/2024`,
      `${String(Math.floor(Math.random() * 28) + 1).padStart(2, "0")}/12/2025`,
      Math.random() > 0.1 ? "Procesado" : "Error",
    ]);
  }

  return { headers, rows };
}

export default function ResultsPage({ params }: ResultsPageProps) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [rowCount, setRowCount] = useState(5000);

  // Resolver params async
  useEffect(() => {
    params.then((p) => setJobId(p.jobId));
  }, [params]);

  // Generar datos mock
  const { headers, rows } = useMemo(() => generateMockData(rowCount), [rowCount]);

  // Simular carga
  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 500);
    return () => clearTimeout(timer);
  }, [rowCount]);

  return (
    <div style={{ padding: "24px", maxWidth: "1800px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: "24px" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "8px" }}>
          Resultados del Proceso
        </h1>
        <p style={{ color: "#6b7280", fontSize: "0.875rem" }}>
          Job ID: <code style={{ backgroundColor: "#f3f4f6", padding: "2px 8px", borderRadius: "4px" }}>{jobId || "..."}</code>
        </p>
      </div>

      {/* Controles de prueba */}
      <div
        style={{
          marginBottom: "16px",
          padding: "12px",
          backgroundColor: "#fef3c7",
          borderRadius: "8px",
          border: "1px solid #fcd34d",
        }}
      >
        <label style={{ fontSize: "0.875rem", fontWeight: 500 }}>
          🧪 Test: Número de filas a generar:{" "}
          <select
            value={rowCount}
            onChange={(e) => {
              setIsLoading(true);
              setRowCount(Number(e.target.value));
            }}
            style={{
              marginLeft: "8px",
              padding: "4px 8px",
              borderRadius: "4px",
              border: "1px solid #d1d5db",
            }}
          >
            <option value={100}>100 filas</option>
            <option value={1000}>1,000 filas</option>
            <option value={5000}>5,000 filas</option>
            <option value={10000}>10,000 filas</option>
            <option value={25000}>25,000 filas</option>
            <option value={50000}>50,000 filas</option>
          </select>
        </label>
      </div>

      {/* Tabla virtualizada */}
      <VirtualizedResultsTable
        headers={headers}
        rows={rows}
        height={600}
        isLoading={isLoading}
        showToolbar={true}
      />

      {/* Info de performance */}
      <div
        style={{
          marginTop: "16px",
          padding: "12px",
          backgroundColor: "#ecfdf5",
          borderRadius: "8px",
          border: "1px solid #6ee7b7",
          fontSize: "0.75rem",
          color: "#065f46",
        }}
      >
        <strong>ℹ️ Info de Performance:</strong>
        <ul style={{ margin: "8px 0 0 16px", padding: 0 }}>
          <li>Virtualización: Solo se renderizan ~20-30 filas visibles + overscan</li>
          <li>TanStack Table: Sorting y filtering optimizados</li>
          <li>TanStack Virtual: Scroll suave con 60fps</li>
          <li>Memoización: Celdas y filas memoizadas para evitar re-renders</li>
        </ul>
      </div>
    </div>
  );
}
