import React, { useContext, useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceArea, Legend } from 'recharts'
import { GridContext } from '../App'

const STATE_COLORS = {
    healthy: '#00000000', 
    fault: '#ef444420',   // red
    isolation: '#64748b20',// outline 
    recovery: '#f59e0b20'  // amber
}

export default function SystemBehaviorGraph() {
    const { gridState } = useContext(GridContext)
    const data = gridState?.graph_data || []
    
    // Build contiguous segments to shade background by State.
    const refAreas = useMemo(() => {
        let areas = []
        if (data.length === 0) return areas
        
        let currentState = data[0].state
        let startX = data[0].time_str
        
        for (let i = 1; i < data.length; i++) {
            if (data[i].state !== currentState) {
                areas.push({ start: startX, end: data[i].time_str, state: currentState })
                currentState = data[i].state
                startX = data[i].time_str
            }
        }
        areas.push({ start: startX, end: data[data.length - 1].time_str, state: currentState })
        return areas
    }, [data])

    return (
        <div className="glass-card p-4 flex flex-col h-full w-full">
            <div className="flex items-center mb-3">
                <span style={{ color: '#00d4ff' }} className="text-sm mr-2">&#9670;</span>
                <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">System Behavior Graph</h2>
            </div>
            
            <div className="flex-grow h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: -25 }}>
                        <XAxis dataKey="time_str" tick={{ fontSize: 9, fill: '#64748b' }} interval="preserveStartEnd" minTickGap={30} />
                        <YAxis yAxisId="left" domain={[0, 250]} tick={{ fontSize: 9, fill: '#00d4ff' }} axisLine={false} tickLine={false} />
                        <YAxis yAxisId="right" orientation="right" domain={[0, 40]} tick={{ fontSize: 9, fill: '#a855f7' }} axisLine={false} tickLine={false} />
                        <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }} itemStyle={{ fontSize: 11 }} labelStyle={{ color: '#94a3b8', fontSize: 10 }} />
                        <Legend wrapperStyle={{ fontSize: '10px' }} />
                        
                        {refAreas.map((area, idx) => (
                            <ReferenceArea key={idx} yAxisId="left" x1={area.start} x2={area.end} fill={STATE_COLORS[area.state]} strokeOpacity={0} />
                        ))}

                        <Line yAxisId="left" type="stepAfter" dataKey="voltage" stroke="#00d4ff" strokeWidth={2} dot={false} isAnimationActive={false} name="Min Voltage (V)" />
                        <Line yAxisId="right" type="stepAfter" dataKey="current" stroke="#a855f7" strokeWidth={2} dot={false} isAnimationActive={false} name="Max Current (A)" />
                    </LineChart>
                </ResponsiveContainer>
            </div>
            
            <div className="flex justify-between items-center mt-2 px-2 text-[9px] uppercase tracking-wider font-mono text-slate-400">
                <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-green-500/50"></div> Healthy</div>
                <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-red-500/50"></div> Fault</div>
                <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-slate-500/50"></div> Isolation</div>
                <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-amber-500/50"></div> Restoration</div>
            </div>
        </div>
    )
}
