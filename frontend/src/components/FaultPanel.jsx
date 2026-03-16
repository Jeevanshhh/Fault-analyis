import React, { useContext, useState } from 'react'
import { GridContext } from '../App'

const NODES = ['bus_2', 'bus_3', 'bus_4', 'bus_5', 'bus_6', 'bus_7', 'bus_8', 'bus_9', 'bus_10', 'bus_11', 'bus_12']
const FAULT_TYPES = ['line_fault', 'ground_fault', 'short_circuit', 'voltage_sag', 'overload']

function timeAgo(ts) {
    if (!ts) return ''
    const diff = (Date.now() - new Date(ts).getTime()) / 1000
    if (diff < 60) return `${Math.floor(diff)}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    return `${Math.floor(diff / 3600)}h ago`
}

export default function FaultPanel() {
    const { gridState, injectFault } = useContext(GridContext)
    const [injectNode, setInjectNode] = useState('bus_4')
    const [injectType, setInjectType] = useState('line_fault')
    const [showInject, setShowInject] = useState(false)

    const activeFaults = gridState?.active_faults || []
    const nodes = gridState?.nodes || []
    const faultedNodes = nodes.filter(n => n.status === 'fault')

    const handleInject = () => {
        injectFault(injectNode, injectType)
        setShowInject(false)
    }

    return (
        <div className="glass-card p-4">
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <span className="text-red-400 text-sm">▲</span>
                    <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Fault Monitor</h2>
                    {activeFaults.length > 0 && (
                        <span className="badge badge-fault">{activeFaults.length}</span>
                    )}
                </div>
                <button className="btn-inject" onClick={() => setShowInject(!showInject)}>
                    {showInject ? 'Cancel' : '+ Inject Fault'}
                </button>
            </div>

            {/* Inject Form */}
            {showInject && (
                <div className="mb-3 p-3 rounded-lg animate-slide-up" style={{ background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.2)' }}>
                    <div className="flex gap-2 mb-2">
                        <select
                            value={injectNode}
                            onChange={(e) => setInjectNode(e.target.value)}
                            className="flex-1 bg-transparent border border-slate-700 rounded px-2 py-1 text-xs text-slate-300 focus:border-cyan-500 outline-none"
                        >
                            {NODES.map(n => <option key={n} value={n}>{n}</option>)}
                        </select>
                        <select
                            value={injectType}
                            onChange={(e) => setInjectType(e.target.value)}
                            className="flex-1 bg-transparent border border-slate-700 rounded px-2 py-1 text-xs text-slate-300 focus:border-cyan-500 outline-none"
                        >
                            {FAULT_TYPES.map(t => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
                        </select>
                    </div>
                    <button
                        onClick={handleInject}
                        className="w-full bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-red-400 py-1.5 rounded text-xs font-semibold transition-all"
                    >
                        Inject Fault
                    </button>
                </div>
            )}

            {/* Fault List */}
            <div className="space-y-2 max-h-48 overflow-y-auto">
                {activeFaults.length === 0 ? (
                    <div className="text-center py-6">
                        <div className="text-2xl mb-1">&#9889;</div>
                        <p className="text-xs text-slate-500">No active faults</p>
                        <p className="text-[10px] text-slate-600 mt-1">System operating normally</p>
                    </div>
                ) : (
                    activeFaults.map((fault, i) => (
                        <div
                            key={fault.id || i}
                            className={`p-2.5 rounded-lg border animate-slide-up ${fault.severity === 'high'
                                    ? 'fault-pulse border-red-500/30 bg-red-500/5'
                                    : 'border-slate-700/50 bg-slate-800/30'
                                }`}
                            style={{ animationDelay: `${i * 100}ms` }}
                        >
                            <div className="flex justify-between items-start">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="font-mono text-xs font-bold text-slate-200">{fault.node_id}</span>
                                        <span className={`badge badge-${fault.severity}`}>{fault.severity}</span>
                                    </div>
                                    <p className="text-[10px] text-slate-500 mt-0.5">{fault.fault_type?.replace(/_/g, ' ')}</p>
                                </div>
                                <span className="text-[10px] text-slate-600 font-mono">{timeAgo(fault.timestamp)}</span>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Faulted Nodes Summary */}
            {faultedNodes.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-700/50">
                    <p className="text-[10px] text-slate-500 mb-1">Affected nodes</p>
                    <div className="flex flex-wrap gap-1">
                        {faultedNodes.map(n => (
                            <span key={n.node_id} className="badge badge-fault">{n.node_id}</span>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
