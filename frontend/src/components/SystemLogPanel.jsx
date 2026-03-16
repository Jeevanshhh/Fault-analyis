import React, { useContext, useEffect, useRef } from 'react'
import { GridContext } from '../App'

export default function SystemLogPanel() {
    const { gridState } = useContext(GridContext)
    const logs = gridState?.system_logs || []
    const scrollRef = useRef(null)

    // Auto-scroll to the top/latest securely (since backend unshifts to index 0, they are already top-to-bottom or bottom-to-top depending on how we render)
    // The backend inserts at 0, meaning new logs are at the top.
    
    return (
        <div className="glass-card flex flex-col h-64 p-4 text-sm">
            <h3 className="text-gray-300 font-semibold mb-3 tracking-wider text-xs uppercase flex items-center justify-between">
                <span>System Log</span>
                <div className="flex space-x-1">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                </div>
            </h3>

            <div 
                ref={scrollRef}
                className="flex-1 overflow-y-auto pr-2 space-y-2 font-mono"
            >
                {logs.length === 0 ? (
                    <div className="text-gray-500 text-xs italic">Awaiting system events...</div>
                ) : (
                    logs.map((log, i) => {
                        // Highlight specific keywords for better visual tracing
                        const isFault = log.message.toLowerCase().includes('fault')
                        const isIso = log.message.toLowerCase().includes('isolat') || log.message.toLowerCase().includes('breaker')
                        const isRestore = log.message.toLowerCase().includes('restor') || log.message.toLowerCase().includes('rerout')

                        let colorClass = "text-gray-400"
                        if (isFault) colorClass = "text-red-400"
                        else if (isIso) colorClass = "text-blue-400"
                        else if (isRestore) colorClass = "text-amber-400"

                        return (
                            <div key={i} className="flex gap-2 text-xs border-b border-gray-800/50 pb-1">
                                <span className="text-gray-500 shrink-0">[{log.timestamp}]</span>
                                <span className={`${colorClass}`}>{log.message}</span>
                            </div>
                        )
                    })
                )}
            </div>
        </div>
    )
}
