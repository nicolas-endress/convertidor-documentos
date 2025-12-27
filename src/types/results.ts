/**
 * Tipos para el sistema de visualización de resultados con virtualización.
 */

export interface ColumnDef {
  id: string;
  header: string;
  accessorKey: string;
  width?: number;
  minWidth?: number;
  maxWidth?: number;
}

export interface ResultsRow {
  [key: string]: string | number | boolean | null;
}

export interface ResultsMeta {
  columns: ColumnDef[];
  totalRows: number;
  /** 'client' si rows <= 10000, 'server' si > 10000 */
  modeHint: "client" | "server";
}

export interface ResultsPage {
  rows: ResultsRow[];
  nextCursor: string | null;
  totalRows: number;
}

export interface SortingState {
  id: string;
  desc: boolean;
}

export interface FilterState {
  globalFilter: string;
  columnFilters: Record<string, string>;
}

export interface VirtualizedTableProps {
  /** Headers de la tabla */
  headers: string[];
  /** Filas de datos (array de arrays) */
  rows: (string | number | null)[][];
  /** Altura del contenedor (px) */
  height?: number;
  /** Altura de cada fila (px) */
  rowHeight?: number;
  /** Filas extra a renderizar fuera del viewport */
  overscan?: number;
  /** Callback al hacer click en descargar */
  onDownload?: () => void;
  /** Blob del Excel para descarga */
  excelBlob?: Blob | null;
  /** Nombre del archivo */
  fileName?: string;
  /** Mostrar toolbar */
  showToolbar?: boolean;
  /** Estado de carga */
  isLoading?: boolean;
  /** Callback para expandir vista */
  onExpand?: () => void;
}

export interface ResultsToolbarProps {
  totalRows: number;
  filteredRows: number;
  globalFilter: string;
  onGlobalFilterChange: (value: string) => void;
  onDownload?: () => void;
  onExpand?: () => void;
  isLoading?: boolean;
}

// Constantes de performance
export const PERFORMANCE_CONFIG = {
  /** Altura fija de cada fila para cálculos de virtualización */
  ROW_HEIGHT: 35,
  /** Filas extra a renderizar fuera del viewport (arriba y abajo) */
  OVERSCAN: 10,
  /** Umbral de filas para cambiar de client-mode a server-mode */
  CLIENT_MODE_THRESHOLD: 10000,
  /** Tamaño de página para server-mode */
  PAGE_SIZE: 500,
  /** Debounce para filtro global (ms) */
  FILTER_DEBOUNCE: 150,
  /** Ancho mínimo de columna (px) */
  MIN_COLUMN_WIDTH: 80,
  /** Ancho máximo de columna (px) */
  MAX_COLUMN_WIDTH: 400,
  /** Ancho por defecto de columna (px) */
  DEFAULT_COLUMN_WIDTH: 150,
} as const;
