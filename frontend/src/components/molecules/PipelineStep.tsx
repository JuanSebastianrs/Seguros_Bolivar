import * as React from "react"
import { cn } from "@/lib/utils"
import { CheckCircle2, Circle } from "lucide-react"

export type StepStatus = "pending" | "loading" | "success" | "error"

interface PipelineStepProps extends React.HTMLAttributes<HTMLDivElement> {
  number: number
  title: string
  description?: string
  status: StepStatus
  isLast?: boolean
}

export function PipelineStep({ number, title, description, status, isLast, className, ...props }: PipelineStepProps) {
  return (
    <div className={cn("relative flex gap-4", className)} {...props}>
      {!isLast && (
        <div className={cn("absolute left-4 top-8 bottom-[-16px] w-[2px]", 
          status === "success" ? "bg-slate-800" : "bg-slate-200"
        )} />
      )}
      
      <div className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-background mt-1">
        {status === "success" && <CheckCircle2 className="h-8 w-8 text-slate-900 fill-slate-900 text-white" />}
        
        {status === "loading" && (
           <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100">
             <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
           </div>
        )}
        
        {status === "error" && <Circle className="h-8 w-8 text-destructive fill-destructive/20" />}
        
        {status === "pending" && (
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-slate-400 font-semibold text-sm">
            {number}
          </div>
        )}
      </div>

      <div className="flex flex-col pb-6 pt-1">
        <span className={cn("text-sm font-bold", status === "pending" ? "text-slate-400" : "text-slate-800")}>
          {title}
        </span>
        {description && (
          <span className="text-xs text-slate-500 mt-1">{description}</span>
        )}
      </div>
    </div>
  )
}
