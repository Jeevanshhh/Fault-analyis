import React, { useContext } from 'react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts'
import { GridContext } from '../App'

const RISK_COLORS = { high: '#ef4444', medium: '#f59e0b', low: '#22c55e' }
const WEATHER_ICONS = {
    lightning: '\u26A1',  // lightning bolt
    rain: '\uD83C\uDF27',  // cloud with rain (might not render, fallback handled below)
    wind: '\uD83D\uDCA8',  // wind
    hot: '\uD83C\uDF21',   // thermometer
}

function CustomTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null
    return (
        <div className="custom-tooltip">
            <p className="text-slate-400 text-[10px]">{label}</p>
            <p className="text-cyan-400 font-mono font-bold text-xs">{payload[0].value?.toFixed(1)} kW</p>
        </div>
    )
}

export default function AIPredictionPanel() {
    const { forecast, riskData, gridState } = useContext(GridContext)
    const weather = gridState?.weather || riskData?.weather || {}

    // Format forecast for chart
    const chartData = (forecast?.forecast || []).map((f, i) => ({
        time: `${Math.floor(i / 2)}:${i % 2 === 0 ? '00' : '30'}`,
        load: f.load_kw,
    }))

    // Slice to show first 24 points (12 hours) for readability
    const displayData = chartData.slice(0, 24)

    // Zone risks
    const zoneRisks = riskData?.zone_risks || []

    return (
        <div className="glass-card p-4">
            {/* Header */}
            <div className="flex items-center gap-2 mb-3">
                <span style={{ color: '#a855f7' }} className="text-sm">&#9670;</span>
                <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">AI Predictions</h2>
            </div>

            {/* Load Forecast Chart */}
            <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider">24h Load Forecast</p>
                    {forecast && (
                        <div className="flex gap-3">
                            <span className="text-[10px] font-mono text-cyan-400">Peak: {forecast.peak_kw} kW</span>
                            <span className="text-[10px] font-mono text-slate-500">Avg: {forecast.avg_kw} kW</span>
                        </div>
                    )}
                </div>
                <div style={{ height: 120 }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={displayData} margin={{ top: 5, right: 5, bottom: 0, left: -20 }}>
                            <defs>
                                <linearGradient id="loadGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#00d4ff" stopOpacity={0.3} />
                                    <stop offset="100%" stopColor="#00d4ff" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <XAxis
                                dataKey="time"
                                tick={{ fontSize: 9, fill: '#64748b' }}
                                axisLine={{ stroke: '#1e293b' }}
                                tickLine={false}
                                interval={5}
                            />
                            <YAxis
                                tick={{ fontSize: 9, fill: '#64748b' }}
                                axisLine={false}
                                tickLine={false}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Area
                                type="monotone"
                                dataKey="load"
                                stroke="#00d4ff"
                                strokeWidth={2}
                                fill="url(#loadGradient)"
                                dot={false}
                                animationDuration={1000}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Zone Risk Matrix */}
            <div className="mb-4">
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Fault Risk by Zone</p>
                <div className="grid grid-cols-4 gap-2">
                    {zoneRisks.map((zone) => (
                        <div
                            key={zone.zone}
                            className="p-2 rounded-lg text-center"
                            style={{
                                background: `${RISK_COLORS[zone.risk_level]}10`,
                                border: `1px solid ${RISK_COLORS[zone.risk_level]}30`,
                            }}
                        >
                            <p className="text-[10px] text-slate-500 font-mono">{zone.zone.replace('zone_', 'Z-').toUpperCase()}</p>
                            <p className="text-sm font-bold font-mono" style={{ color: RISK_COLORS[zone.risk_level] }}>
                                {(zone.risk_score * 100).toFixed(0)}%
                            </p>
                            <span className={`badge badge-${zone.risk_level} text-[8px]`}>{zone.risk_level}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Weather Strip */}
            <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Weather Conditions</p>
                <div className="flex gap-3">
                    <div className="flex items-center gap-1.5 text-xs">
                        <span>T</span>
                        <span className="font-mono text-amber-400">{weather.temp_c?.toFixed(1) || '--'}C</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-xs">
                        <span>W</span>
                        <span className="font-mono text-sky-400">{weather.wind_kmh?.toFixed(0) || '--'} km/h</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-xs">
                        <span>R</span>
                        <span className="font-mono text-blue-400">{weather.rain_mm?.toFixed(1) || '0'} mm</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-xs">
                        <span>L</span>
                        <span className="font-mono" style={{ color: weather.lightning_risk > 0.5 ? '#ef4444' : '#22c55e' }}>
                            {((weather.lightning_risk || 0) * 100).toFixed(0)}%
                        </span>
                    </div>
                </div>
            </div>
        </div>
    )
}
