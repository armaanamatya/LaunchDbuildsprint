import { describe, expect, it } from "vitest";
import { applyEvent, type GraphState } from "./applyEvent";
import type { GraphEvent, GraphNode } from "../types";

const node = (id: string, status: GraphNode["status"] = "idle"): GraphNode => ({
  id,
  label: id,
  status,
  branch_name: `agent/${id}`,
  worktree_path: `.agent-worktrees/${id}`,
  parent_id: id === "root" ? null : "root",
  prompt: null,
  summary: null,
  strategy: null,
  eval_passed: null,
  eval_failed: null,
  eval_summary: null,
  created_at: "2026-04-25T00:00:00Z",
  updated_at: "2026-04-25T00:00:00Z",
});

const baseState = (): GraphState => ({
  graph: {
    nodes: [node("root")],
    edges: [],
    base_branch: "main",
    worktree_root: ".agent-worktrees",
  },
  agentLogs: {},
  diffs: {},
});

const event = (
  type: GraphEvent["type"],
  data: Record<string, unknown>,
  node_id: string | null = null,
): GraphEvent => ({
  type,
  timestamp: "2026-04-25T00:00:01Z",
  node_id,
  data,
});

describe("applyEvent", () => {
  it("appends node on node.created", () => {
    const next = applyEvent(baseState(), event("node.created", { node: node("a") }));
    expect(next.graph.nodes.map((n) => n.id)).toEqual(["root", "a"]);
    expect(next.graph.edges).toEqual([{ id: "root->a", source: "root", target: "a" }]);
  });

  it("removes node and its edges on node.deleted", () => {
    let s = baseState();
    s = applyEvent(s, event("node.created", { node: node("a") }));
    s = applyEvent(s, event("node.deleted", { node_id: "a" }, "a"));
    expect(s.graph.nodes.find((n) => n.id === "a")).toBeUndefined();
    expect(s.graph.edges).toEqual([]);
  });

  it("infers running status from agent.started (backend does not send node.updated)", () => {
    let s = baseState();
    s = applyEvent(s, event("node.created", { node: node("a") }));
    s = applyEvent(
      s,
      event("agent.started", { prompt: "p", worktree_path: "/x" }, "a"),
    );
    expect(s.graph.nodes.find((n) => n.id === "a")?.status).toBe("running");
    expect(s.agentLogs["a"]).toHaveLength(1);
  });

  it("infers completed status from agent.completed", () => {
    let s = baseState();
    s = applyEvent(s, event("node.created", { node: node("a") }));
    s = applyEvent(s, event("agent.completed", {}, "a"));
    expect(s.graph.nodes.find((n) => n.id === "a")?.status).toBe("completed");
  });

  it("infers failed status from agent.failed", () => {
    let s = baseState();
    s = applyEvent(s, event("node.created", { node: node("a") }));
    s = applyEvent(s, event("agent.failed", { error: "boom" }, "a"));
    expect(s.graph.nodes.find((n) => n.id === "a")?.status).toBe("failed");
  });

  it("sets merged status from node.merged (no node payload)", () => {
    let s = baseState();
    s = applyEvent(s, event("node.created", { node: node("a") }));
    s = applyEvent(
      s,
      event("node.merged", { branch_name: "agent/a", target_branch: "main" }, "a"),
    );
    expect(s.graph.nodes.find((n) => n.id === "a")?.status).toBe("merged");
  });

  it("appends agent log entries on agent.text", () => {
    let s = baseState();
    s = applyEvent(s, event("node.created", { node: node("a") }));
    s = applyEvent(s, event("agent.text", { content: "hello" }, "a"));
    expect(s.agentLogs["a"]).toHaveLength(1);
    expect(s.agentLogs["a"][0].content).toBe("hello");
    expect(s.agentLogs["a"][0].type).toBe("text");
  });

  it("flags diff availability on node.diff_ready (does NOT cache full diff)", () => {
    let s = baseState();
    s = applyEvent(s, event("node.created", { node: node("a") }));
    s = applyEvent(
      s,
      event("node.diff_ready", { has_changes: true, diff_preview: "+ x" }, "a"),
    );
    expect(s.diffs["a"]).toEqual({ diff: "", has_changes: true });
  });

  it("ignores heartbeat", () => {
    const before = baseState();
    const after = applyEvent(before, event("heartbeat", {}));
    expect(after).toEqual(before);
  });

  it("ignores graph.connected (handshake only)", () => {
    const before = baseState();
    const after = applyEvent(
      before,
      event("graph.connected", { base_branch: "main", worktree_root: ".agent-worktrees" }),
    );
    expect(after).toEqual(before);
  });
});
