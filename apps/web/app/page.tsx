"use client";

import { useCallback, useEffect, useState } from "react";

type Snippet = {
  id: number;
  name: string;
  trigger: string;
  body: string;
  tags: string[];
  variables: Record<string, string>;
  version: number;
  updated_at: string;
};

type AuditLog = {
  id: number;
  workspace_id: number;
  user_id: number | null;
  action: string;
  meta: Record<string, string> | null;
  created_at: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [email, setEmail] = useState("");
  const [token, setToken] = useState<string | null>(null);
  const [workspaceId, setWorkspaceId] = useState(1);
  const [query, setQuery] = useState("");
  const [snippets, setSnippets] = useState<Snippet[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [auditLoading, setAuditLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    trigger: "",
    body: "",
    tags: "",
    variables: "",
  });

  const authed = Boolean(token);

  const handleLogin = async () => {
    setError(null);
    setMessage(null);
    try {
      const res = await fetch(`${API_BASE}/auth/magic`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) {
        throw new Error(`Failed to authenticate (${res.status})`);
      }
      const data = await res.json();
      const value = data.access_token ?? data.dev_token ?? null;
      if (!value) {
        throw new Error("Token not returned from API");
      }
      setToken(value);
      setMessage("Authenticated. Token stored in memory only.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown authentication error");
    }
  };

  const fetchSnippets = useCallback(async () => {
    if (!token) {
      setSnippets([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const params = query ? `?q=${encodeURIComponent(query)}` : "";
      const res = await fetch(
        `${API_BASE}/workspaces/${workspaceId}/snippets${params}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!res.ok) {
        throw new Error(`Failed to load snippets (${res.status})`);
      }
      const data: Snippet[] = await res.json();
      setSnippets(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error while fetching snippets");
    } finally {
      setLoading(false);
    }
  }, [query, token, workspaceId]);

  const fetchAuditLogs = useCallback(async () => {
    if (!token) {
      setAuditLogs([]);
      return;
    }
    setAuditLoading(true);
    try {
      const res = await fetch(
        `${API_BASE}/workspaces/${workspaceId}/audit?limit=50`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!res.ok) {
        throw new Error(`Failed to load audit logs (${res.status})`);
      }
      const data: AuditLog[] = await res.json();
      setAuditLogs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load audit log");
    } finally {
      setAuditLoading(false);
    }
  }, [token, workspaceId]);

  useEffect(() => {
    fetchSnippets();
  }, [fetchSnippets]);

  useEffect(() => {
    fetchAuditLogs();
  }, [fetchAuditLogs]);

  const parseVariables = () => {
    if (!form.variables.trim()) return {} as Record<string, string>;
    try {
      const parsed = JSON.parse(form.variables);
      if (parsed && typeof parsed === "object") {
        return parsed as Record<string, string>;
      }
      throw new Error("Variables must be a JSON object");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Variables must be valid JSON");
      return null;
    }
  };

  const handleCreate = async () => {
    if (!token) {
      setError("Login is required before creating snippets");
      return;
    }
    const vars = parseVariables();
    if (vars === null) return;

    try {
      const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/snippets`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: form.name,
          trigger: form.trigger,
          body: form.body,
          tags: form.tags
            .split(",")
            .map((tag) => tag.trim())
            .filter(Boolean),
          variables: vars,
        }),
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || `Failed to create snippet (${res.status})`);
      }
      setMessage("Snippet created");
      setForm({ name: "", trigger: "", body: "", tags: "", variables: "" });
      await fetchSnippets();
      await fetchAuditLogs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create snippet");
    }
  };

  const handleExport = async () => {
    if (!token) {
      setError("Login is required before exporting");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/export`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new Error(`Export failed (${res.status})`);
      }
      const blob = new Blob([JSON.stringify(await res.json(), null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `workspace-${workspaceId}-snippets.json`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      await fetchAuditLogs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    }
  };

  const formatTimestamp = (value: string) =>
    new Date(value).toLocaleString(undefined, {
      hour12: false,
    });

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #0f172a 0%, #111827 100%)",
        padding: "2.5rem",
        color: "#f8fafc",
      }}
    >
      <div style={{ maxWidth: 960, margin: "0 auto" }}>
        <header
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "1rem",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "2rem",
          }}
        >
          <div>
            <h1 style={{ margin: 0, fontSize: "1.75rem" }}>Macro Library</h1>
            <p style={{ margin: 0, opacity: 0.75 }}>
              Manage workspace snippets, triggers, and exports with full audit history.
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <input
              style={{
                padding: "0.5rem 0.75rem",
                borderRadius: 8,
                border: "1px solid #1f2937",
                backgroundColor: "#e2e8f0",
                color: "#0f172a",
              }}
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <button
              style={{
                padding: "0.5rem 0.75rem",
                borderRadius: 8,
                border: "none",
                backgroundColor: "#facc15",
                color: "#0f172a",
                fontWeight: 600,
              }}
              onClick={handleLogin}
            >
              Dev Login
            </button>
          </div>
        </header>

        {message && (
          <div
            style={{
              backgroundColor: "#065f46",
              padding: "0.75rem 1rem",
              borderRadius: 8,
              marginBottom: "1rem",
            }}
          >
            {message}
          </div>
        )}
        {error && (
          <div
            style={{
              backgroundColor: "#7f1d1d",
              padding: "0.75rem 1rem",
              borderRadius: 8,
              marginBottom: "1rem",
            }}
          >
            {error}
          </div>
        )}

        <section
          style={{
            display: "grid",
            gap: "2rem",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          }}
        >
          <div
            style={{
              backgroundColor: "#1f2937",
              padding: "1.5rem",
              borderRadius: 16,
              border: "1px solid #374151",
            }}
          >
            <h2 style={{ marginTop: 0 }}>Workspace Controls</h2>
            <label style={{ display: "block", marginBottom: "0.75rem" }}>
              Workspace ID
              <input
                type="number"
                min={1}
                value={workspaceId}
                onChange={(e) => setWorkspaceId(Number(e.target.value) || 1)}
                style={{
                  marginTop: "0.25rem",
                  width: "100%",
                  padding: "0.5rem",
                  borderRadius: 8,
                  border: "1px solid #4b5563",
                  backgroundColor: "#111827",
                  color: "#f9fafb",
                }}
              />
            </label>
            <label style={{ display: "block", marginBottom: "0.75rem" }}>
              Search
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="name, trigger, or body"
                style={{
                  marginTop: "0.25rem",
                  width: "100%",
                  padding: "0.5rem",
                  borderRadius: 8,
                  border: "1px solid #4b5563",
                  backgroundColor: "#111827",
                  color: "#f9fafb",
                }}
              />
            </label>
            <button
              onClick={handleExport}
              disabled={!authed}
              style={{
                width: "100%",
                padding: "0.75rem",
                borderRadius: 8,
                border: "none",
                background: authed ? "#2563eb" : "#1e293b",
                color: authed ? "white" : "#64748b",
                fontWeight: 600,
              }}
            >
              Export Snippets JSON
            </button>
          </div>

          <div
            style={{
              backgroundColor: "#1f2937",
              padding: "1.5rem",
              borderRadius: 16,
              border: "1px solid #374151",
            }}
          >
            <h2 style={{ marginTop: 0 }}>Create Snippet</h2>
            <label style={{ display: "block", marginBottom: "0.75rem" }}>
              Name
              <input
                value={form.name}
                onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                style={{
                  marginTop: "0.25rem",
                  width: "100%",
                  padding: "0.5rem",
                  borderRadius: 8,
                  border: "1px solid #4b5563",
                  backgroundColor: "#111827",
                  color: "#f9fafb",
                }}
              />
            </label>
            <label style={{ display: "block", marginBottom: "0.75rem" }}>
              Trigger
              <input
                value={form.trigger}
                onChange={(e) => setForm((prev) => ({ ...prev, trigger: e.target.value }))}
                style={{
                  marginTop: "0.25rem",
                  width: "100%",
                  padding: "0.5rem",
                  borderRadius: 8,
                  border: "1px solid #4b5563",
                  backgroundColor: "#111827",
                  color: "#f9fafb",
                }}
              />
            </label>
            <label style={{ display: "block", marginBottom: "0.75rem" }}>
              Body
              <textarea
                value={form.body}
                onChange={(e) => setForm((prev) => ({ ...prev, body: e.target.value }))}
                rows={6}
                style={{
                  marginTop: "0.25rem",
                  width: "100%",
                  padding: "0.5rem",
                  borderRadius: 8,
                  border: "1px solid #4b5563",
                  backgroundColor: "#111827",
                  color: "#f9fafb",
                }}
              />
            </label>
            <label style={{ display: "block", marginBottom: "0.75rem" }}>
              Tags (comma separated)
              <input
                value={form.tags}
                onChange={(e) => setForm((prev) => ({ ...prev, tags: e.target.value }))}
                style={{
                  marginTop: "0.25rem",
                  width: "100%",
                  padding: "0.5rem",
                  borderRadius: 8,
                  border: "1px solid #4b5563",
                  backgroundColor: "#111827",
                  color: "#f9fafb",
                }}
              />
            </label>
            <label style={{ display: "block", marginBottom: "0.75rem" }}>
              Variables (JSON)
              <textarea
                value={form.variables}
                onChange={(e) => setForm((prev) => ({ ...prev, variables: e.target.value }))}
                rows={3}
                placeholder='{"name": ""}'
                style={{
                  marginTop: "0.25rem",
                  width: "100%",
                  padding: "0.5rem",
                  borderRadius: 8,
                  border: "1px solid #4b5563",
                  backgroundColor: "#111827",
                  color: "#f9fafb",
                }}
              />
            </label>
            <button
              onClick={handleCreate}
              disabled={!authed}
              style={{
                width: "100%",
                padding: "0.75rem",
                borderRadius: 8,
                border: "none",
                background: authed ? "#10b981" : "#1e293b",
                color: authed ? "#052e16" : "#64748b",
                fontWeight: 600,
              }}
            >
              Save Snippet
            </button>
          </div>
        </section>

        <section style={{ marginTop: "3rem" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "1rem",
            }}
          >
            <h2 style={{ margin: 0 }}>Snippets</h2>
            {loading && <span style={{ opacity: 0.7 }}>Loading...</span>}
          </div>
          {snippets.length === 0 && !loading ? (
            <div
              style={{
                padding: "1rem",
                borderRadius: 12,
                backgroundColor: "#1f2937",
                border: "1px solid #374151",
              }}
            >
              No snippets yet. Create one to get started.
            </div>
          ) : (
            <div
              style={{
                display: "grid",
                gap: "1rem",
              }}
            >
              {snippets.map((snippet) => (
                <article
                  key={snippet.id}
                  style={{
                    padding: "1rem",
                    borderRadius: 12,
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                  }}
                >
                  <header
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "baseline",
                      gap: "0.5rem",
                    }}
                  >
                    <h3 style={{ margin: 0 }}>{snippet.name}</h3>
                    <span style={{ fontSize: "0.85rem", opacity: 0.7 }}>
                      {snippet.trigger} * v{snippet.version}
                    </span>
                  </header>
                  <pre
                    style={{
                      whiteSpace: "pre-wrap",
                      fontSize: "0.95rem",
                      marginTop: "0.75rem",
                      backgroundColor: "#111827",
                      padding: "0.75rem",
                      borderRadius: 8,
                      border: "1px solid #1f2937",
                    }}
                  >
                    {snippet.body}
                  </pre>
                  <footer
                    style={{
                      display: "flex",
                      flexWrap: "wrap",
                      gap: "0.5rem",
                      marginTop: "0.75rem",
                      fontSize: "0.85rem",
                      opacity: 0.75,
                    }}
                  >
                    <span>Tags: {snippet.tags.length ? snippet.tags.join(", ") : "-"}</span>
                    <span>Updated: {formatTimestamp(snippet.updated_at)}</span>
                  </footer>
                </article>
              ))}
            </div>
          )}
        </section>

        <section style={{ marginTop: "3rem" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "1rem",
            }}
          >
            <h2 style={{ margin: 0 }}>Recent Audit Log</h2>
            {auditLoading && <span style={{ opacity: 0.7 }}>Refreshing...</span>}
          </div>
          {auditLogs.length === 0 ? (
            <div
              style={{
                padding: "1rem",
                borderRadius: 12,
                backgroundColor: "#1f2937",
                border: "1px solid #374151",
                fontSize: "0.9rem",
                opacity: 0.8,
              }}
            >
              No audit entries yet. Actions you take will appear here.
            </div>
          ) : (
            <div
              style={{
                display: "grid",
                gap: "0.75rem",
              }}
            >
              {auditLogs.map((log) => (
                <div
                  key={log.id}
                  style={{
                    padding: "0.75rem 1rem",
                    borderRadius: 10,
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                    fontSize: "0.9rem",
                  }}
                >
                  <div style={{ fontWeight: 600 }}>{log.action.replace("_", " ")}</div>
                  <div style={{ opacity: 0.75, marginTop: "0.25rem" }}>
                    {formatTimestamp(log.created_at)}
                  </div>
                  {log.meta && Object.keys(log.meta).length > 0 && (
                    <pre
                      style={{
                        backgroundColor: "#111827",
                        border: "1px solid #1f2937",
                        borderRadius: 6,
                        padding: "0.5rem",
                        marginTop: "0.5rem",
                        whiteSpace: "pre-wrap",
                        fontSize: "0.8rem",
                      }}
                    >
                      {JSON.stringify(log.meta, null, 2)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
