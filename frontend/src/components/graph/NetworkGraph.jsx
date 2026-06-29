import ForceGraph2D from "react-force-graph-2d";
import { useMemo, useRef, useEffect } from "react";

export default function NetworkGraph({ graphData }) {
  const fgRef = useRef(null);

  const normalized = useMemo(() => {
    const nodes = Array.isArray(graphData?.nodes) ? graphData.nodes : [];
    const links = Array.isArray(graphData?.links)
      ? graphData.links
      : Array.isArray(graphData?.edges)
        ? graphData.edges.map((edge) => ({ source: edge.from, target: edge.to, ...edge }))
        : [];

    return { nodes, links };
  }, [graphData]);

  // Make the graph "comfortable" by tuning the physics engine
  useEffect(() => {
    if (fgRef.current) {
      fgRef.current.d3Force("charge").strength(-400); // Push nodes further apart
      fgRef.current.d3Force("link").distance(70);     // Make connections longer
    }
  }, [normalized]);

  return (
    <div className="card relative h-[75vh] w-full overflow-hidden p-2 bg-slate-950/80 cursor-move">
      <div className="pointer-events-none absolute left-3 top-3 z-10 rounded-2xl border border-slate-700/50 bg-slate-950/55 px-3 py-2 text-xs text-slate-300 backdrop-blur">
        Drag canvas to pan. Scroll to zoom. High-risk links pulse in red.
      </div>
      {normalized.nodes.length === 0 ? (
        <div className="flex h-full w-full items-center justify-center">
          <p className="text-slate-400 font-medium">No network graph data available for this entity.</p>
        </div>
      ) : (
        <ForceGraph2D
          ref={fgRef}
          graphData={normalized}
          nodeAutoColorBy="cluster_id"
          enableZoomInteraction={true}
          enablePanInteraction={true}
          enableNodeDrag={true}
          cooldownTicks={150} // Let it settle nicely
          linkDirectionalParticles={(link) => (link.suspicious ? 4 : 0)}
          linkDirectionalParticleWidth={(link) => (link.suspicious ? 2.5 : 1.2)}
          linkWidth={(link) => {
            if (link.suspicious) return 2.2;
            if (Number(link.velocity_score || 0) >= 0.45) return 1.8;
            return 1;
          }}
          linkColor={(link) => {
            if (link.suspicious) return "#ef4444";
            if (Number(link.velocity_score || 0) >= 0.45) return "#f59e0b";
            return "#64748b";
          }}
          nodeCanvasObject={(node, ctx, scale) => {
            if (node.x === undefined || node.y === undefined) return;
            
            const label = node.label || node.id;
            const riskScore = Number(node.risk_score || 0);
            const riskLevel = node.risk_level || (riskScore >= 0.75 ? "high" : riskScore >= 0.45 ? "medium" : "low");
            const radius = riskLevel === "high" ? 7 : riskLevel === "medium" ? 5.5 : 4;

            let fill = "#22d3ee";
            if (riskLevel === "high") fill = "#ef4444";
            else if (riskLevel === "medium") fill = "#f59e0b";

            ctx.beginPath();
            ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
            ctx.fillStyle = fill;
            ctx.fill();

            const fontSize = 11 / scale;
            ctx.font = `${fontSize}px Sans-Serif`;
            
            const isLight = document.documentElement.getAttribute("data-theme") === "light";
            ctx.fillStyle = isLight ? "#0f172a" : "#dbeafe";
            
            ctx.fillText(label, node.x + radius + 2, node.y + radius + 2);
          }}
        />
      )}
    </div>
  );
}
