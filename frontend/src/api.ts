import type {
  DesignState, DocumentInfo, Domain, Entity, Feature, Issue, Project, Relationship, Requirement, StageKey, TraceRow,
} from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `${res.status} ${res.statusText}`);
  }
  if (res.status === 204) return undefined as T;
  const type = res.headers.get("content-type") ?? "";
  return (type.includes("application/json") ? res.json() : res.text()) as Promise<T>;
}

const json = (method: string, body: unknown): RequestInit => ({
  method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});

export const api = {
  domains: () => request<Domain[]>("/domains"),
  projects: () => request<Project[]>("/projects"),
  project: (id: number) => request<Project>(`/projects/${id}`),
  createProject: (name: string, domain: string) => request<Project>("/projects", json("POST", { name, domain })),

  documents: (id: number) => request<DocumentInfo[]>(`/projects/${id}/documents`),
  uploadDocument: (id: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<DocumentInfo>(`/projects/${id}/documents`, { method: "POST", body: form });
  },
  addTextDocument: (id: number, filename: string, text: string) =>
    request<DocumentInfo>(`/projects/${id}/documents/text`, json("POST", { filename, text })),
  deleteDocument: (id: number, docId: number) => request<void>(`/projects/${id}/documents/${docId}`, { method: "DELETE" }),

  design: (id: number) => request<DesignState>(`/projects/${id}/design`),
  generate: (id: number, stage: StageKey) => request<DesignState>(`/projects/${id}/stages/${stage}/generate`, { method: "POST" }),
  approve: (id: number, stage: StageKey) => request<unknown>(`/projects/${id}/stages/${stage}/approve`, { method: "POST" }),
  saveRequirements: (id: number, requirements: Requirement[]) =>
    request<DesignState>(`/projects/${id}/design/requirements`, json("PUT", { requirements })),
  saveFeatures: (id: number, features: Feature[]) =>
    request<DesignState>(`/projects/${id}/design/features`, json("PUT", { features })),
  saveDataModel: (id: number, entities: Entity[], relationships: Relationship[]) =>
    request<DesignState>(`/projects/${id}/design/data_model`, json("PUT", { entities, relationships })),

  trace: (id: number) => request<TraceRow[]>(`/projects/${id}/trace`),
  review: (id: number) => request<Issue[]>(`/projects/${id}/review`, { method: "POST" }),
  issues: (id: number) => request<Issue[]>(`/projects/${id}/issues`),
  setIssueStatus: (id: number, issueId: number, status: Issue["status"]) =>
    request<Issue>(`/projects/${id}/issues/${issueId}`, json("PATCH", { status })),
  ddl: (id: number) => request<string>(`/projects/${id}/export/ddl`),
  mermaid: (id: number) => request<string>(`/projects/${id}/export/mermaid`),
};
