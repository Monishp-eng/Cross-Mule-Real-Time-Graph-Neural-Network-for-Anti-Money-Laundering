import { useEffect, useRef, useState } from 'react';
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import { mockAccounts, mockTransactions } from '../../mockData';
import { Account } from '../../types';
import { motion } from 'motion/react';
import { useTheme } from '../../contexts/ThemeContext';

interface GraphPanelProps {
  onNodeClick: (account: Account) => void;
}

interface Node {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  account: Account;
}

export function GraphPanel({ onNodeClick }: GraphPanelProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const nodesRef = useRef<Node[]>([]);
  const [zoom, setZoom] = useState(1);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const animationFrameRef = useRef<number>();
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  useEffect(() => {
    // Initialize nodes with random positions
    const initialNodes: Node[] = mockAccounts.map((account, i) => ({
      id: account.id,
      x: 400 + Math.cos((i * Math.PI * 2) / mockAccounts.length) * 200,
      y: 300 + Math.sin((i * Math.PI * 2) / mockAccounts.length) * 200,
      vx: 0,
      vy: 0,
      account,
    }));
    setNodes(initialNodes);
    nodesRef.current = initialNodes;
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const animate = () => {
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Apply forces for layout
      const updatedNodes = nodesRef.current.map(node => {
        let fx = 0, fy = 0;

        // Repulsion between nodes
        nodesRef.current.forEach(other => {
          if (node.id === other.id) return;
          const dx = node.x - other.x;
          const dy = node.y - other.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = 1000 / (dist * dist);
          fx += (dx / dist) * force;
          fy += (dy / dist) * force;
        });

        // Attraction for connected nodes
        mockTransactions.forEach(txn => {
          if (txn.fromAccount === node.id) {
            const target = nodesRef.current.find(n => n.id === txn.toAccount);
            if (target) {
              const dx = target.x - node.x;
              const dy = target.y - node.y;
              const dist = Math.sqrt(dx * dx + dy * dy) || 1;
              const force = dist * 0.01;
              fx += (dx / dist) * force;
              fy += (dy / dist) * force;
            }
          }
        });

        // Center gravity
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const dx = centerX - node.x;
        const dy = centerY - node.y;
        fx += dx * 0.001;
        fy += dy * 0.001;

        // Update velocity and position
        const vx = (node.vx + fx) * 0.85;
        const vy = (node.vy + fy) * 0.85;
        const x = node.x + vx;
        const y = node.y + vy;

        return { ...node, x, y, vx, vy };
      });

      nodesRef.current = updatedNodes;
      setNodes(updatedNodes);

      // Draw edges
      mockTransactions.forEach(txn => {
        const source = updatedNodes.find(n => n.id === txn.fromAccount);
        const target = updatedNodes.find(n => n.id === txn.toAccount);
        
        if (source && target) {
          ctx.beginPath();
          ctx.moveTo(source.x * zoom, source.y * zoom);
          ctx.lineTo(target.x * zoom, target.y * zoom);
          
          if (txn.riskScore > 70) {
            ctx.strokeStyle = txn.riskScore > 85 ? '#ef4444' : '#a855f7';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
          } else {
            ctx.strokeStyle = '#334155';
            ctx.lineWidth = 1;
            ctx.setLineDash([]);
          }
          
          ctx.stroke();
          ctx.setLineDash([]);
        }
      });

      // Draw nodes
      updatedNodes.forEach(node => {
        const size = node.account.riskScore > 80 ? 12 : node.account.riskScore > 60 ? 10 : 8;
        const isHovered = hoveredNode === node.id;
        
        // Glow effect for high-risk nodes
        if (node.account.riskScore > 70) {
          ctx.beginPath();
          ctx.arc(node.x * zoom, node.y * zoom, size + 8, 0, Math.PI * 2);
          const gradient = ctx.createRadialGradient(
            node.x * zoom, node.y * zoom, 0,
            node.x * zoom, node.y * zoom, size + 8
          );
          const color = node.account.riskScore > 80 ? '#ef4444' : '#a855f7';
          gradient.addColorStop(0, color + '40');
          gradient.addColorStop(1, color + '00');
          ctx.fillStyle = gradient;
          ctx.fill();
        }

        // Node circle
        ctx.beginPath();
        ctx.arc(node.x * zoom, node.y * zoom, size * (isHovered ? 1.3 : 1), 0, Math.PI * 2);
        ctx.fillStyle = 
          node.account.riskScore > 80 ? '#ef4444' :
          node.account.riskScore > 60 ? '#a855f7' :
          '#06b6d4';
        ctx.fill();
        
        // Border
        ctx.strokeStyle = isHovered ? '#ffffff' : '#1e293b';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Cluster indicator
        if (node.account.clusterId) {
          ctx.beginPath();
          ctx.arc(node.x * zoom, node.y * zoom, size + 4, 0, Math.PI * 2);
          ctx.strokeStyle = '#ef4444';
          ctx.lineWidth = 1.5;
          ctx.setLineDash([2, 2]);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      });

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [zoom, hoveredNode]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / zoom;
    const y = (e.clientY - rect.top) / zoom;

    const clickedNode = nodes.find(node => {
      const dx = node.x - x;
      const dy = node.y - y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const size = node.account.riskScore > 80 ? 12 : node.account.riskScore > 60 ? 10 : 8;
      return dist < size;
    });

    if (clickedNode) {
      onNodeClick(clickedNode.account);
    }
  };

  const handleCanvasMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / zoom;
    const y = (e.clientY - rect.top) / zoom;

    const hovered = nodes.find(node => {
      const dx = node.x - x;
      const dy = node.y - y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const size = node.account.riskScore > 80 ? 12 : node.account.riskScore > 60 ? 10 : 8;
      return dist < size;
    });

    setHoveredNode(hovered ? hovered.id : null);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative bg-slate-900/50 backdrop-blur-xl rounded-xl border-2 border-slate-700/50 overflow-hidden shadow-xl h-full"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
        <div>
          <h3 className="text-lg font-semibold text-white">Entity Relationship Graph</h3>
          <p className="text-sm text-slate-400">Interactive network visualization powered by GNN</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setZoom(Math.max(0.5, zoom - 0.1))}
            className="p-2 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 text-slate-400 hover:text-cyan-400 transition-all"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoom(Math.min(2, zoom + 0.1))}
            className="p-2 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 text-slate-400 hover:text-cyan-400 transition-all"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button className="p-2 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 text-slate-400 hover:text-cyan-400 transition-all">
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div className="relative h-[500px] bg-gradient-to-br from-slate-950/50 to-slate-900/50">
        <canvas
          ref={canvasRef}
          width={800}
          height={500}
          onClick={handleCanvasClick}
          onMouseMove={handleCanvasMove}
          className="w-full h-full cursor-pointer"
        />

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-slate-900/80 backdrop-blur-xl rounded-lg p-3 border border-slate-700/50">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <span className="text-xs text-slate-300">High Risk (&gt;80)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-purple-500" />
              <span className="text-xs text-slate-300">Suspicious (60-80)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-cyan-500" />
              <span className="text-xs text-slate-300">Normal (&lt;60)</span>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="absolute top-4 right-4 bg-slate-900/80 backdrop-blur-xl rounded-lg p-3 border border-slate-700/50">
          <div className="text-xs text-slate-400">
            <div>Nodes: <span className="text-cyan-400 font-semibold">{nodes.length}</span></div>
            <div>Edges: <span className="text-cyan-400 font-semibold">{mockTransactions.length}</span></div>
            <div>Zoom: <span className="text-cyan-400 font-semibold">{(zoom * 100).toFixed(0)}%</span></div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}