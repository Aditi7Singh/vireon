"use client";

/**
 * SankeyChart
 * ===========
 * Pure-SVG Sankey diagram — no extra dependencies.
 * Shows Cash Flow: Revenue → Cost buckets → Net Profit / Net Loss
 */

import React, { useMemo } from "react";

export interface SankeyNode {
  id: string;
  label: string;
}

export interface SankeyLink {
  source: string;
  target: string;
  value: number;
}

interface SankeyChartProps {
  nodes: SankeyNode[];
  links: SankeyLink[];
  width?: number;
  height?: number;
  onNodeClick?: (nodeId: string) => void;
}

const NODE_WIDTH = 20;
const NODE_PADDING = 16;
const COLORS: Record<string, string> = {
  Revenue:    "#059669",
  COGS:       "#ef4444",
  GrossProfit:"#0284c7",
  RD:         "#7c3aed",
  SalesMktg:  "#d97706",
  GA:         "#6b7280",
  NetProfit:  "#10b981",
  NetLoss:    "#dc2626",
};
const DEFAULT_COLOR = "#94a3b8";

function formatK(v: number): string {
  if (Math.abs(v) >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (Math.abs(v) >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
}

// Simple topological layout: columns based on dependency depth
function layoutNodes(
  nodes: SankeyNode[],
  links: SankeyLink[],
  width: number,
  height: number
) {
  // Determine columns (depth)
  const inDegree: Record<string, number> = {};
  const outDegree: Record<string, number> = {};
  nodes.forEach((n) => { inDegree[n.id] = 0; outDegree[n.id] = 0; });
  links.forEach((l) => { inDegree[l.target] = (inDegree[l.target] || 0) + 1; });
  links.forEach((l) => { outDegree[l.source] = (outDegree[l.source] || 0) + 1; });

  const columns: string[][] = [];
  const visited = new Set<string>();

  // Column 0: source nodes (no incoming links)
  const col0 = nodes.filter((n) => !inDegree[n.id] || inDegree[n.id] === 0).map((n) => n.id);
  columns.push(col0);
  col0.forEach((id) => visited.add(id));

  // Remaining columns
  let remaining = nodes.filter((n) => !visited.has(n.id));
  while (remaining.length > 0) {
    const col = remaining.filter((n) => {
      const srcs = links.filter((l) => l.target === n.id).map((l) => l.source);
      return srcs.every((s) => visited.has(s));
    });
    if (col.length === 0) {
      // Avoid infinite loop if circular
      col.push(remaining[0]);
    }
    const colIds = col.map((n) => n.id);
    columns.push(colIds);
    colIds.forEach((id) => visited.add(id));
    remaining = remaining.filter((n) => !visited.has(n.id));
  }

  // Node value = sum of outgoing link values (or incoming if no outgoing)
  const nodeValues: Record<string, number> = {};
  nodes.forEach((n) => {
    const outVal = links.filter((l) => l.source === n.id).reduce((s, l) => s + l.value, 0);
    const inVal = links.filter((l) => l.target === n.id).reduce((s, l) => s + l.value, 0);
    nodeValues[n.id] = outVal || inVal || 1;
  });

  // Lay out x positions
  const colX = columns.map((_, ci) =>
    (width - NODE_WIDTH) * (ci / Math.max(columns.length - 1, 1))
  );

  // Lay out y positions within each column
  const nodePos: Record<string, { x: number; y: number; height: number; value: number }> = {};
  const totalHeight = height - NODE_PADDING * 2;

  columns.forEach((col, ci) => {
    const colTotalVal = col.reduce((s, id) => s + (nodeValues[id] || 1), 0);
    let yOffset = NODE_PADDING;
    col.forEach((id) => {
      const val = nodeValues[id] || 1;
      const h = Math.max(20, (val / colTotalVal) * totalHeight - NODE_PADDING);
      nodePos[id] = { x: colX[ci], y: yOffset, height: h, value: val };
      yOffset += h + NODE_PADDING;
    });
  });

  return { nodePos, columns };
}

export default function SankeyChart({
  nodes,
  links,
  width = 700,
  height = 360,
  onNodeClick,
}: SankeyChartProps) {
  const { nodePos } = useMemo(
    () => layoutNodes(nodes, links, width, height),
    [nodes, links, width, height]
  );

  // Pre-compute flow positions per node
  const linkPaths = useMemo(() => {
    const sourceYOffset: Record<string, number> = {};
    const targetYOffset: Record<string, number> = {};
    nodes.forEach((n) => {
      if (nodePos[n.id]) {
        sourceYOffset[n.id] = nodePos[n.id].y;
        targetYOffset[n.id] = nodePos[n.id].y;
      }
    });

    return links.map((link) => {
      const src = nodePos[link.source];
      const tgt = nodePos[link.target];
      if (!src || !tgt) return null;

      const srcVal = src.value || 1;
      const tgtVal = tgt.value || 1;
      const srcH = (link.value / srcVal) * src.height;
      const tgtH = (link.value / tgtVal) * tgt.height;

      const sy0 = sourceYOffset[link.source];
      const ty0 = targetYOffset[link.target];
      sourceYOffset[link.source] = sy0 + srcH;
      targetYOffset[link.target] = ty0 + tgtH;

      const x0 = src.x + NODE_WIDTH;
      const x1 = tgt.x;
      const cx = (x0 + x1) / 2;

      const path = `M${x0},${sy0} C${cx},${sy0} ${cx},${ty0} ${x1},${ty0}
                    L${x1},${ty0 + tgtH} C${cx},${ty0 + tgtH} ${cx},${sy0 + srcH} ${x0},${sy0 + srcH} Z`;

      return { path, link, srcH, tgtH };
    });
  }, [links, nodePos, nodes]);

  return (
    <svg
      width="100%"
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="xMidYMid meet"
      style={{ overflow: "visible" }}
    >
      {/* Links */}
      {linkPaths.map((lp, i) => {
        if (!lp) return null;
        const color = COLORS[lp.link.source] || DEFAULT_COLOR;
        return (
          <path
            key={i}
            d={lp.path}
            fill={color}
            opacity={0.35}
            stroke={color}
            strokeWidth={0.5}
          />
        );
      })}

      {/* Nodes */}
      {nodes.map((node) => {
        const pos = nodePos[node.id];
        if (!pos) return null;
        const color = COLORS[node.id] || DEFAULT_COLOR;
        const clickable = !!onNodeClick;
        return (
          <g
            key={node.id}
            onClick={() => onNodeClick?.(node.id)}
            style={{ cursor: clickable ? "pointer" : "default" }}
          >
            <rect
              x={pos.x}
              y={pos.y}
              width={NODE_WIDTH}
              height={pos.height}
              fill={color}
              rx={4}
              ry={4}
              opacity={0.9}
            />
            {/* Label to the right of node */}
            <text
              x={pos.x + NODE_WIDTH + 6}
              y={pos.y + pos.height / 2}
              dominantBaseline="middle"
              fontSize={11}
              fontWeight={500}
              fill="#3d2f1e"
              fontFamily="inherit"
            >
              {node.label}
            </text>
            {/* Value label */}
            <text
              x={pos.x + NODE_WIDTH + 6}
              y={pos.y + pos.height / 2 + 14}
              dominantBaseline="middle"
              fontSize={10}
              fill="#7a6252"
              fontFamily="inherit"
            >
              {formatK(pos.value)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
