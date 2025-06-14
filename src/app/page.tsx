"use client";

import { useState, useMemo, useEffect } from "react";
import InstructionsModal from "@/components/InstructionsModal";
import FileSelector from "../components/FileSelector";
import FormatSelector from "../components/FormatSelector";
import ProcessingSummary from "../components/ProcessingSummary";
import PreviewTable from "../components/PreviewTable";
import ExpandedView from "../components/ExpandedView";
import { validatePDFFiles } from "../utils/pdf/fileUtils";
import readXlsxFile from "read-excel-file"; // Eliminado 'saveAs' porque no se utiliza
import logger from "../utils/logger";
import type { PDFFormat } from "@/types/pdfFormat";

function formatTime(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return hours > 0 ? `${hours}h ${minutes}m ${seconds}s` : `${minutes}m ${seconds}s`;
}

export default function Home() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [loading, setLoading] = useState(false);
  const [previewData, setPreviewData] = useState<any[][] | null>(null);
  const [excelBlob, setExcelBlob] = useState<Blob | null>(null);
  const [fileName, setFileName] = useState<string>("consolidado.xlsx");
  const [isExpanded, setIsExpanded] = useState(false);
  const [totalProcesados, setTotalProcesados] = useState(0);
  const [totalExitosos, setTotalExitosos] = useState(0);
  const [totalFallidos, setTotalFallidos] = useState(0);
  const [formatMessage, setFormatMessage] = useState("");
  const [apiError, setApiError] = useState<string | null>(null);
  const [duration, setDuration] = useState<number | null>(null);
  const [progressCount, setProgressCount] = useState(0);
  const [estimatedSeconds, setEstimatedSeconds] = useState(0);
  const [pdfFormat, setPdfFormat] = useState<PDFFormat | null>(null);
  const [showInstructions, setShowInstructions] = useState(true);

  const memoizedPreviewData = useMemo(() => previewData, [previewData]);
  const memoizedHeaders = useMemo(() => memoizedPreviewData?.[0] || [], [memoizedPreviewData]);
  const memoizedRows = useMemo(() => memoizedPreviewData?.slice(1) || [], [memoizedPreviewData]);

  const [listHeight, setListHeight] = useState(() =>
    Math.min(
      typeof window !== "undefined" ? window.innerHeight - 180 : 420,
      Math.max(memoizedRows.length || 1) * 35,
      200
    )
  );

  useEffect(() => {
    function updateHeight() {
      setListHeight(
        Math.min(
          typeof window !== "undefined" ? window.innerHeight - 180 : 420,
          Math.max(memoizedRows.length || 1) * 35,
          200
        )
      );
    }
    window.addEventListener("resize", updateHeight);
    updateHeight();
    return () => window.removeEventListener("resize", updateHeight);
  }, [memoizedRows.length]);

  useEffect(() => {
    if (isExpanded) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isExpanded]);

  useEffect(() => {
    if (showInstructions) {
      document.body.style.overflow = "hidden";
    } else if (!isExpanded) {
      document.body.style.overflow = "";
    }
    return () => {
      if (!isExpanded) document.body.style.overflow = "";
    };
  }, [showInstructions, isExpanded]);

  const resetResults = () => {
    setPreviewData(null);
    setExcelBlob(null);
    setFileName("consolidado.xlsx");
    setTotalProcesados(0);
    setTotalExitosos(0);
    setTotalFallidos(0);
    setFormatMessage("");
    setApiError(null);
    setDuration(null);
    setProgressCount(0);
    setEstimatedSeconds(0);
  };

  const handleFileChange = (fileList: FileList | null) => {
    setFiles(fileList);
    resetResults();
  };

  const handleFormatChange = (format: PDFFormat) => {
    setPdfFormat(format);
    resetResults();
  };

  const handleLimpiar = () => {
    setFiles(null);
    setPdfFormat(null);
    resetResults();

    // Solución: Reiniciar el valor del input de archivos para permitir nuevas selecciones
    const fileInput = document.getElementById("file-upload") as HTMLInputElement;
    if (fileInput) {
      fileInput.value = "";
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!files || files.length === 0) {
      alert("No se han seleccionado archivos.");
      return;
    }
    if (!pdfFormat) {
      alert("Por favor, selecciona un formato antes de convertir.");
      return;
    }
    if (!validatePDFFiles(files)) {
      alert("Uno o más archivos no son válidos.");
      return;
    }
    const startTime = Date.now();
    setLoading(true);
    setApiError(null);
    const formData = new FormData();
    Array.from(files).forEach((file) => {
      formData.append("pdf", file);
    });
    formData.append("pdfFormat", pdfFormat);
    try {
      const response = await fetch("/api/convert", {
        method: "POST",
        body: formData,
      });
      if (!response.ok || !response.body) {
        throw new Error("Error en la respuesta del servidor");
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let partial = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        partial += decoder.decode(value, { stream: true });
        const events = partial.split("\n\n");
        partial = events.pop() || "";
        for (const evt of events) {
          if (!evt.trim()) continue;
          const lines = evt.trim().split("\n");
          for (const line of lines) {
            if (line.startsWith("data:")) {
              const jsonString = line.replace(/^data:\s?/, "");
              if (!jsonString.trim()) continue;
              const data = JSON.parse(jsonString);
              if (data.progress !== undefined && data.total !== undefined) {
                setProgressCount(data.progress);
                if (data.successes !== undefined) setTotalExitosos(data.successes);
                if (data.failures !== undefined) setTotalFallidos(data.failures);
                setEstimatedSeconds(Math.round(data.estimatedMsLeft / 1000));
              }
              if (data.final) {
                if (data.final.error) {
                  setApiError(data.final.error);
                }
                setTotalProcesados(data.final.totalProcesados);
                setTotalExitosos(data.final.totalExitosos);
                setTotalFallidos(data.final.totalFallidos);
                setFormatMessage(data.final.message || "");
                if (data.final.excel) {
                  const byteCharacters = atob(data.final.excel);
                  const byteNumbers = new Array(byteCharacters.length);
                  for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                  }
                  const byteArray = new Uint8Array(byteNumbers);
                  const blob = new Blob([byteArray], {
                    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                  });
                  setExcelBlob(blob);
                  setFileName(decodeURIComponent(data.final.fileName));
                  const rows = await readXlsxFile(blob);
                  setPreviewData(rows);
                } else {
                  setExcelBlob(null);
                  setPreviewData(null);
                }
                reader.cancel();
              }
            }
          }
        }
      }
    } catch (error: any) {
      logger.error("Error:", error);
      alert("Ocurrió un error");
    } finally {
      setLoading(false);
      const endTime = Date.now();
      setDuration((endTime - startTime) / 1000);
    }
  };

  return (
    <>
      {showInstructions && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100vw",
            height: "100vh",
            background: "rgba(33,37,41,0.45)",
            zIndex: 3001,
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "center",
            overflowY: "auto",
          }}
        >
          <InstructionsModal onClose={() => setShowInstructions(false)} />
        </div>
      )}

      <div className="container my-5">
        <div className="row justify-content-center">
          <div className="col-12 col-lg-10">
            <div className="card shadow-lg border-0">
              <div
                className="card-header bg-gradient text-white text-center py-4"
                style={{
                  background: "#f8f9fa",
                  borderBottom: "1px solid #e3e6ea",
                }}
              >
                <h1
                  className="mb-1 fw-bold"
                  style={{
                    letterSpacing: "1px",
                    color: "#222",
                  }}
                >
                  <i className="bi bi-table me-2" style={{ color: "#333" }}></i>
                  Conversor de PDFs a Excel
                </h1>
                <p className="mb-0 fs-6" style={{ color: "#555" }}>
                  Convierte tus documentos PDF en hojas de cálculo Excel de forma rápida y sencilla.
                </p>
              </div>
              <div className="card-body px-3 px-md-5 py-4" style={{ background: "#f8f9fa" }}>
                {apiError && (
                  <div className="alert alert-warning text-center shadow-sm">{apiError}</div>
                )}
                {formatMessage && (
                  <div className="alert alert-info text-center shadow-sm">{formatMessage}</div>
                )}

                <form onSubmit={handleSubmit}>
                  <FileSelector
                    files={files}
                    loading={loading}
                    onFileChange={handleFileChange}
                  />
                  <FormatSelector
                    pdfFormat={pdfFormat}
                    loading={loading}
                    onFormatChange={handleFormatChange}
                  />
                  <div className="d-flex flex-wrap justify-content-center gap-3 mb-4">
                    <button
                      type="submit"
                      className="btn btn-dark px-4 shadow-sm d-flex align-items-center gap-2"
                      disabled={loading}
                      style={{
                        minWidth: 180,
                        minHeight: 44,
                        fontWeight: 600,
                        fontSize: "1.08rem",
                        margin: "4px",
                      }}
                    >
                      {loading ? (
                        <>
                          <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                          Procesando...
                        </>
                      ) : (
                        <>
                          <i className="bi bi-arrow-right-circle me-2"></i>
                          Convertir
                        </>
                      )}
                    </button>
                    <button
                      type="button"
                      className="btn btn-outline-dark px-4 shadow-sm d-flex align-items-center gap-2"
                      onClick={handleLimpiar}
                      disabled={loading}
                      style={{
                        minWidth: 180,
                        minHeight: 44,
                        fontWeight: 600,
                        fontSize: "1.08rem",
                        margin: "4px",
                      }}
                    >
                      <i className="bi bi-x-circle me-2"></i>
                      Limpiar
                    </button>
                  </div>
                </form>

                <ProcessingSummary
                  loading={loading}
                  files={files}
                  progressCount={progressCount}
                  totalProcesados={totalProcesados}
                  totalExitosos={totalExitosos}
                  totalFallidos={totalFallidos}
                  duration={duration}
                  estimatedSeconds={estimatedSeconds}
                  formatTime={formatTime}
                />

                {previewData && (
                  <PreviewTable
                    memoizedHeaders={memoizedHeaders}
                    memoizedRows={memoizedRows}
                    setIsExpanded={setIsExpanded}
                    excelBlob={excelBlob}
                    fileName={fileName}
                  />
                )}
              </div>
            </div>
          </div>
        </div>

        {isExpanded && previewData && (
          <ExpandedView
            memoizedHeaders={memoizedHeaders}
            memoizedRows={memoizedRows}
            listHeight={listHeight}
            setIsExpanded={setIsExpanded}
          />
        )}
      </div>
    </>
  );
}
