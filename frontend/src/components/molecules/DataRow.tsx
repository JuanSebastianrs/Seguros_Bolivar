import * as React from "react"
import { cn } from "@/lib/utils"

interface DataRowProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string
  value: React.ReactNode
}

export function DataRow({ label, value, className, ...props }: DataRowProps) {
  return (
    <div className={cn("flex flex-col sm:flex-row sm:items-center justify-between py-2 border-b border-white/10 gap-1", className)} {...props}>
      <span className="text-sm text-slate-400 font-medium">{label}</span>
      <span className="text-sm text-white font-semibold text-right">{value}</span>
    </div>
  )
}
