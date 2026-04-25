import type {
  CreateNodeRequest,
  DeleteNodeResponse,
  DiffResponse,
  GraphNode,
  GraphSnapshot,
  MergeResponse,
  RepoConfigResponse,
  RunNodeResponse,
} from "../types";

export class ApiError extends Error {
  constructor(message: string, readonly status: number, readonly body?: unknown) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  const text = await response.text();
  const body = text ? safeJson(text) : null;
  if (!response.ok) {
    const detail = (body && typeof body === "object" && "detail" in body)
      ? String((body as { detail: unknown }).detail)
      : response.statusText;
    throw new ApiError(`${response.status} ${detail}`, response.status, body);
  }
  return body as T;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function fetchGraph(): Promise<GraphSnapshot> {
  return request<GraphSnapshot>("/api/v1/graph");
}

export async function fetchRepoConfig(): Promise<RepoConfigResponse> {
  return request<RepoConfigResponse>("/api/v1/repo");
}

export async function createNode(payload: CreateNodeRequest): Promise<GraphNode> {
  return request<GraphNode>("/api/v1/nodes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteNode(nodeId: string): Promise<DeleteNodeResponse> {
  return request<DeleteNodeResponse>(`/api/v1/nodes/${nodeId}`, { method: "DELETE" });
}

export async function runNode(nodeId: string): Promise<RunNodeResponse> {
  return request<RunNodeResponse>(`/api/v1/nodes/${nodeId}/run`, { method: "POST" });
}

export async function fetchDiff(nodeId: string): Promise<DiffResponse> {
  return request<DiffResponse>(`/api/v1/nodes/${nodeId}/diff`);
}

export async function mergeBranch(nodeId: string): Promise<MergeResponse> {
  return request<MergeResponse>(`/api/v1/nodes/${nodeId}/merge`, { method: "POST" });
}
