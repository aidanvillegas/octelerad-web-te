"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { AgGridReact } from "ag-grid-react";
import type { AgGridReact as AgGridReactType } from "ag-grid-react";
import type { ColDef } from "ag-grid-community";

import { http } from "@/lib/api";
import { useWs } from "@/hooks/useWs";

import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-quartz.css";

type Schema = {
  columns: { key: string; type?: string }[];
};

type DatasetRow = Record<string, unknown> & { id: number };

type SocketMessage =
  | { type: "cell"; row_id: number; key: string; value: unknown }
  | { type: "rows_upsert"; rows: DatasetRow[] }
  | { type: "column_add"; key: string }
  | { type: "delete_rows"; ids: number[] };

export default function DatasetPage() {
  const params = useParams<{ id: string }>();
  const datasetId = Number(params.id);
  const gridRef = useRef<AgGridReactType<DatasetRow>>(null);

  const [schema, setSchema] = useState<Schema | null>(null);
  const [datasetName, setDatasetName] = useState("");
  const [rows, setRows] = useState<DatasetRow[]>([]);
  const [query, setQuery] = useState("");
  const [saving, setSaving] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const { socket, connected } = useWs("/ws/datasets/" + datasetId);

  const columnDefs = useMemo<ColDef[]>(
    () =>
      (schema?.columns ?? []).map((column) => ({
        field: column.key,
        headerName: column.key,
        sortable: true,
        filter: true,
        editable: true,
        resizable: true,
      })),
    [schema]
  );

  const fetchRows = useCallback(
    async (search: string) => {
      if (!datasetId) return;
      const response = await http.get(`/datasets/${datasetId}/rows`, {
        params: { q: search || undefined },
      });
      setRows(response.data.rows ?? []);
    },
    [datasetId]
  );

  useEffect(() => {
    if (!datasetId) return;
    http
      .get(`/datasets/${datasetId}`)
      .then((response) => {
        setSchema(response.data.schema as Schema);
        setDatasetName(response.data.name as string);
      })
      .catch(console.error);
  }, [datasetId]);

  useEffect(() => {
    fetchRows(query).catch(console.error);
  }, [fetchRows, query]);

  useEffect(() => {
    if (!socket) return;

    const handleMessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data) as SocketMessage;
        if (message.type === "cell") {
          setRows((prev) =>
            prev.map((row) =>
              row.id === message.row_id ? { ...row, [message.key]: message.value } : row
            )
          );
        } else if (message.type === "rows_upsert") {
          setRows((prev) => {
            const map = new Map(prev.map((row) => [row.id, row]));
            message.rows.forEach((row) => {
              const existing = map.get(row.id);
              map.set(row.id, { ...(existing ?? {}), ...row });
            });
            return Array.from(map.values());
          });
        } else if (message.type === "column_add") {
          setSchema((prev) =>
            prev ? { columns: [...prev.columns, { key: message.key }] } : prev
          );
        } else if (message.type === "delete_rows") {
          setRows((prev) => prev.filter((row) => !message.ids.includes(row.id)));
        }
      } catch (error) {
        console.error("failed to process websocket message", error);
      }
    };

    socket.addEventListener("message", handleMessage);
    return () => {
      socket.removeEventListener("message", handleMessage);
    };
  }, [socket]);

  const onCellValueChanged = async (event: any) => {
    const rowId = event.data?.id;
    const key = event.colDef?.field;
    if (!rowId || !key) return;
    setSaving(true);
    try {
      await http.post(`/datasets/${datasetId}/rows/patch`, {
        id: rowId,
        key,
        value: event.newValue,
      });
    } finally {
      setSaving(false);
    }
  };

  const addRow = async () => {
    if (!schema) return;
    const payload: Record<string, unknown> = {};
    schema.columns.forEach((column) => {
      payload[column.key] = "";
    });
    await http.post(`/datasets/${datasetId}/rows/upsert`, { rows: [payload] });
    await fetchRows(query);
  };

  const addColumn = async () => {
    const key = prompt("New column name");
    if (!key?.trim()) return;
    await http.post(`/datasets/${datasetId}/columns/add`, { key: key.trim() });
    setSchema((prev) =>
      prev ? { columns: [...prev.columns, { key: key.trim() }] } : prev
    );
  };

  const deleteRows = async () => {
    if (selectedIds.length === 0) return;
    const params = new URLSearchParams();
    selectedIds.forEach((id) => params.append("ids", String(id)));
    await http.delete(`/datasets/${datasetId}/rows?${params.toString()}`);
    setRows((prev) => prev.filter((row) => !selectedIds.includes(row.id)));
    setSelectedIds([]);
  };

  const exportDataset = async (format: "json" | "csv") => {
    const response = await http.get(`/datasets/${datasetId}/export`, {
      params: { fmt: format },
    });
    const { filename, content } = response.data;
    const blob = new Blob(
      [format === "json" ? JSON.stringify(content, null, 2) : content],
      { type: format === "json" ? "application/json" : "text/csv" }
    );
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename ?? `dataset.${format}`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const onSelectionChanged = () => {
    const api = gridRef.current?.api;
    if (!api) return;
    const selected = api.getSelectedRows() as DatasetRow[];
    setSelectedIds(selected.map((row) => row.id));
  };

  return (
    <main className="min-h-screen bg-neutral-950 p-6 text-neutral-100">
      <div className="mx-auto flex max-w-[1400px] flex-col gap-4">
        <header className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-semibold">
                {datasetName || `Dataset ${datasetId}`}
              </h1>
              <span className="text-sm opacity-60">
                {saving ? "Saving…" : "All changes saved"}
              </span>
              <span className="text-xs opacity-70">{connected ? "Live" : "Reconnecting…"}</span>
            </div>
            <input
              className="max-w-sm rounded bg-neutral-100 px-3 py-2 text-neutral-900"
              placeholder="Search…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button className="rounded bg-neutral-800 px-3 py-2" onClick={addRow}>
              Add Row
            </button>
            <button className="rounded bg-neutral-800 px-3 py-2" onClick={addColumn}>
              Add Column
            </button>
            <button
              className="rounded bg-neutral-800 px-3 py-2 disabled:opacity-50"
              onClick={deleteRows}
              disabled={selectedIds.length === 0}
            >
              Delete Rows
            </button>
            <button className="rounded bg-neutral-800 px-3 py-2" onClick={() => exportDataset("json")}>
              Export JSON
            </button>
            <button className="rounded bg-neutral-800 px-3 py-2" onClick={() => exportDataset("csv")}>
              Export CSV
            </button>
          </div>
        </header>

        <div className="ag-theme-quartz" style={{ height: "70vh", width: "100%" }}>
          <AgGridReact
            ref={gridRef}
            rowData={rows}
            columnDefs={columnDefs}
            defaultColDef={{ editable: true, resizable: true }}
            pagination={false}
            suppressRowClickSelection
            rowSelection="multiple"
            enableCellTextSelection
            onSelectionChanged={onSelectionChanged}
            onCellValueChanged={onCellValueChanged}
            getRowId={(params) => String(params.data.id)}
          />
        </div>
      </div>
    </main>
  );
}
