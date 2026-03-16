import React, { useContext, useRef, useState, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Text, Line } from '@react-three/drei'
import * as THREE from 'three'
import { GridContext } from '../App'

/* ─── Node Positions (2D grid layout for 12 buses) ─────────────────────────── */
const NODE_POSITIONS = {
    bus_1: [0, 0, 0],
    bus_2: [-2.5, -1.5, 0],
    bus_3: [2.5, -1.5, 0],
    bus_4: [-4, -3, 0],
    bus_5: [-1, -3, 0],
    bus_6: [1, -3, 0],
    bus_7: [4, -3, 0],
    bus_8: [-5, -4.5, 0],
    bus_9: [-1.5, -4.5, 0],
    bus_10: [1.5, -4.5, 0],
    bus_11: [3.5, -4.5, 0],
    bus_12: [-5.5, -6, 0],
}

const EDGES = [
    ['bus_1', 'bus_2'], ['bus_1', 'bus_3'],
    ['bus_2', 'bus_4'], ['bus_2', 'bus_5'],
    ['bus_3', 'bus_6'], ['bus_3', 'bus_7'],
    ['bus_4', 'bus_8'], ['bus_5', 'bus_9'],
    ['bus_6', 'bus_10'], ['bus_7', 'bus_11'],
    ['bus_8', 'bus_12'],
]

const BACKUP_EDGES = [
    ['bus_4', 'bus_6'], ['bus_5', 'bus_7'],
    ['bus_9', 'bus_10'], ['bus_10', 'bus_11'],
    ['bus_11', 'bus_12'],
]

const STATUS_COLORS = {
    healthy: '#22c55e',
    fault: '#ef4444',
    restored: '#f59e0b',
    isolated: '#64748b',
    warning: '#f59e0b',
}

/* ─── Animated Node Sphere ─────────────────────────────────────────────────── */

function GridNode({ nodeId, position, nodeData, onClick }) {
    const meshRef = useRef()
    const glowRef = useRef()
    const status = nodeData?.status || 'healthy'
    const color = STATUS_COLORS[status] || '#22c55e'
    const isFault = status === 'fault'
    const isSource = nodeId === 'bus_1'
    const size = isSource ? 0.4 : 0.28

    useFrame((state) => {
        if (meshRef.current) {
            // Gentle hover animation
            meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 1.5 + position[0]) * 0.03
            // Pulse scale on fault
            if (isFault) {
                const pulse = 1 + Math.sin(state.clock.elapsedTime * 5) * 0.15
                meshRef.current.scale.setScalar(pulse)
            } else {
                meshRef.current.scale.setScalar(1)
            }
        }
        if (glowRef.current) {
            const glowPulse = 0.5 + Math.sin(state.clock.elapsedTime * 3) * 0.3
            glowRef.current.material.opacity = isFault ? glowPulse : 0.15
        }
    })

    return (
        <group position={position} onClick={(e) => { e.stopPropagation(); onClick?.(nodeId, nodeData) }}>
            {/* Glow sphere */}
            <mesh ref={glowRef}>
                <sphereGeometry args={[size * 2, 16, 16]} />
                <meshBasicMaterial color={color} transparent opacity={0.15} />
            </mesh>

            {/* Main node */}
            <mesh ref={meshRef} castShadow>
                <sphereGeometry args={[size, 32, 32]} />
                <meshStandardMaterial
                    color={color}
                    emissive={color}
                    emissiveIntensity={isFault ? 1.5 : 0.4}
                    roughness={0.3}
                    metalness={0.7}
                />
            </mesh>

            {/* Label */}
            <Text
                position={[0, -0.55, 0]}
                fontSize={0.18}
                color="#94a3b8"
                anchorX="center"
                anchorY="top"
                font="https://fonts.gstatic.com/s/inter/v13/UcC73FwrK3iLTeHuS_fvQtMwCp50KnMa2JL7W0Q5nw.woff2"
            >
                {nodeId.replace('bus_', 'B')}
            </Text>

            {/* Voltage label */}
            {nodeData && (
                <Text
                    position={[0, 0.5, 0]}
                    fontSize={0.13}
                    color={color}
                    anchorX="center"
                    anchorY="bottom"
                >
                    {nodeData.voltage_v?.toFixed(0)}V
                </Text>
            )}
        </group>
    )
}

/* ─── Animated Power Flow Line ─────────────────────────────────────────────── */

function PowerLine({ from, to, isBackup, isFaulted }) {
    const lineColor = isFaulted ? '#ef4444' : isBackup ? '#334155' : '#1e3a5f'
    const points = useMemo(() => [
        new THREE.Vector3(...from),
        new THREE.Vector3(...to),
    ], [from, to])

    return (
        <Line
            points={points}
            color={lineColor}
            lineWidth={isBackup ? 1 : 2}
            dashed={isBackup}
            dashScale={5}
            opacity={isBackup ? 0.3 : 0.7}
            transparent
        />
    )
}

/* ─── Flow Particles ───────────────────────────────────────────────────────── */

function FlowParticle({ from, to }) {
    const ref = useRef()
    const startPos = useMemo(() => new THREE.Vector3(...from), [from])
    const endPos = useMemo(() => new THREE.Vector3(...to), [to])
    const offset = useMemo(() => Math.random(), [])

    useFrame((state) => {
        if (ref.current) {
            const t = ((state.clock.elapsedTime * 0.3 + offset) % 1)
            ref.current.position.lerpVectors(startPos, endPos, t)
            ref.current.material.opacity = Math.sin(t * Math.PI) * 0.8
        }
    })

    return (
        <mesh ref={ref}>
            <sphereGeometry args={[0.05, 8, 8]} />
            <meshBasicMaterial color="#00d4ff" transparent opacity={0.5} />
        </mesh>
    )
}

/* ─── Scene ────────────────────────────────────────────────────────────────── */

function GridScene({ nodes, selectedNode, onNodeClick }) {
    const nodeMap = useMemo(() => {
        const m = {}
        if (nodes) nodes.forEach(n => { m[n.node_id] = n })
        return m
    }, [nodes])

    const faultedNodes = useMemo(() => {
        return new Set(nodes?.filter(n => n.status === 'fault' || n.status === 'isolated').map(n => n.node_id) || [])
    }, [nodes])

    const restoredNodes = useMemo(() => {
        return new Set(nodes?.filter(n => n.status === 'restored').map(n => n.node_id) || [])
    }, [nodes])

    return (
        <>
            {/* Lighting */}
            <ambientLight intensity={0.3} />
            <pointLight position={[0, 5, 5]} intensity={0.8} color="#ffffff" />
            <pointLight position={[-5, 3, -3]} intensity={0.4} color="#00d4ff" />
            <pointLight position={[5, 3, -3]} intensity={0.4} color="#a855f7" />

            {/* Grid plane */}
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -7, 0]} receiveShadow>
                <planeGeometry args={[20, 20]} />
                <meshStandardMaterial color="#0a0e1a" transparent opacity={0.5} />
            </mesh>

            {/* Edges */}
            {EDGES.map(([a, b]) => (
                <PowerLine
                    key={`${a}-${b}`}
                    from={NODE_POSITIONS[a]}
                    to={NODE_POSITIONS[b]}
                    isBackup={false}
                    isFaulted={faultedNodes.has(a) || faultedNodes.has(b)}
                />
            ))}

            {/* Backup edges */}
            {BACKUP_EDGES.map(([a, b]) => {
                const isActiveBackup = restoredNodes.has(a) || restoredNodes.has(b);
                return (
                    <React.Fragment key={`backup-group-${a}-${b}`}>
                        <PowerLine
                            key={`backup-${a}-${b}`}
                            from={NODE_POSITIONS[a]}
                            to={NODE_POSITIONS[b]}
                            isBackup={!isActiveBackup}
                            isFaulted={false}
                        />
                        {isActiveBackup && (
                            <FlowParticle key={`flow-backup-${a}-${b}`} from={NODE_POSITIONS[a]} to={NODE_POSITIONS[b]} />
                        )}
                    </React.Fragment>
                )
            })}

            {/* Flow particles on healthy active edges */}
            {EDGES.filter(([a, b]) => !faultedNodes.has(a) && !faultedNodes.has(b)).map(([a, b]) => (
                <FlowParticle key={`flow-${a}-${b}`} from={NODE_POSITIONS[a]} to={NODE_POSITIONS[b]} />
            ))}

            {/* Nodes */}
            {Object.entries(NODE_POSITIONS).map(([id, pos]) => (
                <GridNode
                    key={id}
                    nodeId={id}
                    position={pos}
                    nodeData={nodeMap[id]}
                    onClick={onNodeClick}
                />
            ))}

            <OrbitControls
                enablePan={true}
                enableZoom={true}
                enableRotate={true}
                maxPolarAngle={Math.PI / 1.8}
                minDistance={3}
                maxDistance={15}
                target={[0, -2.5, 0]}
            />
        </>
    )
}

/* ─── Node Detail Popup ────────────────────────────────────────────────────── */

function NodeDetail({ nodeId, nodeData, onClose }) {
    if (!nodeData) return null
    const status = nodeData.status || 'healthy'
    return (
        <div className="absolute bottom-4 left-4 glass-card neon-border p-4 w-64 animate-slide-up z-10">
            <div className="flex justify-between items-start mb-3">
                <div>
                    <h3 className="font-bold text-sm neon-text">{nodeId}</h3>
                    <span className={`badge badge-${status} mt-1`}>{status}</span>
                </div>
                <button onClick={onClose} className="text-slate-500 hover:text-white text-sm">✕</button>
            </div>
            <div className="space-y-1.5 text-xs font-mono">
                <div className="flex justify-between"><span className="text-slate-500">Voltage</span><span>{nodeData.voltage_v?.toFixed(2)} V</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Current</span><span>{nodeData.current_a?.toFixed(2)} A</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Frequency</span><span>{nodeData.frequency_hz?.toFixed(3)} Hz</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Power</span><span>{nodeData.power_kw?.toFixed(2)} kW</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Load</span><span>{nodeData.load_kw?.toFixed(2)} kW</span></div>
                {nodeData.fault_type && (
                    <div className="flex justify-between text-red-400">
                        <span>Fault</span><span>{nodeData.fault_type}</span>
                    </div>
                )}
            </div>
        </div>
    )
}

/* ─── Main GridMap3D Component ─────────────────────────────────────────────── */

export default function GridMap3D() {
    const { gridState } = useContext(GridContext)
    const [selectedNode, setSelectedNode] = useState(null)
    const nodes = gridState?.nodes || []

    const selectedData = useMemo(() => {
        if (!selectedNode) return null
        return nodes.find(n => n.node_id === selectedNode)
    }, [selectedNode, nodes])

    return (
        <div className="glass-card relative flex-1 overflow-hidden" style={{ minHeight: '400px' }}>
            {/* Header */}
            <div className="absolute top-3 left-4 z-10 flex items-center gap-2">
                <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">3D Grid Topology</h2>
                <div className="flex gap-2 ml-3">
                    <span className="flex items-center gap-1 text-[10px]"><span className="w-2 h-2 rounded-full bg-green-500 inline-block" /> Healthy</span>
                    <span className="flex items-center gap-1 text-[10px]"><span className="w-2 h-2 rounded-full bg-red-500 inline-block" /> Fault</span>
                    <span className="flex items-center gap-1 text-[10px]"><span className="w-2 h-2 rounded-full bg-slate-500 inline-block" /> Isolated</span>
                    <span className="flex items-center gap-1 text-[10px]"><span className="w-2 h-2 rounded-full bg-amber-500 inline-block" /> Restored</span>
                </div>
            </div>

            {/* 3D Canvas */}
            <Canvas
                camera={{ position: [0, 2, 8], fov: 50 }}
                style={{ background: 'transparent' }}
                shadows
            >
                <GridScene
                    nodes={nodes}
                    selectedNode={selectedNode}
                    onNodeClick={(id) => setSelectedNode(prev => prev === id ? null : id)}
                />
            </Canvas>

            {/* Node Detail Popup */}
            {selectedNode && (
                <NodeDetail
                    nodeId={selectedNode}
                    nodeData={selectedData}
                    onClose={() => setSelectedNode(null)}
                />
            )}
        </div>
    )
}
