import React, { useContext } from 'react'
import { GridContext } from '../App'

const STAT_ITEMS = [
    { key: 'avg_voltage_v', label: 'Voltage', unit: 'V', icon: '⚡', color: '#00d4ff' },
    { key: 'avg_current_a', label: 'Current', unit: 'A', icon: '〰', color: '#a855f7' },
    { key: 'avg_frequency_hz', label: 'Frequency', unit: 'Hz', icon: '~', color: '#22c55e' },
    { key: 'total_load_kw', label: 'Total Load', unit: 'kW', icon: '⏻', color: '#f59e0b' },
    { key: 'healthy_nodes', label: 'Healthy', unit: '', icon: '●', color: '#22c55e' },
    { key: 'active_faults', label: 'Active Faults', unit: '', icon: '▲', color: '#ef4444' },
]

export default function StatsBar() {
    const { gridState, connected } = useContext(GridContext)
    const stats = gridState?.stats || {}

    return (
        <div className="glass-card px-4 py-3">
            <div className="flex items-center justify-between">
                {/* Left: Title + connection */}
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white font-bold text-sm">
                            SH
                        </div>
                        <div>
                            <h1 className="text-sm font-bold tracking-wide neon-text">SHDN</h1>
                            <p className="text-[10px] text-slate-500 -mt-0.5">Self-Healing Distribution Network</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-1.5 ml-4">
                        <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 connection-dot' : 'bg-red-500'}`} />
                        <span className="text-[10px] text-slate-500 font-mono">
                            {connected ? 'LIVE' : 'DISCONNECTED'}
                        </span>
                    </div>
                </div>

                {/* Right: Stats */}
                <div className="flex items-center gap-1">
                    {STAT_ITEMS.map((item) => {
                        const val = stats[item.key]
                        const display = val !== undefined
                            ? (typeof val === 'number' && item.unit ? val.toFixed(item.key.includes('frequency') ? 2 : 1) : val)
                            : '--'
                        return (
                            <div
                                key={item.key}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
                                style={{ background: `${item.color}10` }}
                            >
                                <span className="text-xs" style={{ color: item.color }}>{item.icon}</span>
                                <div className="flex flex-col">
                                    <span className="text-[9px] text-slate-500 font-medium uppercase tracking-wider">{item.label}</span>
                                    <span className="text-sm font-bold font-mono" style={{ color: item.color }}>
                                        {display}
                                        {item.unit && <span className="text-[9px] text-slate-500 ml-0.5">{item.unit}</span>}
                                    </span>
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>
        </div>
    )
}
