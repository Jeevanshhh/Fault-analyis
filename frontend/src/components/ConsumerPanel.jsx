import React, { useContext, useMemo } from 'react'
import { GridContext } from '../App'

export default function ConsumerPanel() {
    const { consumers, gridState } = useContext(GridContext)

    // Compute aggregate stats
    const stats = useMemo(() => {
        const total = consumers.length
        const outage = consumers.filter(c => c.status === 'outage').length
        const totalLoad = consumers.reduce((s, c) => s + (c.load_kw || 0), 0)
        const totalCapacity = consumers.reduce((s, c) => s + (c.peak_load_kw || 0), 0)
        return { total, outage, totalLoad, totalCapacity, utilization: totalCapacity > 0 ? totalLoad / totalCapacity * 100 : 0 }
    }, [consumers])

    // Top consumers by load
    const topConsumers = useMemo(() => {
        return [...consumers].sort((a, b) => (b.load_kw || 0) - (a.load_kw || 0)).slice(0, 8)
    }, [consumers])

    const outageConsumers = useMemo(() => {
        return consumers.filter(c => c.status === 'outage')
    }, [consumers])

    return (
        <div className="glass-card p-4">
            {/* Header */}
            <div className="flex items-center gap-2 mb-3">
                <span style={{ color: '#22c55e' }} className="text-sm">&#9632;</span>
                <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Consumer Analytics</h2>
                <span className="badge badge-healthy ml-auto">{stats.total} total</span>
            </div>

            {/* Load Gauge (simple CSS bar) */}
            <div className="mb-4">
                <div className="flex justify-between items-baseline mb-1">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider">System Load Utilization</span>
                    <span className="text-sm font-bold font-mono" style={{ color: stats.utilization > 80 ? '#ef4444' : stats.utilization > 60 ? '#f59e0b' : '#22c55e' }}>
                        {stats.utilization.toFixed(1)}%
                    </span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                    <div
                        className="h-full rounded-full transition-all duration-1000"
                        style={{
                            width: `${Math.min(100, stats.utilization)}%`,
                            background: stats.utilization > 80
                                ? 'linear-gradient(90deg, #f59e0b, #ef4444)'
                                : stats.utilization > 60
                                    ? 'linear-gradient(90deg, #22c55e, #f59e0b)'
                                    : 'linear-gradient(90deg, #00d4ff, #22c55e)',
                        }}
                    />
                </div>
                <div className="flex justify-between mt-1">
                    <span className="text-[9px] text-slate-600 font-mono">{stats.totalLoad.toFixed(0)} kW used</span>
                    <span className="text-[9px] text-slate-600 font-mono">{stats.totalCapacity.toFixed(0)} kW capacity</span>
                </div>
            </div>

            {/* Outage Alert */}
            {outageConsumers.length > 0 && (
                <div className="mb-3 p-2.5 rounded-lg border border-red-500/30 bg-red-500/5 fault-pulse">
                    <div className="flex items-center gap-2 mb-1">
                        <span className="text-red-400 text-xs font-bold">OUTAGE ALERT</span>
                        <span className="badge badge-fault">{outageConsumers.length} affected</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                        {outageConsumers.slice(0, 6).map(c => (
                            <span key={c.consumer_id} className="text-[10px] font-mono text-red-300 bg-red-500/10 px-1.5 py-0.5 rounded">
                                {c.consumer_id} ({c.node_id})
                            </span>
                        ))}
                        {outageConsumers.length > 6 && (
                            <span className="text-[10px] text-red-400">+{outageConsumers.length - 6} more</span>
                        )}
                    </div>
                </div>
            )}

            {/* Top Consumers Table */}
            <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Top Consumers by Load</p>
                <div className="space-y-1">
                    {topConsumers.map((c) => (
                        <div key={c.consumer_id} className="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-slate-800/50 transition-colors">
                            <div className={`w-1.5 h-1.5 rounded-full ${c.status === 'outage' ? 'bg-red-500' : 'bg-green-500'}`} />
                            <span className="text-xs font-mono text-slate-300 w-12">{c.consumer_id}</span>
                            <span className="text-[10px] text-slate-500 w-12">{c.node_id}</span>
                            <div className="flex-1">
                                <div className="w-full h-1 rounded-full bg-slate-800">
                                    <div
                                        className="h-full rounded-full bg-cyan-500/60"
                                        style={{ width: `${Math.min(100, (c.load_kw / c.peak_load_kw) * 100)}%` }}
                                    />
                                </div>
                            </div>
                            <span className="text-[10px] font-mono text-cyan-400 w-16 text-right">{c.load_kw?.toFixed(1)} kW</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
