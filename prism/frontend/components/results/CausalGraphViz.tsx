"use client";

import { useEffect, useRef } from "react";
import * as d3 from "d3";

interface Node extends d3.SimulationNodeDatum {
  id: string;
  group: "disease" | "biomarker" | "factor";
  label: string;
  value: number;
}

interface Link extends d3.SimulationLinkDatum<Node> {
  source: string | Node;
  target: string | Node;
  weight: number;
}

interface CausalGraphVizProps {
  dotString: string; // Simplified for now, passing nodes/links directly would be better in prod
  attributions: Record<string, number>;
  primaryDiagnosis: string;
}

export default function CausalGraphViz({ attributions, primaryDiagnosis }: CausalGraphVizProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !attributions) return;

    // Build mock graph from attributions for visualization
    const nodes: Node[] = [
      { id: "target", group: "disease", label: primaryDiagnosis || "Disease", value: 1.0 },
    ];
    const links: Link[] = [];

    Object.entries(attributions).forEach(([factor, weight]) => {
      const id = `factor_${factor}`;
      nodes.push({
        id,
        group: factor.includes("cough") || factor.includes("rppg") ? "biomarker" : "factor",
        label: factor.replace(/_/g, " "),
        value: weight,
      });
      links.push({
        source: id,
        target: "target",
        weight: weight,
      });
    });

    const width = 400;
    const height = 300;

    const svg = d3.select(svgRef.current)
      .attr("viewBox", [0, 0, width, height]);

    svg.selectAll("*").remove();

    const simulation = d3.forceSimulation<Node>(nodes)
      .force("link", d3.forceLink<Node, Link>(links).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2));

    const link = svg.append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", "#4b5563")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", d => Math.max(1, d.weight * 10));

    const nodeColors = {
      disease: "#ef4444", // red
      biomarker: "#3b82f6", // blue
      factor: "#f59e0b", // orange
    };

    const node = svg
      .append("g")
      .selectAll<SVGGElement, Node>("g")
      .data(nodes)
      .join((enter) => enter.append("g"))
      .call(
        d3
          .drag<SVGGElement, Node>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }),
      );

    node.append("circle")
      .attr("r", d => d.group === "disease" ? 20 : 10 + d.value * 15)
      .attr("fill", d => nodeColors[d.group])
      .attr("stroke", "#1f2937")
      .attr("stroke-width", 2);

    node.append("text")
      .text(d => d.label)
      .attr("x", 0)
      .attr("y", d => d.group === "disease" ? 30 : 20 + d.value * 15)
      .attr("text-anchor", "middle")
      .attr("fill", "#94a3b8")
      .attr("font-size", "10px");

    simulation.on("tick", () => {
      link
        .attr("x1", d => (d.source as Node).x!)
        .attr("y1", d => (d.source as Node).y!)
        .attr("x2", d => (d.target as Node).x!)
        .attr("y2", d => (d.target as Node).y!);

      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [attributions, primaryDiagnosis]);

  return (
    <div className="glass-card p-4 flex flex-col items-center">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide self-start mb-2">Causal Graph</h3>
      <svg ref={svgRef} className="w-full h-64" />
      <div className="flex gap-4 mt-2 text-xs text-gray-500">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" /> Disease</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500" /> Biomarker</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-500" /> Risk Factor</span>
      </div>
    </div>
  );
}
