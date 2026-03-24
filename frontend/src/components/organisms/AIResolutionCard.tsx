import * as React from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { DataRow } from "@/components/molecules/DataRow"
import { SolicitudOutput } from "@/types"
import { RawJSONViewer } from "./RawJSONViewer"

interface Props {
  result: SolicitudOutput | null;
  onReset: () => void;
}

export function AIResolutionCard({ result, onReset }: Props) {
  if (!result) {
    return (
      <div className="bg-slate-950 text-slate-400 p-8 rounded-2xl flex flex-col items-center justify-center h-full text-center border border-slate-800">
        <p>A la espera de una nueva petición para iniciar el análisis...</p>
      </div>
    )
  }

  const isSuccess = result.estado !== "error";
  
  if (!isSuccess) {
    return (
      <div className="bg-[#1e1114] text-white p-6 sm:p-8 rounded-2xl shadow-xl flex flex-col h-full border border-rose-900/40 relative overflow-hidden">
        <div className="mb-6">
          <Badge variant="outline" className="border-rose-900/50 text-rose-400 font-mono text-xs px-3 py-1 bg-transparent">
            PIPELINE ABORTADO
          </Badge>
        </div>
        <div className="mb-8">
          <h2 className="text-2xl font-bold leading-tight mb-2 text-rose-500">Error de Procesamiento</h2>
          <p className="text-sm text-rose-200/70 leading-relaxed font-light">
            El Orquestador detuvo la ejecución debido a una excepción en los pasos de validación o red.
          </p>
        </div>
        
        <div className="mb-8 p-4 bg-rose-950/30 border border-rose-900/50 rounded-lg">
           <p className="text-[10px] uppercase tracking-widest text-rose-400 font-bold mb-2">Detalle Técnico (Exception)</p>
           <p className="text-sm text-slate-300 font-mono">{result.justificacion}</p>
        </div>

        <div className="mt-auto">
          <Button onClick={onReset} className="w-full bg-slate-800 hover:bg-slate-700 text-white font-semibold">
            NUEVA SOLICITUD
          </Button>
        </div>
        <RawJSONViewer data={result} />
      </div>
    )
  }

  const priorityColor = 
    result.solicitud_prioridad?.toLowerCase() === "alta" ? "danger" : 
    result.solicitud_prioridad?.toLowerCase() === "media" ? "warning" : 
    result.solicitud_prioridad?.toLowerCase() === "baja" ? "success" : "default";

  return (
    <div className="bg-[#0f172a] text-white p-6 sm:p-8 rounded-2xl shadow-xl flex flex-col h-full border border-slate-800 relative overflow-hidden">
      {/* Etiqueta superior */}
      <div className="flex justify-between items-center mb-6">
        <Badge variant="outline" className="border-slate-700 text-slate-300 font-mono text-xs px-3 py-1 bg-transparent">
          TICKET {result.solicitud_id}
        </Badge>
        <Badge variant={priorityColor} className="uppercase px-3 py-1 text-[10px] tracking-wider font-bold">
          Prioridad {result.solicitud_prioridad}
        </Badge>
      </div>

      <div className="mb-8">
        <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-2">Resolución Sugerida</p>
        <h2 className="text-2xl font-bold leading-tight mb-4 text-slate-50">{result.solicitud_tipo}</h2>
        <div className="flex gap-2">
           <Badge variant="secondary" className="bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors">
             {result.proximo_paso.replace(/_/g, " ")}
           </Badge>
           <Badge variant="secondary" className="bg-slate-800 text-emerald-400 hover:bg-slate-700 transition-colors">
             SLA Inteligente
           </Badge>
        </div>
      </div>

      <div className="mb-8 border-t border-slate-800/60 pt-6">
        <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-3">Justificación del Motor (IA)</p>
        <p className="text-sm text-slate-300 leading-relaxed font-light">
          {result.justificacion}
        </p>
      </div>

      <div className="mt-auto flex flex-col gap-2">
        <div className="bg-slate-900/50 rounded-lg p-3 mb-4 space-y-1 border border-slate-800/50">
           <DataRow label="ID Cliente" value={`${result.solicitud_tipo_id_cliente} ${result.solicitud_id_cliente}`} />
           <DataRow label="ID Externo" value={result.solicitud_id_plataforma_externa || "N/A"} className="border-none pb-0" />
        </div>

        <div className="flex gap-3">
          <Button onClick={onReset} className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold outline-none border-none">
            APROBAR Y ENRUTAR
          </Button>
        </div>
      </div>
      
      {/* Developer Raw JSON Footer */}
      <RawJSONViewer data={result} />
    </div>
  )
}
