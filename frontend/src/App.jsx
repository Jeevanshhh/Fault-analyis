import React, { useState, useEffect, useRef, createContext, useContext } from 'react'
import StatsBar from './components/StatsBar'
import GridMap3D from './components/GridMap3D'
import FaultPanel from './components/FaultPanel'
import AIPredictionPanel from './components/AIPredictionPanel'
import ConsumerPanel from './components/ConsumerPanel'
import SystemLogPanel from './components/SystemLogPanel'

// ─── Grid Context ────────────────────────────────────────────────────────────

export const GridContext = createContext(null)

const API = 'http://localhost:8000'
const WS_URL = 'ws://localhost:8000/ws/grid'

export default function App() {
    const [gridState, setGridState] = useState({
        tick: 0,
        weather: { temp_c: 28.5, wind_kmh: 15.2, rain_mm: 0, lightning_risk: 0.12 },
        nodes: Array(12).fill(0).map((_, i) => ({
            node_id: `bus_${i+1}`,
            status: 'healthy',
            voltage_v: 230.1,
            current_a: 12.4,
            load_kw: 25.0
        })),
        active_faults: [],
        system_logs: [{ timestamp: new Date().toLocaleTimeString('en-US',{hour12:false}), message: "System initialized. Monitoring grid..." }],
        stats: {
            healthy_nodes: 12,
            fault_nodes: 0,
            total_load_kw: 300.5,
            avg_voltage_v: 230.1,
            avg_current_a: 12.4,
            avg_frequency_hz: 50.01,
            active_faults: 0
        }
    })
    const [connected, setConnected] = useState(false)
    const [forecast, setForecast] = useState(null)
    const [riskData, setRiskData] = useState(null)
    const [consumers, setConsumers] = useState([])
    const wsRef = useRef(null)
    const reconnectTimer = useRef(null)

    // ── WebSocket ──────────────────────────────────────────────────────────────

    useEffect(() => {
        function connect() {
            const ws = new WebSocket(WS_URL)
            wsRef.current = ws

            ws.onopen = () => {
                setConnected(true)
                console.log('WebSocket connected')
            }

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data)
                    setGridState(data)
                } catch (e) {
                    console.error('WS parse error:', e)
                }
            }

            ws.onclose = () => {
                setConnected(false)
                console.log('WebSocket disconnected, reconnecting in 3s...')
                reconnectTimer.current = setTimeout(connect, 3000)
            }

            ws.onerror = (err) => {
                console.error('WS error:', err)
                ws.close()
            }
        }

        connect()
        return () => {
            wsRef.current?.close()
            clearTimeout(reconnectTimer.current)
        }
    }, [])

    // ── Fetch forecast & risk periodically ─────────────────────────────────────

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [fRes, rRes, cRes] = await Promise.all([
                    fetch(`${API}/forecast/load`),
                    fetch(`${API}/forecast/risk`),
                    fetch(`${API}/consumers`),
                ])
                if (fRes.ok) setForecast(await fRes.json())
                if (rRes.ok) setRiskData(await rRes.json())
                if (cRes.ok) {
                    const cData = await cRes.json()
                    setConsumers(cData.consumers || [])
                }
            } catch (e) { console.error('Fetch error:', e) }
        }

        fetchData()
        const interval = setInterval(fetchData, 10000)
        return () => clearInterval(interval)
    }, [])

    // ── Inject Fault ───────────────────────────────────────────────────────────

    const injectFault = async (nodeId, faultType = 'line_fault') => {
        try {
            await fetch(`${API}/faults/inject`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ node_id: nodeId, fault_type: faultType }),
            })
        } catch (e) { console.error('Inject error:', e) }
    }

    // ── Render ─────────────────────────────────────────────────────────────────

    const contextValue = {
        gridState,
        connected,
        forecast,
        riskData,
        consumers,
        injectFault,
    }

    return (
        <GridContext.Provider value={contextValue}>
            <div className="dashboard-grid">
                {/* Header Stats Bar */}
                <div className="stats-bar">
                    <StatsBar />
                </div>

                {/* Left: 3D Grid Visualization */}
                <div className="main-panel">
                    <GridMap3D />
                </div>

                {/* Right: Side Panels */}
                <div className="side-panels">
                    <SystemLogPanel />
                    <FaultPanel />
                    <AIPredictionPanel />
                    <ConsumerPanel />
                </div>
            </div>
        </GridContext.Provider>
    )
}
