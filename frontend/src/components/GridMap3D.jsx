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

/* ─── Fault Spark Particles (electric arc effect around faulted node) ──────── */

function FaultSparks({ position }) {
    const groupRef = useRef()
    const sparkCount = 12
    const sparks = useMemo(() => {
        return Array.from({ length: sparkCount }, (_, i) => ({
            angle: (i / sparkCount) * Math.PI * 2,
            speed: 1.5 + Math.random() * 2,
            radius: 0.3 + Math.random() * 0.4,
            phase: Math.random() * Math.PI * 2,
        }))
    }, [])

    useFrame((state) => {
        if (!groupRef.current) return
        groupRef.current.children.forEach((spark, i) => {
            const s = sparks[i]
            const t = state.clock.elapsedTime * s.speed + s.phase
            const r = s.radius * (0.5 + 0.5 * Math.sin(t * 3))
            spark.position.x = Math.cos(s.angle + t) * r
            spark.position.y = Math.sin(s.angle + t * 0.7) * r
            spark.position.z = Math.sin(t * 2) * 0.15
            spark.material.opacity = 0.3 + 0.7 * Math.abs(Math.sin(t * 4))
            spark.scale.setScalar(0.5 + 0.5 * Math.sin(t * 6))
        })
    })

    return (
        <group ref={groupRef} position={position}>
            {sparks.map((_, i) => (
                <mesh key={i}>
                    <boxGeometry args={[0.04, 0.04, 0.12]} />
                    <meshBasicMaterial color="#ffaa00" transparent opacity={0.8} />
                </mesh>
            ))}
        </group>
    )
}

/* ─── Restoration Ring (pulsing amber ring around restored node) ───────────── */

function RestorationRing({ position }) {
    const ringRef = useRef()

    useFrame((state) => {
        if (ringRef.current) {
            const s = 1 + Math.sin(state.clock.elapsedTime * 3) * 0.2
            ringRef.current.scale.set(s, s, 1)
            ringRef.current.material.opacity = 0.3 + Math.sin(state.clock.elapsedTime * 4) * 0.2
            ringRef.current.rotation.z = state.clock.elapsedTime * 0.5
        }
    })

    return (
        <mesh ref={ringRef} position={position}>
            <ringGeometry args={[0.5, 0.6, 32]} />
            <meshBasicMaterial color="#f59e0b" transparent opacity={0.4} side={THREE.DoubleSide} />
        </mesh>
    )
}

/* ─── Animated Node Sphere ─────────────────────────────────────────────────── */

function GridNode({ nodeId, position, nodeData, onClick }) {
    const meshRef = useRef()
    const glowRef = useRef()
    const status = nodeData?.status || 'healthy'
    const color = STATUS_COLORS[status] || '#22c55e'
    const isFault = status === 'fault'
    const isIsolated = status === 'isolated'
    const isRestored = status === 'restored'
    const isSource = nodeId === 'bus_1'
    const size = isSource ? 0.4 : 0.28

    useFrame((state) => {
        if (meshRef.current) {
            // Gentle hover animation
            meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 1.5 + position[0]) * 0.03
            // Pulse scale on fault
            if (isFault) {
                const pulse = 1 + Math.sin(state.clock.elapsedTime * 5) * 0.2
                meshRef.current.scale.setScalar(pulse)
            } else if (isRestored) {
                const pulse = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.08
                meshRef.current.scale.setScalar(pulse)
            } else {
                meshRef.current.scale.setScalar(1)
            }
        }
        if (glowRef.current) {
            if (isFault) {
                glowRef.current.material.opacity = 0.3 + Math.sin(state.clock.elapsedTime * 6) * 0.3
                glowRef.current.scale.setScalar(1 + Math.sin(state.clock.elapsedTime * 4) * 0.15)
            } else if (isRestored) {
                glowRef.current.material.opacity = 0.2 + Math.sin(state.clock.elapsedTime * 2) * 0.1
                glowRef.current.scale.setScalar(1)
            } else {
                glowRef.current.material.opacity = 0.1
                glowRef.current.scale.setScalar(1)
            }
        }
    })

    return (
        <group position={position} onClick={(e) => { e.stopPropagation(); onClick?.(nodeId, nodeData) }}>
            {/* Outer glow sphere */}
            <mesh ref={glowRef}>
                <sphereGeometry args={[size * 2.5, 16, 16]} />
                <meshBasicMaterial color={color} transparent opacity={0.1} />
            </mesh>

            {/* Main node */}
            <mesh ref={meshRef} castShadow>
                <sphereGeometry args={[size, 32, 32]} />
                <meshStandardMaterial
                    color={color}
                    emissive={color}
                    emissiveIntensity={isFault ? 2.0 : isRestored ? 0.8 : 0.4}
                    roughness={0.3}
                    metalness={0.7}
                />
            </mesh>

            {/* Fault sparks */}
            {isFault && <FaultSparks position={[0, 0, 0]} />}

            {/* Restoration ring */}
            {isRestored && <RestorationRing position={[0, 0, 0.01]} />}

            {/* Label */}
            <Text
                position={[0, -0.55, 0]}
                fontSize={0.18}
                color="#94a3b8"
                anchorX="center"
                anchorY="top"
                font="https://fonts.gstatic.com/s/inter/v13/UcC73FwrK3iLTeHuS_fvQtMwCp50KnMa2JL7W0Q5nw.woff2"
            >
                {isSource ? '⚡ Substation' : nodeId.replace('bus_', 'B')}
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

            {/* Status label for non-healthy */}
            {(isFault || isIsolated || isRestored) && (
                <Text
                    position={[0.45, 0.3, 0]}
                    fontSize={0.1}
                    color={color}
                    anchorX="left"
                >
                    {status.toUpperCase()}
                </Text>
            )}
        </group>
    )
}

/* ─── Animated Power Flow Line ─────────────────────────────────────────────── */

function PowerLine({ from, to, isBackup, isFaulted, isActiveBackup }) {
    const lineRef = useRef()
    const lineColor = isFaulted ? '#ef4444' : isActiveBackup ? '#f59e0b' : isBackup ? '#1e293b' : '#1e3a5f'
    const width = isActiveBackup ? 2.5 : isBackup ? 1 : 2
    const points = useMemo(() => [
        new THREE.Vector3(...from),
        new THREE.Vector3(...to),
    ], [from, to])

    return (
        <>
            <Line
                ref={lineRef}
                points={points}
                color={lineColor}
                lineWidth={width}
                dashed={isBackup && !isActiveBackup}
                dashScale={5}
                opacity={isBackup && !isActiveBackup ? 0.2 : isFaulted ? 0.5 : 0.7}
                transparent
            />
            {/* Glow line for active backup feeders */}
            {isActiveBackup && (
                <Line
                    points={points}
                    color="#f59e0b"
                    lineWidth={5}
                    opacity={0.15}
                    transparent
                />
            )}
        </>
    )
}

/* ─── Flow Particles (multiple per edge for visible energy flow) ──────────── */

function FlowParticles({ from, to, count = 3, color = '#00d4ff', speed = 0.3 }) {
    const particles = useMemo(() =>
        Array.from({ length: count }, (_, i) => ({
            offset: i / count,
            speedMult: 0.8 + Math.random() * 0.4,
        })),
        [count]
    )

    return (
        <>
            {particles.map((p, i) => (
                <SingleFlowParticle
                    key={i}
                    from={from}
                    to={to}
                    offset={p.offset}
                    speed={speed * p.speedMult}
                    color={color}
                />
            ))}
        </>
    )
}

function SingleFlowParticle({ from, to, offset, speed, color }) {
    const ref = useRef()
    const startPos = useMemo(() => new THREE.Vector3(...from), [from])
    const endPos = useMemo(() => new THREE.Vector3(...to), [to])

    useFrame((state) => {
        if (ref.current) {
            const t = ((state.clock.elapsedTime * speed + offset) % 1)
            ref.current.position.lerpVectors(startPos, endPos, t)
            ref.current.material.opacity = Math.sin(t * Math.PI) * 0.9
            const s = 0.8 + Math.sin(t * Math.PI) * 0.4
            ref.current.scale.setScalar(s)
        }
    })

    return (
        <mesh ref={ref}>
            <sphereGeometry args={[0.055, 8, 8]} />
            <meshBasicMaterial color={color} transparent opacity={0.6} />
        </mesh>
    )
}

/* ─── Faulted Line Flicker ─────────────────────────────────────────────────── */

function FaultedLineFlicker({ from, to }) {
    const ref = useRef()
    const startPos = useMemo(() => new THREE.Vector3(...from), [from])
    const endPos = useMemo(() => new THREE.Vector3(...to), [to])

    useFrame((state) => {
        if (ref.current) {
            // Random flicker along the faulted line
            const t = 0.3 + Math.random() * 0.4
            ref.current.position.lerpVectors(startPos, endPos, t)
            ref.current.material.opacity = Math.random() > 0.3 ? 0.8 : 0.1
            ref.current.scale.setScalar(0.5 + Math.random() * 1.5)
        }
    })

    return (
        <mesh ref={ref}>
            <sphereGeometry args={[0.04, 6, 6]} />
            <meshBasicMaterial color="#ff6600" transparent opacity={0.5} />
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

            {/* Primary Edges */}
            {EDGES.map(([a, b]) => {
                const edgeFaulted = faultedNodes.has(a) || faultedNodes.has(b)
                return (
                    <React.Fragment key={`edge-group-${a}-${b}`}>
                        <PowerLine
                            from={NODE_POSITIONS[a]}
                            to={NODE_POSITIONS[b]}
                            isBackup={false}
                            isFaulted={edgeFaulted}
                            isActiveBackup={false}
                        />
                        {/* Flicker sparks on faulted edges */}
                        {edgeFaulted && (
                            <>
                                <FaultedLineFlicker from={NODE_POSITIONS[a]} to={NODE_POSITIONS[b]} />
                                <FaultedLineFlicker from={NODE_POSITIONS[a]} to={NODE_POSITIONS[b]} />
                            </>
                        )}
                    </React.Fragment>
                )
            })}

            {/* Backup edges */}
            {BACKUP_EDGES.map(([a, b]) => {
                const isActiveBackup = restoredNodes.has(a) || restoredNodes.has(b)
                return (
                    <React.Fragment key={`backup-group-${a}-${b}`}>
                        <PowerLine
                            from={NODE_POSITIONS[a]}
                            to={NODE_POSITIONS[b]}
                            isBackup={!isActiveBackup}
                            isFaulted={false}
                            isActiveBackup={isActiveBackup}
                        />
                        {/* Bright amber particles on active backup paths */}
                        {isActiveBackup && (
                            <FlowParticles
                                from={NODE_POSITIONS[a]}
                                to={NODE_POSITIONS[b]}
                                count={4}
                                color="#f59e0b"
                                speed={0.5}
                            />
                        )}
                    </React.Fragment>
                )
            })}

            {/* Flow particles on healthy active edges (3 per edge) */}
            {EDGES.filter(([a, b]) => !faultedNodes.has(a) && !faultedNodes.has(b)).map(([a, b]) => (
                <FlowParticles
                    key={`flow-${a}-${b}`}
                    from={NODE_POSITIONS[a]}
                    to={NODE_POSITIONS[b]}
                    count={3}
                    color="#00d4ff"
                    speed={0.3}
                />
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
        <div className="absolute bottom-4 left-4 glass-card neon-border p-4 w-72 z-10" style={{ animation: 'slideUp 0.3s ease-out' }}>
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
                <div className="flex justify-between"><span className="text-slate-500">Zone</span><span className="text-cyan-400">{nodeData.zone}</span></div>
                {nodeData.fault_type && (
                    <div className="flex justify-between text-red-400 font-semibold pt-1 border-t border-red-900/30">
                        <span>⚠ Fault</span><span>{nodeData.fault_type} ({nodeData.fault_severity})</span>
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

    // Count statuses for the header
    const statusCounts = useMemo(() => {
        const counts = { healthy: 0, fault: 0, isolated: 0, restored: 0 }
        nodes.forEach(n => { if (counts[n.status] !== undefined) counts[n.status]++ })
        return counts
    }, [nodes])

    return (
        <div className="glass-card relative flex-1 overflow-hidden" style={{ minHeight: '400px' }}>
            {/* Header */}
            <div className="absolute top-3 left-4 z-10 flex items-center gap-2">
                <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">3D Grid Topology</h2>
                <div className="flex gap-2 ml-3">
                    <span className="flex items-center gap-1 text-[10px]"><span className="w-2 h-2 rounded-full bg-green-500 inline-block" /> {statusCounts.healthy}</span>
                    <span className="flex items-center gap-1 text-[10px]"><span className="w-2 h-2 rounded-full bg-red-500 inline-block" /> {statusCounts.fault}</span>
                    <span className="flex items-center gap-1 text-[10px]"><span className="w-2 h-2 rounded-full bg-slate-500 inline-block" /> {statusCounts.isolated}</span>
                    <span className="flex items-center gap-1 text-[10px]"><span className="w-2 h-2 rounded-full bg-amber-500 inline-block" /> {statusCounts.restored}</span>
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
