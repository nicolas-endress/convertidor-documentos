// src/services/pdfService.ts
import pLimit from "p-limit";
import { procesarPDF } from "@/utils/pdf/pdfUtils";
import { generateExcel, ExcelStats } from "@/utils/excel/excelUtils"; // <-- Usamos la función generateExcel
import type { PDFFormat } from "@/types/pdfFormat";

export type ConversionSuccess = {
  fileName: string;
  datos: Record<string, string>;
  titulo?: string;
  regexes?: Record<string, RegExp> | null;
};

export type ConversionFailure = {
  fileName: string;
  error: string;
};

// Exportamos SettledFailure para que otros módulos puedan importarlo si lo requieren
export type SettledFailure = {
  status: "rejected";
  reason: {
    fileName: string;
    error: string;
  };
};

// Elimina el genérico T y usa ConversionSuccess directamente
type SettledSuccess = { status: "fulfilled"; value: ConversionSuccess };
export type SettledResult = SettledSuccess | SettledFailure;

interface ProcessOptions {
  files: File[];
  pdfFormat: PDFFormat;
  returnRegex: boolean;
  onEvent: (data: any) => void;
  concurrency?: number; // Nuevo parámetro opcional
}

/**
 * Procesa un arreglo de archivos PDF en lotes para evitar bloquear el event loop.
 * Emite eventos de progreso y retorna un arreglo de resultados "settled" para cada archivo.
 */
export async function processPDFFiles({
  files,
  pdfFormat,
  returnRegex,
  onEvent,
  concurrency = 15,
}: ProcessOptions): Promise<SettledResult[]> {
  const limit = pLimit(concurrency);
  const totalFiles = files.length;
  let processedCount = 0;
  let successesCount = 0;
  let failuresCount = 0;
  const start = Date.now(); // <-- Marca el inicio global

  const results: SettledResult[] = [];
  const batchSize = 100; // Ajusta el tamaño del lote según tu servidor

  for (let i = 0; i < files.length; i += batchSize) {
    const batch = files.slice(i, i + batchSize);
    const promises: Array<Promise<SettledResult>> = batch.map((file) =>
      limit(async () => {
        try {
          const result = await procesarPDF(file, pdfFormat, returnRegex);
          processedCount++;
          successesCount++;
          const elapsedMsSoFar = Date.now() - start; // <-- Tiempo real transcurrido
          const avgTimePerFile = elapsedMsSoFar / processedCount;
          const remaining = totalFiles - processedCount;
          const estimatedMsLeft = Math.round(avgTimePerFile * remaining);

          onEvent({
            progress: processedCount,
            total: totalFiles,
            file: file.name,
            status: "fulfilled",
            estimatedMsLeft,
            elapsedMsSoFar, // <-- Envía el tiempo real transcurrido
            successes: successesCount,
            failures: failuresCount,
          });

          return {
            status: "fulfilled",
            value: {
              fileName: file.name,
              ...result,
            },
          } as SettledSuccess;
        } catch (error: any) {
          processedCount++;
          failuresCount++;
          const elapsedMsSoFar = Date.now() - start;
          const avgTimePerFile = elapsedMsSoFar / processedCount;
          const remaining = totalFiles - processedCount;
          const estimatedMsLeft = Math.round(avgTimePerFile * remaining);

          let errorMsg = error.message || "Error desconocido";
          if (errorMsg.includes("Se detectó que pertenece a:")) {
            errorMsg = errorMsg.replace(
              /Se detectó que pertenece a:\s*(.*)/,
              '<span style="background-color: yellow; font-weight: bold;">Se detectó que pertenece a: $1</span>'
            );
          }

          onEvent({
            progress: processedCount,
            total: totalFiles,
            file: file.name,
            status: "rejected",
            error: errorMsg,
            estimatedMsLeft,
            elapsedMsSoFar, // <-- Envía el tiempo real transcurrido
            successes: successesCount,
            failures: failuresCount,
          });

          return {
            status: "rejected",
            reason: {
              fileName: file.name,
              error: errorMsg,
            },
          } as SettledFailure;
        }
      })
    );

    // Espera a que termine el lote actual
    const batchResults = await Promise.all(promises);
    results.push(...batchResults);

    // Cede el control al event loop para evitar bloquear el servidor
    await new Promise<void>((resolve) => setImmediate(resolve));
  }

  return results;
}

/**
 * Genera un Excel a partir de los resultados exitosos y, opcionalmente, incluye la hoja de estadísticas.
 * Llama internamente a generateExcel (definida en excelUtils.ts).
 */
export async function generateExcelFromResults(
  successes: ConversionSuccess[],
  pdfFormat: PDFFormat,
  stats?: ExcelStats
): Promise<{ excelBuffer: Buffer; fileName: string }> {
  let baseFileName = "";
  switch (pdfFormat) {
    case "CERTIFICADO_DE_HOMOLOGACION":
      baseFileName = "Certificado de Homologación";
      break;
    case "CRT":
      baseFileName = "Certificado de Revisión Técnica (CRT)";
      break;
    case "SOAP":
      baseFileName = "Seguro Obligatorio (SOAP)";
      break;
    case "PERMISO_CIRCULACION":
      baseFileName = "Permiso de Circulación";
      break;
    default:
      baseFileName = "Consolidado";
  }

  // Siempre usar el nombre base, nunca el título extraído del PDF
  const nombreArchivo = baseFileName;

  const registros = successes.map((r) => ({
    "Nombre PDF": r.fileName,
    ...r.datos, // Los campos extraídos del PDF
  })) as Array<{ [key: string]: any }>;

  const { buffer, encodedName } = await generateExcel(registros, nombreArchivo, pdfFormat, stats);
  return { excelBuffer: buffer, fileName: encodedName };
}
