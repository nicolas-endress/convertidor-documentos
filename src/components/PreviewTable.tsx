import React, { useState } from "react";
import { FixedSizeList as List } from "react-window";
import { saveAs } from "file-saver";

interface PreviewTableProps {
  memoizedHeaders: string[];
  memoizedRows: any[][];
  setIsExpanded: (value: boolean) => void;
  excelBlob: Blob | null;
  fileName: string;
}

const PreviewTable: React.FC<PreviewTableProps> = ({
  memoizedHeaders,
  memoizedRows,
  setIsExpanded,
  excelBlob,
  fileName,
}) => {
  const [hoveredRow, setHoveredRow] = useState<number | null>(null);

  const renderVirtualRow = (
    row: any,
    headers: string[],
    style: React.CSSProperties,
    rowIndex: number
  ) => (
    <div
      style={{
        ...style,
        display: "table",
        tableLayout: "fixed",
        width: "100%",
        borderBottom: "1px solid #f8f9fa",
        background: rowIndex === hoveredRow ? "#e9ecef" : rowIndex % 2 === 0 ? "#fff" : "#f8f9fa",
        transition: "background 0.2s ease",
      }}
      key={rowIndex}
      role="row"
      onMouseEnter={() => setHoveredRow(rowIndex)}
      onMouseLeave={() => setHoveredRow(null)}
    >
      {headers.map((header, colIdx) => (
        <div
          key={colIdx}
          style={{
            display: "table-cell",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            textAlign: "left",
            borderRight: "1px solid #dee2e6",
            padding: "0.5rem",
            verticalAlign: "middle",
          }}
          role="cell"
        >
          {Array.isArray(row) ? row[colIdx] ?? "" : ""}
        </div>
      ))}
    </div>
  );

  return (
    <div className="mt-4">
      <h5 className="mb-3 text-center fw-bold">
        <i className="bi bi-eye me-2"></i>
        Vista Previa del Excel
      </h5>
      <div
        style={{
          flex: 1,
          minHeight: 0,
          width: "100%",
          overflowX: "auto",
          overflowY: "auto",
          background: "#fff",
          borderRadius: "0.5rem",
          boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
          marginBottom: "1rem",
          border: "1px solid #e3e6f0",
        }}
      >
        <div style={{ minWidth: "900px" }}>
          <table
            className="table table-bordered table-striped table-sm mb-0"
            style={{
              tableLayout: "fixed",
              width: "100%",
              borderCollapse: "separate",
              borderSpacing: 0,
            }}
          >
            <thead className="table-light">
              <tr
                style={{
                  display: "table",
                  tableLayout: "fixed",
                  width: "100%",
                }}
              >
                {memoizedHeaders.map((header: string, idx: number) => (
                  <th
                    key={idx}
                    style={{
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      textAlign: "left",
                      borderRight: "1px solid #dee2e6",
                      borderBottom: "2px solid #dee2e6",
                      background: "#f8f9fa",
                      padding: "0.5rem",
                    }}
                  >
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
          </table>
          <div style={{ display: "block", width: "100%" }}>
            <List
              height={Math.min(420, typeof window !== "undefined" ? window.innerHeight - 300 : 420)}
              itemCount={memoizedRows.length}
              itemSize={35}
              width={"100%"}
            >
              {({ index, style }) =>
                renderVirtualRow(memoizedRows[index], memoizedHeaders, style, index)
              }
            </List>
          </div>
        </div>
      </div>
      <div className="d-flex flex-column flex-md-row justify-content-between align-items-center mt-3 gap-2">
        <button
          className="btn btn-outline-dark d-flex align-items-center gap-2"
          onClick={() => setIsExpanded(true)}
          style={{
            minWidth: 180,
            minHeight: 44,
            fontWeight: 600,
            fontSize: "1.08rem",
          }}
        >
          <i className="bi bi-arrows-fullscreen"></i>
          Expandir Vista
        </button>
        <button
          className="btn btn-dark d-flex align-items-center gap-2"
          onClick={() => {
            if (excelBlob) saveAs(excelBlob, fileName);
          }}
          style={{
            minWidth: 180,
            minHeight: 44,
            fontWeight: 600,
            fontSize: "1.08rem",
          }}
        >
          <i className="bi bi-download"></i>
          Descargar Excel
        </button>
      </div>
    </div>
  );
};

export default PreviewTable;
