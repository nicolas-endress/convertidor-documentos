"use client";

import React, { memo, useMemo, useState, useCallback, useRef } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
} from "@tanstack/react-table";
import { useVirtualizer } from "@tanstack/react-virtual";
import { PERFORMANCE_CONFIG, type VirtualizedTableProps } from "@/types/results";
import ResultsToolbar from "@/components/results/ResultsToolbar";

// ============================================================================
// CELDA MEMOIZADA - Evita re-renders innecesarios
// ============================================================================
const TableCell = memo(function TableCell({
  value,
  width,
}: {
  value: string | number | null;
  width: number;
}) {
  return (
    <div
      className="table-cell"
      style={{
        width,
        minWidth: width,
        maxWidth: width,
        padding: "8px 12px",
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
        borderRight: "1px solid #e5e7eb",
        fontSize: "0.875rem",
      }}
      title={String(value ?? "")}
    >
      {value ?? ""}
    </div>
  );
});

// ============================================================================
// FILA MEMOIZADA
// ============================================================================
const TableRow = memo(function TableRow({
  row,
  headers,
  columnWidths,
  isEven,
  isHovered,
  onHover,
  style,
}: {
  row: (string | number | null)[];
  headers: string[];
  columnWidths: number[];
  isEven: boolean;
  isHovered: boolean;
  onHover: (hover: boolean) => void;
  style: React.CSSProperties;
}) {
  return (
    <div
      className="table-row"
      style={{
        ...style,
        display: "flex",
        width: "100%",
        backgroundColor: isHovered ? "#f0f9ff" : isEven ? "#ffffff" : "#f9fafb",
        borderBottom: "1px solid #e5e7eb",
        transition: "background-color 0.1s ease",
      }}
      onMouseEnter={() => onHover(true)}
      onMouseLeave={() => onHover(false)}
    >
      {headers.map((_, colIdx) => (
        <TableCell
          key={colIdx}
          value={row[colIdx]}
          width={columnWidths[colIdx]}
        />
      ))}
    </div>
  );
});

// ============================================================================
// COMPONENTE PRINCIPAL: VirtualizedResultsTable
// ============================================================================
export default function VirtualizedResultsTable({
  headers,
  rows,
  height = 500,
  rowHeight = PERFORMANCE_CONFIG.ROW_HEIGHT,
  overscan = PERFORMANCE_CONFIG.OVERSCAN,
  onDownload,
  excelBlob,
  fileName = "consolidado.xlsx",
  showToolbar = true,
  isLoading = false,
  onExpand,
}: VirtualizedTableProps) {
  // Estado de sorting y filtering
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState("");
  const [hoveredRowIndex, setHoveredRowIndex] = useState<number | null>(null);

  // Refs del contenedor scrollable y header
  const parentRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);

  // Sincronizar scroll horizontal entre header y body
  const handleBodyScroll = useCallback(() => {
    if (parentRef.current && headerRef.current) {
      headerRef.current.scrollLeft = parentRef.current.scrollLeft;
    }
  }, []);

  // Calcular anchos de columna basado en contenido
  const columnWidths = useMemo(() => {
    return headers.map((header, idx) => {
      // Calcular ancho basado en header y primeras filas
      const headerWidth = header.length * 10 + 24;
      let maxContentWidth = headerWidth;

      // Muestrear primeras 100 filas para estimar ancho
      const sampleSize = Math.min(rows.length, 100);
      for (let i = 0; i < sampleSize; i++) {
        const cellValue = String(rows[i][idx] ?? "");
        const cellWidth = cellValue.length * 8 + 24;
        maxContentWidth = Math.max(maxContentWidth, cellWidth);
      }

      return Math.min(
        Math.max(maxContentWidth, PERFORMANCE_CONFIG.MIN_COLUMN_WIDTH),
        PERFORMANCE_CONFIG.MAX_COLUMN_WIDTH
      );
    });
  }, [headers, rows]);

  // Ancho total de la tabla
  const totalWidth = useMemo(
    () => columnWidths.reduce((sum, w) => sum + w, 0),
    [columnWidths]
  );

  // Convertir datos a formato de TanStack Table
  type RowData = Record<string, string | number | null>;

  const tableData = useMemo<RowData[]>(() => {
    return rows.map((row) => {
      const obj: RowData = {};
      headers.forEach((header, idx) => {
        obj[header] = row[idx];
      });
      return obj;
    });
  }, [rows, headers]);

  // Crear definiciones de columna
  const columnHelper = createColumnHelper<RowData>();

  const columns = useMemo(() => {
    return headers.map((header, idx) =>
      columnHelper.accessor(header, {
        id: header,
        header: () => header,
        cell: (info) => info.getValue(),
        size: columnWidths[idx],
        enableSorting: true,
        enableColumnFilter: true,
      })
    );
  }, [headers, columnWidths, columnHelper]);

  // Configurar TanStack Table
  const table = useReactTable({
    data: tableData,
    columns,
    state: {
      sorting,
      globalFilter,
    },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    globalFilterFn: "includesString",
  });

  // Obtener filas filtradas/ordenadas
  const { rows: tableRows } = table.getRowModel();

  // Configurar virtualizador
  const virtualizer = useVirtualizer({
    count: tableRows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: useCallback(() => rowHeight, [rowHeight]),
    overscan,
  });

  const virtualItems = virtualizer.getVirtualItems();
  const totalSize = virtualizer.getTotalSize();

  // Handlers memoizados
  const handleGlobalFilterChange = useCallback((value: string) => {
    setGlobalFilter(value);
  }, []);

  const handleRowHover = useCallback((index: number, hover: boolean) => {
    setHoveredRowIndex(hover ? index : null);
  }, []);

  const handleDownload = useCallback(() => {
    if (excelBlob && onDownload) {
      onDownload();
    } else if (excelBlob) {
      const url = URL.createObjectURL(excelBlob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  }, [excelBlob, onDownload, fileName]);

  // Render estado vacío
  if (!isLoading && rows.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-gray-200">
        <div className="text-center text-gray-500">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p className="mt-2 text-sm">No hay datos para mostrar</p>
        </div>
      </div>
    );
  }

  // Determinar si estamos en modo expandido (cuando onExpand existe, estamos en preview)
  const isPreviewMode = !!onExpand;

  // Altura para el contenedor de scroll
  // En preview: altura fija pasada como prop
  // En expandido: usamos la altura pasada (que viene calculada desde ExpandedView)
  const scrollContainerHeight = height;

  return (
    <div
      className="virtualized-table-container"
      style={{
        width: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Toolbar */}
      {showToolbar && (
        <ResultsToolbar
          totalRows={rows.length}
          filteredRows={tableRows.length}
          globalFilter={globalFilter}
          onGlobalFilterChange={handleGlobalFilterChange}
          onDownload={excelBlob ? handleDownload : undefined}
          onExpand={onExpand}
          isLoading={isLoading}
        />
      )}

      {/* Contenedor exterior con borde */}
      <div
        style={{
          border: "1px solid #e5e7eb",
          borderRadius: "8px",
          backgroundColor: "#fff",
          boxShadow: "0 1px 3px 0 rgb(0 0 0 / 0.1)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* Contenedor con scroll horizontal y vertical - altura fija */}
        <div
          ref={parentRef}
          onScroll={handleBodyScroll}
          style={{
            height: scrollContainerHeight,
            maxHeight: scrollContainerHeight,
            overflowX: "auto",
            overflowY: "auto",
            scrollbarWidth: "auto",
            scrollbarColor: "#94a3b8 #f1f5f9",
          }}
        >
          {/* Contenedor interno con ancho mínimo = suma de columnas */}
          <div style={{ minWidth: totalWidth, width: "fit-content" }}>
            {/* Header sticky */}
            <div
              ref={headerRef}
              style={{
                position: "sticky",
                top: 0,
                zIndex: 10,
                backgroundColor: "#f8fafc",
                borderBottom: "2px solid #e5e7eb",
                display: "flex",
                width: totalWidth,
              }}
            >
              {table.getHeaderGroups().map((headerGroup) =>
                headerGroup.headers.map((header, idx) => (
                  <div
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    style={{
                      width: columnWidths[idx],
                      minWidth: columnWidths[idx],
                      maxWidth: columnWidths[idx],
                      padding: "12px",
                      fontWeight: 600,
                      fontSize: "0.75rem",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                      color: "#374151",
                      cursor: header.column.getCanSort() ? "pointer" : "default",
                      userSelect: "none",
                      display: "flex",
                      alignItems: "center",
                      gap: "4px",
                      borderRight: "1px solid #e5e7eb",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      backgroundColor: "#f8fafc",
                    }}
                    title={String(
                      flexRender(header.column.columnDef.header, header.getContext())
                    )}
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {header.column.getIsSorted() && (
                      <span style={{ marginLeft: "4px" }}>
                        {header.column.getIsSorted() === "asc" ? "↑" : "↓"}
                      </span>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Cuerpo virtualizado */}
            <div
              style={{
                position: "relative",
                width: totalWidth,
              }}
            >
              <div
                style={{
                  height: totalSize,
                  width: totalWidth,
                  position: "relative",
                }}
              >
                {virtualItems.map((virtualRow) => {
                  const row = tableRows[virtualRow.index];
                  const rowData = row.original;
                  const rowArray = headers.map((h) => rowData[h]);

                  return (
                    <TableRow
                      key={virtualRow.key}
                      row={rowArray}
                      headers={headers}
                      columnWidths={columnWidths}
                      isEven={virtualRow.index % 2 === 0}
                      isHovered={hoveredRowIndex === virtualRow.index}
                      onHover={(hover) => handleRowHover(virtualRow.index, hover)}
                      style={{
                        position: "absolute",
                        top: 0,
                        left: 0,
                        width: totalWidth,
                        height: rowHeight,
                        transform: `translateY(${virtualRow.start}px)`,
                      }}
                    />
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Footer con estadísticas */}
        <div
          style={{
            padding: "8px 12px",
            backgroundColor: "#f8fafc",
            borderTop: "1px solid #e5e7eb",
            fontSize: "0.75rem",
            color: "#6b7280",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexShrink: 0,
          }}
        >
          <span>
            Mostrando {tableRows.length.toLocaleString()} de{" "}
            {rows.length.toLocaleString()} filas
          </span>
          {sorting.length > 0 && (
            <span>
              Ordenado por: {sorting[0].id} ({sorting[0].desc ? "desc" : "asc"})
            </span>
          )}
        </div>
      </div>

      {/* Loading overlay */}
      {isLoading && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundColor: "rgba(255, 255, 255, 0.8)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 20,
          }}
        >
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      )}
    </div>
  );
}
