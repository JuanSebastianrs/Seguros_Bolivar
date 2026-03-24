import * as React from "react"
import { cn } from "@/lib/utils"

interface FormFieldProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string
  htmlFor?: string
  description?: string
  children: React.ReactNode
}

export function FormField({ label, htmlFor, description, children, className, ...props }: FormFieldProps) {
  return (
    <div className={cn("space-y-2", className)} {...props}>
      <label htmlFor={htmlFor} className="text-xs font-bold text-slate-500 uppercase tracking-wider">
        {label}
      </label>
      {children}
      {description && <p className="text-xs text-slate-500">{description}</p>}
    </div>
  )
}
