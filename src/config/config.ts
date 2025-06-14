// src/config/config.ts
// Configuración mínima para el convertidor PDF a Excel

export const MAX_FILE_SIZE = parseInt(process.env.NEXT_PUBLIC_MAX_FILE_SIZE || "5242880", 10); 
// Si NEXT_PUBLIC_MAX_FILE_SIZE no está definido, se usa 5MB (5242880 bytes) por defecto.
