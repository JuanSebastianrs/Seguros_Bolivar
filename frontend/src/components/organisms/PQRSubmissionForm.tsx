import * as React from "react"
import { Textarea } from "@/components/ui/textarea"
import { Select } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { FormField } from "@/components/molecules/FormField"
import { Button } from "@/components/ui/button"
import { Sparkles } from "lucide-react"

export interface FormValues {
  compania: string;
  descripcion: string;
  simularFalla: boolean;
  simularDuplicado: boolean;
}

interface Props {
  onSubmit: (values: FormValues) => void;
  isLoading: boolean;
}

const COMPANIES = [
  { value: "GASES DEL ORINOCO", label: "Gases del Orinoco" },
  { value: "MENSAJERIA DEL VALLE", label: "Mensajería del Valle" },
  { value: "LOGISTICA ANDINA", label: "Logística Andina" },
  { value: "TECH SOLUTIONS", label: "Tech Solutions" },
  { value: "ACME CORP", label: "Empresa Inexistente (Error 404)" },
];

export function PQRSubmissionForm({ onSubmit, isLoading }: Props) {
  const [compania, setCompania] = React.useState(COMPANIES[0].value)
  const [descripcion, setDescripcion] = React.useState("")
  const [simularFalla, setSimularFalla] = React.useState(false)
  const [simularDuplicado, setSimularDuplicado] = React.useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!descripcion.trim()) return;
    onSubmit({ compania, descripcion, simularFalla, simularDuplicado })
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6 bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-100">
      <FormField label="Organización Cliente" htmlFor="compania">
        <Select 
          id="compania" 
          value={compania} 
          onChange={(e) => setCompania(e.target.value)} 
          options={COMPANIES} 
          disabled={isLoading}
        />
      </FormField>

      <FormField 
        label="Descripción de la PQR" 
        htmlFor="descripcion"
      >
        <Textarea 
          id="descripcion" 
          placeholder="Ingrese el detalle de la petición, queja o reclamo. El motor de IA analizará sentimiento, urgencia e intención técnica..."
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          required
          disabled={isLoading}
        />
      </FormField>

      <div className="flex items-center justify-between pt-2">
        <div className="flex flex-col">
          <span className="text-sm font-bold text-slate-800">Simular Falla de Red BPO</span>
          <span className="text-xs text-slate-500">Bono +4% — Resiliencia ante caída de plataforma externa</span>
        </div>
        <Switch checked={simularFalla} onCheckedChange={setSimularFalla} disabled={isLoading} />
      </div>

      <div className="flex items-center justify-between">
        <div className="flex flex-col">
          <span className="text-sm font-bold text-slate-800">Simular Solicitud Duplicada</span>
          <span className="text-xs text-slate-500">Bono +4% — Demuestra idempotencia (HTTP 409)</span>
        </div>
        <Switch checked={simularDuplicado} onCheckedChange={setSimularDuplicado} disabled={isLoading} />
      </div>

      <Button type="submit" size="lg" className="w-full mt-2 bg-slate-900 text-white hover:bg-slate-800 gap-2 transition-all" disabled={isLoading || !descripcion.trim()}>
        <Sparkles className="w-4 h-4" />
        {isLoading ? "Procesando con IA..." : "Procesar con IA"}
      </Button>
    </form>
  )
}
