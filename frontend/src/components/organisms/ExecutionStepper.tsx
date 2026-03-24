import * as React from "react"
import { PipelineStep } from "@/components/molecules/PipelineStep"
import { PipelineInfo } from "@/types"

interface Props {
  currentStep: number;
  stepsInfo: PipelineInfo[];
}

const DEFAULT_STEPS = [
  { id: 1, title: "Validar Información", text: "Extrayendo entidades clave" },
  { id: 2, title: "Clasificar Intención", text: "Mapeando con reglas de negocio" },
  { id: 3, title: "Calcular Prioridad", text: "Delegando a IA o Reglas" },
  { id: 4, title: "Generar Justificación", text: "Redactando respuesta ejecutiva" },
  { id: 5, title: "Enrutar Caso", text: "Decidiendo flujo de cierre" },
  { id: 6, title: "Gestión Externa", text: "Simulando CRM Externo" },
];

export function ExecutionStepper({ currentStep, stepsInfo }: Props) {
  
  const getStatus = (stepNumber: number) => {
    const info = stepsInfo.find(s => s.step === stepNumber);
    if (info) return info.status;
    if (currentStep > stepNumber) return "success";
    if (currentStep === stepNumber) return "loading";
    return "pending";
  }

  const getDescription = (stepNumber: number, defaultText: string) => {
    const info = stepsInfo.find(s => s.step === stepNumber);
    return info?.description || defaultText;
  }

  return (
    <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-100 flex flex-col h-full w-full">
      <div className="flex flex-col gap-6 w-full max-w-[280px] mx-auto py-4">
        {DEFAULT_STEPS.map((step, idx) => (
          <PipelineStep
            key={step.id}
            number={step.id}
            title={step.title}
            description={getDescription(step.id, step.text)}
            status={getStatus(step.id)}
            isLast={idx === DEFAULT_STEPS.length - 1}
          />
        ))}
      </div>
    </div>
  )
}
