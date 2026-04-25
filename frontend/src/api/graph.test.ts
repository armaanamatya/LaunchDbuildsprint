import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, createNode, fetchGraph, mergeBranch } from "./graph";

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch);
});

afterEach(() => {
  mockFetch.mockReset();
  vi.unstubAllGlobals();
});

describe("fetchGraph", () => {
  it("returns parsed snapshot on 200", async () => {
    mockFetch.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          nodes: [],
          edges: [],
          base_branch: "main",
          worktree_root: ".agent-worktrees",
        }),
        { status: 200 },
      ),
    );

    const snap = await fetchGraph();
    expect(snap.base_branch).toBe("main");
  });

  it("throws ApiError on non-200", async () => {
    mockFetch.mockResolvedValueOnce(new Response("boom", { status: 500 }));
    await expect(fetchGraph()).rejects.toBeInstanceOf(ApiError);
  });
});

describe("createNode", () => {
  it("POSTs JSON body and returns the new node", async () => {
    const node = {
      id: "node-1",
      label: "A",
      status: "idle",
      branch_name: "agent/node-1",
      worktree_path: ".agent-worktrees/agent-node-1",
      parent_id: "root",
      prompt: "p",
      summary: null,
      created_at: "2026-04-25T00:00:00Z",
      updated_at: "2026-04-25T00:00:00Z",
    };
    mockFetch.mockResolvedValueOnce(new Response(JSON.stringify(node), { status: 200 }));

    const result = await createNode({ label: "A", parent_id: "root", prompt: "p" });

    expect(result.id).toBe("node-1");
    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toBe("/api/v1/nodes");
    expect(init?.method).toBe("POST");
    expect(JSON.parse(String(init?.body))).toEqual({
      label: "A",
      parent_id: "root",
      prompt: "p",
    });
  });
});

describe("mergeBranch", () => {
  it("surfaces 409 conflict as ApiError with status 409", async () => {
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "merge conflict" }), { status: 409 }),
    );

    try {
      await mergeBranch("node-1");
      expect.fail("should have thrown");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).status).toBe(409);
    }
  });
});
