import * as React from "react"

export function RawJSONViewer({ data }: { data: any }) {
  if (!data) return null;
  return (
    <div className="mt-6 bg-[#0a0f1c] rounded-lg border border-slate-800/80 overflow-hidden text-left shadow-inner">
      <div className="px-4 py-2 border-b border-slate-800 flex justify-between items-center bg-slate-900/80">
        <span className="text-[10px] uppercase tracking-widest text-slate-400 font-bold flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
          Developer Raw JSON
        </span>
      </div>
      <div className="p-4 overflow-auto max-h-[200px] scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
        <pre className="text-[11px] font-mono text-emerald-400/90 leading-relaxed break-all whitespace-pre-wrap">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    </div>
  )
}
