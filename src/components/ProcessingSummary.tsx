import React from "react";

interface ProcessingSummaryProps {
  loading: boolean;
  files: FileList | null;
  progressCount: number;
  totalProcesados: number;
  totalExitosos: number;
  totalFallidos: number;
  duration: number | null;
  estimatedSeconds: number;
  formatTime: (totalSeconds: number) => string;
}

const ProcessingSummary: React.FC<ProcessingSummaryProps> = ({
  loading,
  files,
  progressCount,
  totalProcesados,
  totalExitosos,
  totalFallidos,
  duration,
  estimatedSeconds,
  formatTime,
}) => {
  return (
    (loading || totalProcesados || totalExitosos || totalFallidos || duration !== null) && (
      <div className="mt-4">
        <h5 className="text-center mb-3 fw-bold">
          <i className="bi bi-bar-chart-line me-2"></i>
          Resumen de Procesamiento
        </h5>
        <div className="row text-center g-2">
          <div className="col-6 col-md-3 mb-2">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body py-2">
                <p className="fw-bold mb-1">Procesados</p>
                <p className="fs-5 mb-0">
                  {loading && files ? `${progressCount} de ${files.length}` : totalProcesados}
                </p>
              </div>
            </div>
          </div>
          <div className="col-6 col-md-3 mb-2">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body py-2">
                <p className="fw-bold text-success mb-1">Exitosos</p>
                <p className="fs-5 mb-0">{totalExitosos}</p>
              </div>
            </div>
          </div>
          <div className="col-6 col-md-3 mb-2">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body py-2">
                <p className="fw-bold text-danger mb-1">Fallidos</p>
                <p className="fs-5 mb-0">{totalFallidos}</p>
              </div>
            </div>
          </div>
          <div className="col-6 col-md-3 mb-2">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body py-2">
                {loading ? (
                  <>
                    <p className="fw-bold mb-1">Estimado</p>
                    <p className="fs-6 mb-0">
                      <i className="bi bi-clock-history me-1"></i>
                      {formatTime(estimatedSeconds)}
                    </p>
                  </>
                ) : duration !== null ? (
                  <>
                    <p className="fw-bold mb-1">Duración</p>
                    <p className="fs-6 mb-0">
                      <i className="bi bi-stopwatch me-1"></i>
                      {formatTime(Math.round(duration))}
                    </p>
                  </>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  );
};

export default ProcessingSummary;
