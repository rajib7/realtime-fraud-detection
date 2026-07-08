import React from "react";
import { motion } from "framer-motion";
import { Server, Database, ShieldAlert, Cpu, Radio } from "lucide-react";

/**
 * Animated architecture diagram: Tx Service -> Kafka -> Fraud Scoring (ML API) -> Alert Service
 */
export default function ArchitectureDiagram({ topics = {} }) {
  const nodes = [
    {
      id: "tx",
      x: 60,
      title: "Transaction Service",
      subtitle: "POST /api/tx/transactions",
      Icon: Server,
      accent: "#00E5FF",
      count: topics["transactions.raw"] || 0,
      topic: "transactions.raw",
    },
    {
      id: "fraud",
      x: 380,
      title: "Fraud Scoring Service",
      subtitle: "consumes transactions.raw",
      Icon: Cpu,
      accent: "#FFB000",
      count: topics["fraud.scores"] || 0,
      topic: "fraud.scores",
    },
    {
      id: "alert",
      x: 700,
      title: "Alert Service",
      subtitle: "consumes fraud.scores",
      Icon: ShieldAlert,
      accent: "#FF3366",
      count: topics["alerts.raised"] || 0,
      topic: "alerts.raised",
    },
  ];

  const links = [
    { from: nodes[0], to: nodes[1], label: "transactions.raw" },
    { from: nodes[1], to: nodes[2], label: "fraud.scores" },
  ];

  return (
    <div className="card-surface p-4 sm:p-6 relative overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-xs uppercase tracking-[0.2em] font-semibold text-[#F8FAFC]">
            Event-Driven Architecture
          </div>
          <div className="text-[11px] font-mono text-[#64748B]">
            3 microservices · 3 kafka topics · async at-least-once semantics
          </div>
        </div>
        <span className="chip text-[#00E5FF] bg-[#00E5FF]/10 border-[#00E5FF]/30">
          <Radio size={10} />
          live topology
        </span>
      </div>

      <div className="w-full overflow-x-auto">
        <svg
          viewBox="0 0 900 260"
          className="w-full min-w-[820px]"
          style={{ height: 260 }}
        >
          <defs>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#333A4A" />
            </marker>
          </defs>

          {/* grid backdrop */}
          <g opacity="0.5">
            {Array.from({ length: 10 }).map((_, i) => (
              <line
                key={`v${i}`}
                x1={i * 90}
                y1={0}
                x2={i * 90}
                y2={260}
                stroke="#161a22"
                strokeWidth={1}
              />
            ))}
            {Array.from({ length: 4 }).map((_, i) => (
              <line
                key={`h${i}`}
                x1={0}
                y1={i * 65}
                x2={900}
                y2={i * 65}
                stroke="#161a22"
                strokeWidth={1}
              />
            ))}
          </g>

          {/* links */}
          {links.map((l, idx) => {
            const cx1 = l.from.x + 160;
            const cx2 = l.to.x;
            const yMid = 130;
            const pathD = `M ${cx1} ${yMid} C ${cx1 + 60} ${yMid}, ${cx2 - 60} ${yMid}, ${cx2} ${yMid}`;
            return (
              <g key={idx}>
                <path
                  d={pathD}
                  fill="none"
                  stroke="#333A4A"
                  strokeWidth={1.5}
                  strokeDasharray="6 6"
                  markerEnd="url(#arrow)"
                />
                <text
                  x={(cx1 + cx2) / 2}
                  y={yMid - 12}
                  fill="#94A3B8"
                  fontFamily="JetBrains Mono, monospace"
                  fontSize="10"
                  textAnchor="middle"
                >
                  {l.label}
                </text>
                {/* animated particles */}
                {[0, 0.33, 0.66].map((delay) => (
                  <motion.circle
                    key={`p-${idx}-${delay}`}
                    r={3}
                    fill={l.from.accent}
                    initial={{ opacity: 0 }}
                    animate={{
                      offsetDistance: ["0%", "100%"],
                      opacity: [0, 1, 1, 0],
                    }}
                    transition={{
                      duration: 2.4,
                      delay,
                      repeat: Infinity,
                      ease: "linear",
                    }}
                    style={{
                      offsetPath: `path("${pathD}")`,
                    }}
                  />
                ))}
              </g>
            );
          })}

          {/* nodes */}
          {nodes.map((n) => (
            <g key={n.id}>
              <rect
                x={n.x}
                y={70}
                width={160}
                height={120}
                rx={6}
                fill="#0f1218"
                stroke={n.accent}
                strokeOpacity={0.35}
                strokeWidth={1}
              />
              <rect
                x={n.x}
                y={70}
                width={160}
                height={22}
                rx={6}
                fill={n.accent}
                fillOpacity={0.08}
              />
              <text
                x={n.x + 12}
                y={86}
                fill={n.accent}
                fontFamily="JetBrains Mono, monospace"
                fontSize="10"
                fontWeight="600"
                letterSpacing="1"
              >
                {n.id.toUpperCase()}
              </text>
              <text
                x={n.x + 148}
                y={86}
                textAnchor="end"
                fill="#94A3B8"
                fontFamily="JetBrains Mono, monospace"
                fontSize="10"
              >
                UP
              </text>
              <text
                x={n.x + 12}
                y={116}
                fill="#F8FAFC"
                fontFamily="IBM Plex Sans, sans-serif"
                fontSize="12"
                fontWeight="600"
              >
                {n.title}
              </text>
              <text
                x={n.x + 12}
                y={134}
                fill="#94A3B8"
                fontFamily="JetBrains Mono, monospace"
                fontSize="10"
              >
                {n.subtitle}
              </text>
              <text
                x={n.x + 12}
                y={168}
                fill={n.accent}
                fontFamily="JetBrains Mono, monospace"
                fontSize="20"
                fontWeight="600"
              >
                {n.count}
              </text>
              <text
                x={n.x + 12}
                y={182}
                fill="#64748B"
                fontFamily="JetBrains Mono, monospace"
                fontSize="9"
              >
                events published
              </text>
            </g>
          ))}

          {/* ML API callout */}
          <g>
            <rect
              x={380}
              y={210}
              width={160}
              height={40}
              rx={4}
              fill="#0f1218"
              stroke="#FFB000"
              strokeOpacity={0.3}
              strokeDasharray="4 4"
            />
            <text
              x={460}
              y={228}
              textAnchor="middle"
              fill="#FFB000"
              fontFamily="JetBrains Mono, monospace"
              fontSize="10"
              fontWeight="600"
            >
              ML MODEL API
            </text>
            <text
              x={460}
              y={242}
              textAnchor="middle"
              fill="#94A3B8"
              fontFamily="JetBrains Mono, monospace"
              fontSize="9"
            >
              POST /api/fraud/score
            </text>
            <path
              d="M 460 210 L 460 190"
              stroke="#FFB000"
              strokeOpacity={0.4}
              strokeDasharray="3 3"
            />
          </g>
        </svg>
      </div>

      <div className="grid grid-cols-3 gap-3 mt-4">
        {nodes.map((n) => (
          <div
            key={n.id}
            className="border border-[#222630] rounded p-3 flex items-center gap-3"
          >
            <div
              className="w-8 h-8 rounded flex items-center justify-center"
              style={{ background: `${n.accent}18`, color: n.accent }}
            >
              <n.Icon size={16} />
            </div>
            <div className="min-w-0">
              <div className="font-mono text-[11px] text-[#94A3B8] truncate">
                {n.subtitle}
              </div>
              <div className="text-xs text-[#F8FAFC]">{n.title}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
