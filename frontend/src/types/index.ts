export type StepStatus = "pending" | "loading" | "success" | "error";

export interface PipelineInfo {
  step: number;
  message: string;
  status: StepStatus;
  description?: string;
}

export interface SolicitudOutput {
  compania: string;
  solicitud_id: string;
  Solicitud_fecha: string;
  solicitud_tipo: string;
  solicitud_prioridad: string;
  solicitud_id_cliente: string;
  solicitud_tipo_id_cliente: string;
  solicitud_id_plataforma_externa: string | null;
  proximo_paso: string;
  justificacion: string;
  estado: string;
}
