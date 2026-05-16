"use client";

import { useEffect, useState, useCallback } from "react";
import FederatedDashboard from "@/components/federated/FederatedDashboard";
import NodeParticipationTable from "@/components/federated/NodeParticipationTable";
import PrivacyBudgetGauge from "@/components/federated/PrivacyBudgetGauge";
import RoundDetailTable from "@/components/federated/RoundDetailTable";
import ModelVersionHistory from "@/components/federated/ModelVersionHistory";
import DPExplainerPanel from "@/components/federated/DPExplainerPanel";
import TrainingControls from "@/components/federated/TrainingControls";
import { getFLStatus, getFLNodes, getFLRounds, getModelVersionHistory } from "@/lib/api";
import type { FLStatus, FLNode, FLRound, ModelVersion } from "@/lib/types";

export default function FederatedPage() {
  const [status, setStatus] = useState<FLStatus | null>(null);
  const [nodes, setNodes] = useState<FLNode[]>([]);
  const [rounds, setRounds] = useState<FLRound[]>([]);
  const [modelVersions, setModelVersions] = useState<ModelVersion[]>([]);
  const [loadingNodes, setLoadingNodes] = useState(true);
  const [loadingRounds, setLoadingRounds] = useState(true);
  const [loadingVersions, setLoadingVersions] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const s = await getFLStatus();
      setStatus(s);
    } catch (err) {
      console.error("FL status error", err);
    }
  }, []);

  const fetchNodes = useCallback(async () => {
    try {
      const n = await getFLNodes();
      setNodes(Array.isArray(n) ? n : []);
    } catch (err) {
      console.error("FL nodes error", err);
      setNodes([]);
    } finally {
      setLoadingNodes(false);
    }
  }, []);

  const fetchRounds = useCallback(async () => {
    try {
      const r = await getFLRounds(30);
      setRounds(Array.isArray(r) ? r : (r as { rounds: FLRound[] }).rounds || []);
    } catch (err) {
      console.error("FL rounds error", err);
      setRounds([]);
    } finally {
      setLoadingRounds(false);
    }
  }, []);

  const fetchVersions = useCallback(async () => {
    try {
      const v = await getModelVersionHistory();
      setModelVersions(Array.isArray(v) ? v : []);
    } catch (err) {
      console.error("Model versions error", err);
      setModelVersions([]);
    } finally {
      setLoadingVersions(false);
    }
  }, []);

  useEffect(() => {
    setTimeout(() => {
      fetchStatus();
      fetchNodes();
      fetchRounds();
      fetchVersions();
    }, 0);

    // Poll status every 10s, nodes every 30s
    const statusInterval = setInterval(fetchStatus, 10000);
    const nodesInterval = setInterval(fetchNodes, 30000);
    return () => {
      clearInterval(statusInterval);
      clearInterval(nodesInterval);
    };
  }, [fetchStatus, fetchNodes, fetchRounds, fetchVersions]);

  const handleRoundTriggered = () => {
    // Refresh status and rounds after triggering
    setTimeout(() => {
      fetchStatus();
      fetchRounds();
    }, 1000);
  };

  return (
    <div className="p-6 md:p-10 space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--text)" }}>Federated Learning Operations</h1>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Monitor nodes, privacy budget, model convergence, and trigger training rounds</p>
      </div>

      {/* Top row: Privacy gauge + Training controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <PrivacyBudgetGauge
          currentEpsilon={status?.cumulative_dp_epsilon ?? 0}
          maxEpsilon={10}
          delta={1e-5}
          noiseMultiplier={1.1}
        />
        <TrainingControls
          currentRound={status?.current_round ?? 0}
          totalNodes={status?.total_nodes ?? 0}
          onRoundTriggered={handleRoundTriggered}
        />
      </div>

      {/* DP Explainer */}
      <DPExplainerPanel
        epsilon={status?.cumulative_dp_epsilon ?? 0}
        delta={1e-5}
        noiseMultiplier={1.1}
        mechanism="Gaussian"
      />

      {/* Node Participation */}
      <NodeParticipationTable nodes={nodes} loading={loadingNodes} />

      {/* Convergence Chart (existing component) */}
      <div>
        <h2 className="text-lg font-bold mb-4" style={{ color: "var(--text)" }}>Model Convergence</h2>
        <FederatedDashboard />
      </div>

      {/* Round Detail Table */}
      <RoundDetailTable rounds={rounds} loading={loadingRounds} />

      {/* Model Version History */}
      <ModelVersionHistory versions={modelVersions} loading={loadingVersions} />
    </div>
  );
}
