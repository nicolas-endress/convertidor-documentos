import React, { useEffect, useState } from "react";
import { FixedSizeList as List } from "react-window";

interface ExpandedViewProps {
  memoizedHeaders: string[];
  memoizedRows: any[][];
  listHeight: number;
  setIsExpanded: (value: boolean) => void;
}

const ExpandedView: React.FC<ExpandedViewProps> = ({
  memoizedHeaders,
  memoizedRows,
  listHeight,
  setIsExpanded,
}) => {
  const [dynamicHeight, setDynamicHeight] = useState(listHeight);
  const [hoveredRow, setHoveredRow] = useState<number | null>(null);

  // Ajustar dinámicamente el alto de la tabla según el tamaño de la pantalla
  useEffect(() => {
    const updateHeight = () => {
      const availableHeight = window.innerHeight - 180; // Restar espacio para encabezados y márgenes
      setDynamicHeight(Math.min(availableHeight, memoizedRows.length * 35)); // Ajustar al contenido o al espacio disponible
    };

    updateHeight();
    window.addEventListener("resize", updateHeight);
    return () => window.removeEventListener("resize", updateHeight);
  }, [memoizedRows.length]);

  // Bloquear el scroll del body mientras la vista expandida está activa
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
    };
  }, []);

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
    <div
      className="position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center animate__animated animate__fadeIn"
      style={{
        zIndex: 3000,
        left: 0,
        top: 0,
        width: "100vw",
        height: "100vh",
        minHeight: "100vh",
        minWidth: "100vw",
        background: "rgba(33, 37, 41, 0.92)",
        overflow: "hidden", // Cambiado de "auto" a "hidden" para evitar scroll innecesario
        transition: "background 0.2s",
      }}
    >
      <div
        className="bg-white rounded shadow w-100 h-100"
        style={{
          maxWidth: "100vw",
          maxHeight: "100vh",
          overflow: "hidden", // Asegura que el contenido no desborde
          position: "relative",
          display: "flex",
          flexDirection: "column",
          justifyContent: "flex-start",
          boxShadow: "0 0 0 9999px rgba(33,37,41,0.92)",
        }}
      >
        <div
          className="sticky-top bg-white p-2 d-flex justify-content-end"
          style={{
            zIndex: 3,
            top: 0,
            position: "sticky",
          }}
        >
          <button
            className="btn btn-danger d-flex align-items-center gap-2"
            onClick={() => setIsExpanded(false)}
          >
            <i className="bi bi-x-lg"></i>
            Cerrar Vista
          </button>
        </div>
        <div
          className="flex-grow-1 d-flex flex-column"
          style={{ padding: "0.5rem", minHeight: 0 }}
        >
          <h4 className="mb-3 text-center fw-bold" style={{ marginTop: 0 }}>
            <i className="bi bi-table me-2"></i>
            Vista Expandida del Excel
          </h4>
          <div
            style={{
              flex: 1, // Asegura que el contenido ocupe todo el espacio disponible
              width: "100%",
              overflow: "auto",
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-start",
            }}
          >
            <div
              style={{
                minWidth: "900px",
                display: "flex",
                flexDirection: "column",
                flex: 1, // Asegura que la tabla ocupe todo el espacio vertical
              }}
            >
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
              <div style={{ display: "block", width: "100%", flex: 1 }}>
                <List
                  height={dynamicHeight} // Usar el alto dinámico calculado
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
        </div>
      </div>
    </div>
  );
};

export default ExpandedView;
