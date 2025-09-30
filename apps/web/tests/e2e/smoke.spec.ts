import { expect, test } from "@playwright/test";

type DatasetRow = Record<string, unknown> & { id: number };

test("public dataset flow with realtime broadcast", async ({ page }) => {
  const datasetId = 101;
  const dataset = {
    id: datasetId,
    name: "Playwright Dataset",
    schema: { columns: [{ key: "Column A" }] },
    updated_at: new Date().toISOString(),
  };
  const rows: DatasetRow[] = [];

  await page.addInitScript(() => {
    const sockets: Array<{ onmessage: ((event: MessageEvent) => void) | null; close: () => void; readyState: number }> = [];

    class MockWebSocket {
      url: string;
      readyState = 1;
      onmessage: ((event: MessageEvent) => void) | null = null;
      onopen: ((event: Event) => void) | null = null;
      onclose: ((event: Event) => void) | null = null;

      constructor(url: string) {
        this.url = url;
        sockets.push(this);
        setTimeout(() => this.onopen?.(new Event("open")), 0);
      }

      send(): void {
        // no-op for tests
      }

      close(): void {
        this.readyState = 3;
        this.onclose?.(new Event("close"));
      }

      addEventListener(type: string, handler: (event: MessageEvent) => void): void {
        if (type === "message") {
          this.onmessage = handler;
        }
      }

      removeEventListener(): void {
        // no-op
      }
    }

    const emitMessage = (message: unknown) => {
      sockets.slice().forEach((socket) => {
        socket.onmessage?.({ data: JSON.stringify(message) } as MessageEvent);
      });
    };

    (window as any).__mockSockets = sockets;
    (window as any).WebSocket = MockWebSocket as any;
    (window as any).__emitDatasetMessage = emitMessage;

    const originalFetch = window.fetch.bind(window);
    window.fetch = async (...args: Parameters<typeof fetch>) => {
      const response = await originalFetch(...args);
      try {
        const [resource, init] = args;
        const url = typeof resource === "string" ? resource : resource.url;
        if (url.includes("/rows/patch") && init?.body && typeof init.body === "string") {
          const payload = JSON.parse(init.body);
          emitMessage({
            type: "cell",
            row_id: payload.id,
            key: payload.key,
            value: payload.value,
          });
        }
      } catch (error) {
        console.error("mock fetch broadcast failed", error);
      }
      return response;
    };
  });

  await page.route("**/datasets/all", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ all: [] }),
    });
  });

  await page.route("**/datasets/mine-local", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
  });

  await page.route(`**/datasets/${datasetId}`, async (route) => {
    if (route.request().resourceType() === "document") {
      return route.continue();
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(dataset),
    });
  });

  await page.route(`**/datasets/${datasetId}/rows`, async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ total: rows.length, rows }),
      });
      return;
    }
    return route.continue();
  });

  await page.route("**/datasets", async (route) => {
    if (route.request().method() === "POST" && route.request().url().endsWith("/datasets")) {
      dataset.updated_at = new Date().toISOString();
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(dataset),
      });
      return;
    }
    return route.continue();
  });

  await page.route(`**/datasets/${datasetId}/rows/upsert`, async (route) => {
    const payload = JSON.parse(route.request().postData() || "{}");
    const incoming: DatasetRow[] = Array.isArray(payload.rows) ? payload.rows : [];
    incoming.forEach((row) => {
      const nextId = rows.length + 1;
      rows.push({ ...row, id: nextId });
    });
    dataset.updated_at = new Date().toISOString();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ created: incoming.length }),
    });
  });

  await page.route(`**/datasets/${datasetId}/rows/patch`, async (route) => {
    const payload = JSON.parse(route.request().postData() || "{}");
    const target = rows.find((row) => row.id === payload.id);
    if (target) {
      target[payload.key as keyof DatasetRow] = payload.value;
    }
    dataset.updated_at = new Date().toISOString();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true, applied: payload }),
    });
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Datasets", level: 1 })).toBeVisible();

  await page.locator('input').first().fill(dataset.name);
  await page.getByRole("button", { name: "Create", exact: true }).click();
  await expect(page).toHaveURL(new RegExp("/datasets/" + datasetId + "$"));

  await expect(page.getByRole("heading", { name: dataset.name })).toBeVisible();

  await page.getByRole("button", { name: "Add Row" }).click();
  await expect(page.locator(".ag-center-cols-container .ag-row")).toHaveCount(1);

  const firstCell = page.locator(".ag-center-cols-container .ag-cell").first();
  await firstCell.dblclick();
  await page.keyboard.type("Updated value");
  await page.keyboard.press("Enter");

  await expect(firstCell).toHaveText("Updated value");
});
