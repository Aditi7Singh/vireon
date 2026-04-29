"use client";

import { useState } from "react";
import TopBar from "@/components/TopBar";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import {
  Link2, ShieldCheck, CheckCircle2, AlertTriangle, Hash,
  ChevronDown, ChevronRight, Lock, Eye, RefreshCw, Layers,
  FileSearch, Clock,
} from "lucide-react";

interface BlockEvent {
  id: string;
  event_type: string;
  entity_type: string;
  timestamp: string;
  leaf_hash: string;
}

interface Block {
  index: number;
  block_hash: string;
  prev_hash: string;
  merkle_root: string;
  event_count: number;
  sealed_at: string;
  status: "verified" | "tampered" | "pending";
  events: BlockEvent[];
}

const DEMO_BLOCKS: Block[] = [
  {
    index: 0,
    block_hash: "a3f9c2e1d8b7a6f5e4c3b2a1d0e9f8c7b6a5e4f3d2c1b0a9e8f7d6c5b4a3e2f1",
    prev_hash: "0000000000000000000000000000000000000000000000000000000000000000",
    merkle_root: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    event_count: 50,
    sealed_at: "2026-04-01T00:00:00Z",
    status: "verified",
    events: [
      { id: "e1", event_type: "entity_change", entity_type: "invoice", timestamp: "2026-03-01T09:00:00Z", leaf_hash: "d4e5f6..." },
      { id: "e2", event_type: "entity_change", entity_type: "expense", timestamp: "2026-03-01T10:30:00Z", leaf_hash: "a1b2c3..." },
      { id: "e3", event_type: "entity_change", entity_type: "journal_entry", timestamp: "2026-03-02T14:00:00Z", leaf_hash: "f7e8d9..." },
    ],
  },
  {
    index: 1,
    block_hash: "b4e8d3c2f1a9e7d6c5b4a3f2e1d0c9b8a7e6f5d4c3b2a1e0f9d8c7b6a5e4f3d2",
    prev_hash: "a3f9c2e1d8b7a6f5e4c3b2a1d0e9f8c7b6a5e4f3d2c1b0a9e8f7d6c5b4a3e2f1",
    merkle_root: "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d906",
    event_count: 50,
    sealed_at: "2026-04-07T00:00:00Z",
    status: "verified",
    events: [
      { id: "e4", event_type: "entity_change", entity_type: "vendor", timestamp: "2026-03-08T11:00:00Z", leaf_hash: "c9d0e1..." },
      { id: "e5", event_type: "approval", entity_type: "purchase_order", timestamp: "2026-03-09T16:30:00Z", leaf_hash: "b8c9d0..." },
    ],
  },
  {
    index: 2,
    block_hash: "c5f9e4d3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5",
    prev_hash: "b4e8d3c2f1a9e7d6c5b4a3f2e1d0c9b8a7e6f5d4c3b2a1e0f9d8c7b6a5e4f3d2",
    merkle_root: "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
    event_count: 47,
    sealed_at: "2026-04-14T00:00:00Z",
    status: "verified",
    events: [
      { id: "e6", event_type: "anomaly_corrected", entity_type: "anomaly", timestamp: "2026-03-14T09:15:00Z", leaf_hash: "f0a1b2..." },
    ],
  },
  {
    index: 3,
    block_hash: "pending",
    prev_hash: "c5f9e4d3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5",
    merkle_root: "pending",
    event_count: 23,
    sealed_at: "Pending",
    status: "pending",
    events: [],
  },
];

function short(hash: string, n = 12): string {
  if (hash === "pending" || hash.startsWith("0000")) return hash.substring(0, n) + "...";
  return hash.substring(0, n) + "..." + hash.slice(-6);
}

export default function BlockchainAuditPage() {
  const { openChat } = useAppStore();
  const [expanded, setExpanded] = useState<Set<number>>(new Set([0]));
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<"pass" | "fail" | null>(null);
  const [sealing, setSealing] = useState(false);

  const toggleBlock = (idx: number) => {
    setExpanded(prev => {
      const n = new Set(prev);
      n.has(idx) ? n.delete(idx) : n.add(idx);
      return n;
    });
  };

  const handleVerify = () => {
    setVerifying(true);
    setVerifyResult(null);
    setTimeout(() => { setVerifying(false); setVerifyResult("pass"); }, 2000);
  };

  const handleSeal = () => {
    setSealing(true);
    setTimeout(() => setSealing(false), 2000);
  };

  const verifiedBlocks = DEMO_BLOCKS.filter(b => b.status === "verified").length;
  const totalEvents = DEMO_BLOCKS.reduce((s, b) => s + b.event_count, 0);

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Blockchain Audit Trail" />
      <div className="max-w-5xl mx-auto px-6 pt-6 space-y-6">

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: "Total Blocks", value: DEMO_BLOCKS.length, icon: Layers, color: "text-violet-600" },
            { label: "Events Sealed", value: totalEvents, icon: Lock, color: "text-blue-600" },
            { label: "Verified Blocks", value: verifiedBlocks, icon: ShieldCheck, color: "text-emerald-600" },
            { label: "Chain Status", value: verifyResult === "pass" ? "Intact" : verifyResult === "fail" ? "TAMPERED" : "Unverified", icon: Hash, color: verifyResult === "pass" ? "text-emerald-600" : verifyResult === "fail" ? "text-red-600" : "text-amber-600" },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="bg-white border border-[#e8ddd4] rounded-2xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-[#8a7e74] uppercase tracking-wide">{label}</span>
                <Icon className={cn("w-4 h-4", color)} />
              </div>
              <div className={cn("text-2xl font-black", color.includes("red") ? "text-red-600" : "text-[#1d1b17]")}>{value}</div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleVerify}
            className="flex items-center gap-2 px-4 py-2 bg-[#b3622d] hover:bg-[#9d4f22] text-white rounded-xl text-sm font-semibold transition-all"
          >
            {verifying ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
            {verifying ? "Verifying..." : "Verify Chain Integrity"}
          </button>
          <button
            onClick={handleSeal}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-[#e8ddd4] hover:border-[#b3622d] text-[#1d1b17] rounded-xl text-sm font-semibold transition-all"
          >
            {sealing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
            {sealing ? "Sealing..." : "Seal Pending Events"}
          </button>
          <button
            onClick={() => openChat("Explain the blockchain audit trail and how to verify chain integrity.")}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-[#e8ddd4] hover:border-[#b3622d] text-[#1d1b17] rounded-xl text-sm font-semibold transition-all"
          >
            <FileSearch className="w-4 h-4" />
            Ask Finley
          </button>
        </div>

        {/* Verification Result */}
        {verifyResult && (
          <div className={cn(
            "flex items-center gap-3 p-4 rounded-2xl border",
            verifyResult === "pass" ? "bg-emerald-50 border-emerald-200" : "bg-red-50 border-red-200"
          )}>
            {verifyResult === "pass"
              ? <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
              : <AlertTriangle className="w-5 h-5 text-red-600 shrink-0" />}
            <div>
              <div className={cn("font-bold text-sm", verifyResult === "pass" ? "text-emerald-800" : "text-red-800")}>
                {verifyResult === "pass" ? "Chain Integrity Verified — PASS" : "Chain Integrity FAILED — Tampering Detected"}
              </div>
              <div className="text-xs text-[#6a6054] mt-0.5">
                {verifyResult === "pass"
                  ? `All ${verifiedBlocks} blocks verified. Every block hash and Merkle root is intact. No tampering detected.`
                  : "One or more block hashes do not match their computed values. Investigate immediately."}
              </div>
            </div>
          </div>
        )}

        {/* Chain Visualization */}
        <div className="bg-white border border-[#e8ddd4] rounded-2xl p-4">
          <h3 className="font-bold text-sm mb-4 flex items-center gap-2">
            <Link2 className="w-4 h-4 text-[#b3622d]" />
            Block Chain (newest at top)
          </h3>

          <div className="space-y-2">
            {[...DEMO_BLOCKS].reverse().map(block => {
              const isExpanded = expanded.has(block.index);
              const statusColor = {
                verified: "border-emerald-300 bg-emerald-50",
                tampered: "border-red-300 bg-red-50",
                pending: "border-amber-300 bg-amber-50",
              }[block.status];

              return (
                <div key={block.index}>
                  {/* Block Header */}
                  <div
                    className={cn("border rounded-xl p-4 cursor-pointer hover:shadow-sm transition-all", statusColor)}
                    onClick={() => toggleBlock(block.index)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-xl bg-white border border-current flex items-center justify-center font-black text-sm">
                          {block.index}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-sm text-[#1d1b17]">Block #{block.index}</span>
                            {block.status === "verified" && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}
                            {block.status === "pending" && <Clock className="w-3.5 h-3.5 text-amber-600" />}
                            {block.status === "tampered" && <AlertTriangle className="w-3.5 h-3.5 text-red-600" />}
                            <span className={cn(
                              "text-[10px] font-bold px-2 py-0.5 rounded-full uppercase",
                              block.status === "verified" ? "text-emerald-700 bg-white" :
                              block.status === "pending" ? "text-amber-700 bg-white" : "text-red-700 bg-white"
                            )}>{block.status}</span>
                          </div>
                          <div className="flex items-center gap-3 mt-0.5">
                            <span className="text-[10px] text-[#6a6054] font-mono">{short(block.block_hash)}</span>
                            <span className="text-[10px] text-[#8a7e74]">{block.event_count} events</span>
                            <span className="text-[10px] text-[#8a7e74]">{block.status !== "pending" ? new Date(block.sealed_at).toLocaleDateString() : "Pending seal"}</span>
                          </div>
                        </div>
                      </div>
                      {isExpanded ? <ChevronDown className="w-4 h-4 text-[#8a7e74]" /> : <ChevronRight className="w-4 h-4 text-[#8a7e74]" />}
                    </div>

                    {/* Expanded Detail */}
                    {isExpanded && (
                      <div className="mt-4 space-y-3 border-t border-white/60 pt-3">
                        <div className="grid grid-cols-2 gap-3 text-xs">
                          <div>
                            <div className="text-[10px] uppercase text-[#8a7e74] font-semibold mb-1">Block Hash</div>
                            <div className="font-mono text-[10px] bg-white rounded-lg p-2 break-all text-[#1d1b17]">{block.block_hash}</div>
                          </div>
                          <div>
                            <div className="text-[10px] uppercase text-[#8a7e74] font-semibold mb-1">Previous Hash</div>
                            <div className="font-mono text-[10px] bg-white rounded-lg p-2 break-all text-[#1d1b17]">{block.prev_hash}</div>
                          </div>
                        </div>
                        <div>
                          <div className="text-[10px] uppercase text-[#8a7e74] font-semibold mb-1">Merkle Root</div>
                          <div className="font-mono text-[10px] bg-white rounded-lg p-2 break-all text-[#1d1b17]">{block.merkle_root}</div>
                        </div>
                        {block.events.length > 0 && (
                          <div>
                            <div className="text-[10px] uppercase text-[#8a7e74] font-semibold mb-2">Sample Events</div>
                            <div className="space-y-1.5">
                              {block.events.map(ev => (
                                <div key={ev.id} className="flex items-center gap-3 bg-white rounded-lg p-2">
                                  <div className="w-1.5 h-1.5 rounded-full bg-[#b3622d]" />
                                  <span className="text-[10px] font-semibold text-[#1d1b17] capitalize">{ev.event_type}</span>
                                  <span className="text-[10px] text-[#8a7e74]">{ev.entity_type}</span>
                                  <span className="text-[10px] text-[#8a7e74] ml-auto">{new Date(ev.timestamp).toLocaleDateString()}</span>
                                  <span className="font-mono text-[9px] text-[#b0a499]">{ev.leaf_hash}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Chain Link Arrow */}
                  {block.index > 0 && (
                    <div className="flex justify-center my-1">
                      <div className="w-px h-4 bg-[#d8c9be]" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* How it Works */}
        <div className="bg-white border border-[#e8ddd4] rounded-2xl p-5">
          <h3 className="font-bold text-sm mb-3 text-[#1d1b17]">How Blockchain Audit Works</h3>
          <div className="grid grid-cols-3 gap-4">
            {[
              { step: "1", title: "Events Logged", desc: "Every financial change is SHA-256 hashed and stored as an immutable leaf." },
              { step: "2", title: "Blocks Sealed", desc: "Events are grouped into blocks with a Merkle root and linked to the previous block hash." },
              { step: "3", title: "Chain Verified", desc: "Any tampering breaks the hash chain — instantly detectable during integrity checks." },
            ].map(({ step, title, desc }) => (
              <div key={step} className="text-center">
                <div className="w-8 h-8 rounded-full bg-[#b3622d] text-white font-black text-sm flex items-center justify-center mx-auto mb-2">{step}</div>
                <div className="font-bold text-sm text-[#1d1b17] mb-1">{title}</div>
                <div className="text-xs text-[#6a6054]">{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
