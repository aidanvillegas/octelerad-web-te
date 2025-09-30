"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Papa from "papaparse";
import toast from "react-hot-toast";

import { http } from "@/lib/api";
import { getClientId } from "@/lib/client-id";
import { fileStem, timeAgo } from "@/lib/format";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Dropzone } from "@/components/Dropzone";
import ApiStatusBanner from "@/components/ApiStatusBanner";

type DatasetLite = { id: number; name: string; updated_at: string };
type ImportPreview = { columns: string[]; rows: Array<Record<string, unknown>> };

export default function Dashboard() {
  const router = useRouter();
  const clientId = getClientId();

  const [owned, setOwned] = useState<DatasetLite[]>([]);
  const [all, setAll] = useState<DatasetLite[]>([]);
  const [loading, setLoading] = useState(true);

  const [createName, setCreateName] = useState("");
  const [creating, setCreating] = useState(false);

  const [file, setFile] = useState<File | null>(null);
  const [importName, setImportName] = useState("");
  const [importPreview, setImportPreview] = useState<ImportPreview | null>(null);
  const [importing, setImporting] = useState(false);

  const loadLists = useCallback(async () => {
    setLoading(true);
    try {
      const [allResponse, mineResponse] = await Promise.all([
        http.get<{ all: DatasetLite[] }>("/datasets/all"),
        http.get<DatasetLite[]>("/datasets/mine-local", { params: { client_id: clientId } }),
      ]);
      setAll(allResponse.data.all ?? []);
      setOwned(mineResponse.data ?? []);
    } catch (error) {
      console.error("datasets_load_failed", error);
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  useEffect(() => {
    loadLists().catch((error) => console.error("datasets_load_effect_failed", error));
  }, [loadLists]);

  const handleCreate = async () => {
    const name = createName.trim();
    if (!name) {
      toast("Please enter a dataset name.");
      return;
    }

    setCreating(true);
    try {
      const response = await http.post("/datasets", {
        name,
        created_by_client: clientId,
      });
      toast.success("Dataset created");
      router.push(`/datasets/${response.data.id}`);
    } catch (error) {
      console.error("dataset_create_failed", error);
    } finally {
      setCreating(false);
    }
  };

  const parsePreview = async (selected: File) => {
    try {
      if (selected.name.toLowerCase().endsWith(".csv")) {
        const text = await selected.text();
        const parsed = Papa.parse(text, { header: true, skipEmptyLines: "greedy", preview: 5 });
        const rows = (parsed.data as Record<string, unknown>[]).slice(0, 5);
        const columns = parsed.meta.fields ?? Object.keys(rows[0] ?? {});
        setImportPreview({ columns, rows });
      } else if (selected.name.toLowerCase().endsWith(".json")) {
        const text = await selected.text();
        const data = JSON.parse(text);
        const rowsSource = Array.isArray(data) ? data : data.rows ?? data.snippets ?? [];
        const rows = (rowsSource as Record<string, unknown>[]).slice(0, 5);
        const columns = Object.keys(rows[0] ?? {});
        setImportPreview({ columns, rows });
      } else {
        setImportPreview(null);
      }
    } catch (error) {
      console.error("import_preview_failed", error);
      setImportPreview(null);
    }
  };

  const handleFile = async (selected: File) => {
    setFile(selected);
    setImportName(fileStem(selected.name));
    await parsePreview(selected);
  };

  const clearImport = () => {
    setFile(null);
    setImportName("");
    setImportPreview(null);
  };

  const handleImport = async () => {
    if (!file) {
      toast("Choose a CSV or JSON file.");
      return;
    }

    const name = importName.trim() || fileStem(file.name);
    setImporting(true);
    try {
      const created = await http.post("/datasets", {
        name,
        created_by_client: clientId,
      });
      const datasetId = created.data.id;

      const form = new FormData();
      form.append("file", file);
      await http.post(`/datasets/${datasetId}/import`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      toast.success("Dataset imported");
      router.push(`/datasets/${datasetId}`);
    } catch (error) {
      console.error("dataset_import_failed", error);
    } finally {
      setImporting(false);
    }
  };

  const renderList = (items: DatasetLite[]) => (
    <ul className="space-y-2">
      {items.map((dataset) => (
        <li
          key={dataset.id}
          className="flex items-center justify-between rounded border border-neutral-800 p-3"
        >
          <div>
            <div className="font-medium">{dataset.name}</div>
            <div className="text-xs opacity-70">Updated {timeAgo(dataset.updated_at)}</div>
          </div>
          <div className="flex gap-2">
            <a className="rounded bg-neutral-800 px-3 py-1 hover:bg-neutral-700" href={`/datasets/${dataset.id}`}>
              Open
            </a>
            <button
              className="rounded border border-neutral-700 px-3 py-1 text-sm hover:bg-neutral-800"
              onClick={() => {
                const url = `${window.location.origin}/datasets/${dataset.id}`;
                navigator.clipboard
                  .writeText(url)
                  .then(() => toast("Link copied"))
                  .catch(() => toast.error("Copy failed"));
              }}
            >
              Copy link
            </button>
          </div>
        </li>
      ))}
    </ul>
  );

  return (
    <main className="min-h-screen bg-neutral-950 p-6 text-neutral-100">
      <div className="mx-auto flex max-w-6xl flex-col gap-8">
        <ApiStatusBanner />
        <header className="space-y-2">
          <h1 className="text-3xl font-semibold">Datasets
          </h1>
          <p className="text-sm opacity-80">
            Public collaborative tables. Changes are visible to everyone instantly.
          </p>
        </header>

        <section className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <Card>
            <CardHeader
              title="Create new dataset"
              subtitle="Blank table with default columns. You can add more later."
            />
            <div className="space-y-3">
              <Input
                placeholder="e.g., Radiology Macros"
                value={createName}
                onChange={(event) => setCreateName(event.target.value)}
                aria-label="Dataset name"
              />
              <Button variant="primary" onClick={handleCreate} loading={creating}>
                Create
              </Button>
            </div>
          </Card>

          <Card>
            <CardHeader
              title="Import dataset"
              subtitle="CSV or JSON. We'll create a new dataset from your file."
            />
            <div className="space-y-3">
              <Dropzone onFile={handleFile} />
              {file && (
                <div className="space-y-3">
                  <div className="text-sm">
                    Selected: <span className="opacity-80">{file.name}</span>
                  </div>
                  <Input
                    label="Dataset name"
                    placeholder="Dataset name"
                    value={importName}
                    onChange={(event) => setImportName(event.target.value)}
                  />
                  {importPreview && (
                    <div className="rounded-md border border-neutral-800 p-2 text-xs">
                      <div className="opacity-80">
                        Columns ({importPreview.columns.length}): {importPreview.columns.join(", ")}
                      </div>
                      <div className="opacity-70">
                        Preview rows: {importPreview.rows.length > 0 ? importPreview.rows.length : 0}
                      </div>
                    </div>
                  )}
                  <div className="flex gap-2">
                    <Button variant="secondary" onClick={clearImport}>
                      Clear
                    </Button>
                    <Button
                      variant="primary"
                      onClick={handleImport}
                      loading={importing}
                      disabled={!file}
                    >
                      Import
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </section>

        <section className="grid gap-6 md:grid-cols-2">
          <div>
            <h2 className="text-xl font-semibold">My Datasets</h2>
            <div className="mt-3 text-sm">
              {loading ? (
                <p className="opacity-70">Loading...</p>
              ) : owned.length === 0 ? (
                <p className="opacity-70">Nothing yet. Create or import to see datasets here.</p>
              ) : (
                renderList(owned)
              )}
            </div>
          </div>
          <div>
            <h2 className="text-xl font-semibold">All datasets</h2>
            <div className="mt-3 text-sm">
              {loading ? (
                <p className="opacity-70">Loading...</p>
              ) : all.length === 0 ? (
                <p className="opacity-70">No datasets available yet.</p>
              ) : (
                renderList(all)
              )}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
