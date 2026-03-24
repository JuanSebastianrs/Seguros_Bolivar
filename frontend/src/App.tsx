import { useState, useRef, useEffect } from "react"
import { PQRSubmissionForm, FormValues } from "./components/organisms/PQRSubmissionForm"
import { ExecutionStepper } from "./components/organisms/ExecutionStepper"
import { AIResolutionCard } from "./components/organisms/AIResolutionCard"
import { SolicitudOutput, PipelineInfo } from "./types"

function App() {
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<SolicitudOutput | null>(null)
  
  // Pipeline State
  const [currentStep, setCurrentStep] = useState(0)
  const [stepsInfo, setStepsInfo] = useState<PipelineInfo[]>([])
  
  const timerRef = useRef<number | null>(null)

  const handleSubmit = async (values: FormValues) => {
    setIsLoading(true)
    setResult(null)
    setCurrentStep(1)
    setStepsInfo([])
    
    // Fake progressive loader UX para simular los pasos de la IA
    let step = 1;
    timerRef.current = window.setInterval(() => {
      if (step < 5) {
        step++;
        setCurrentStep(step);
      }
    }, 1200); 

    try {
      const resp = await fetch(`http://localhost:8000/api/v1/solicitudes?simular_fallos_bpo=${values.simularFalla}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          compania: values.compania,
          solicitud_id: `REQ-${Math.floor(Math.random() * 10000)}`,
          solicitud_descripcion: values.descripcion
        })
      });

      const data = await resp.json()
      
      clearInterval(timerRef.current!)
      setCurrentStep(6) // Fin
      
      if (!resp.ok) {
        setStepsInfo([{ step: 6, status: "error", message: data.detail || "Error de red" }])
        setResult({
           ...data,
           estado: "error",
           justificacion: `HTTP ${resp.status}: ${data.detail || 'Operación Fallida'}`
        } as SolicitudOutput)
        return
      }

      setResult(data)
    } catch {
      clearInterval(timerRef.current!)
      setCurrentStep(6)
      setStepsInfo([{ step: 6, status: "error", message: "Error de conexión" }])
      setResult({
        estado: "error",
        justificacion: "Fallo de conexión al backend. Asegúrese de que el servidor FastAPI esté corriendo en el puerto 8000."
      } as SolicitudOutput)
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    setResult(null)
    setCurrentStep(0)
    setStepsInfo([])
  }

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 flex flex-col">
      <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between sticky top-0 z-50">
        <div>
          <h1 className="text-xl font-bold tracking-tight">BPO AI Orchestrator</h1>
          <p className="text-[11px] text-slate-500 font-medium uppercase tracking-widest mt-1">Propuesta Técnica Seguros Bolívar - Por Juan Sebastián Rodríguez Salazar</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-xs font-bold ring-1 ring-emerald-600/20">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            SISTEMA ACTIVO
          </div>
          <div className="hidden md:flex flex-col text-right">
             <span className="text-sm font-bold">Juan Sebastián Rodríguez Salazar</span>
             <span className="text-xs text-slate-400">Project Lead</span>
          </div>
          <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center font-bold text-slate-600 border border-slate-200">
            JS
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto p-4 sm:p-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
          
          {/* Col 1: Formulario */}
          <div className="lg:col-span-4 flex flex-col">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Configuración de Entrada</h2>
            <h3 className="text-3xl font-bold mb-6 text-slate-800 tracking-tight">Contexto del Caso</h3>
            <PQRSubmissionForm onSubmit={handleSubmit} isLoading={isLoading} />
          </div>

          {/* Col 2: Stepper */}
          <div className="lg:col-span-3 flex flex-col">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Motor de Orquestación</h2>
            <h3 className="text-3xl font-bold mb-6 text-slate-800 tracking-tight">Pipeline de Ejecución</h3>
            <ExecutionStepper currentStep={currentStep} stepsInfo={stepsInfo} />
          </div>

          {/* Col 3: Resultado IA */}
          <div className="lg:col-span-5 flex flex-col">
             <h2 className="text-[10px] font-bold text-transparent uppercase tracking-wider mb-2 select-none">.</h2>
             <h3 className="text-3xl font-bold mb-6 text-transparent select-none tracking-tight">.</h3>
             <AIResolutionCard result={result} onReset={handleReset} />
          </div>

        </div>
      </main>

      <footer className="bg-white border-t border-slate-200 mt-auto py-8 text-center text-slate-500 text-sm">
        <p className="font-semibold text-slate-700 mb-1">Prueba Técnica Seguros Bolívar</p>
        <p>Desarrollado por <span className="font-medium text-slate-900">Juan Sebastián Rodríguez Salazar</span></p>
        <div className="flex justify-center gap-6 mt-4">
          <a href="https://www.linkedin.com/in/juan-sebastian-rs/" target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-blue-600 transition-colors font-medium flex items-center gap-1">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path fillRule="evenodd" d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" clipRule="evenodd" /></svg>
            LinkedIn
          </a>
          <a href="https://github.com/JuanSebastianrs" target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-slate-900 transition-colors font-medium flex items-center gap-1">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" /></svg>
            GitHub
          </a>
        </div>
      </footer>
    </div>
  )
}

export default App
