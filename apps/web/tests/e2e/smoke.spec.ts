import { expect, test } from "@playwright/test";

test("login and create snippet flow", async ({ page }) => {
  const snippets: any[] = [];
  const auditLogs: any[] = [];

  const addAudit = (action: string, meta: Record<string, unknown> = {}) => {
    auditLogs.unshift({
      id: auditLogs.length + 1,
      workspace_id: 1,
      user_id: 1,
      action,
      meta,
      created_at: new Date().toISOString(),
    });
  };

  await page.route("**/auth/magic", async (route) => {
    if (route.request().method() !== "POST") {
      return route.continue();
    }
    addAudit("login", { email: "e2e@example.com" });
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ access_token: "fake-token" }),
    });
  });

  await page.route("**/workspaces/1/snippets*", async (route) => {
    const request = route.request();
    if (request.method() === "GET") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(snippets),
      });
    }
    if (request.method() === "POST") {
      const body = JSON.parse(request.postData() || "{}");
      const snippet = {
        id: snippets.length + 1,
        ...body,
        version: 1,
        updated_at: new Date().toISOString(),
      };
      snippets.length = 0;
      snippets.push(snippet);
      addAudit("create_snippet", { snippet_id: snippet.id });
      return route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify(snippet),
      });
    }
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
  });

  await page.route("**/workspaces/1/export", async (route) => {
    addAudit("export", { count: snippets.length });
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        schema: "text-expander.v1",
        workspace_id: 1,
        snippets,
      }),
    });
  });

  await page.route("**/workspaces/1/audit*", async (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(auditLogs.slice(0, 10)),
    })
  );

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Macro Library" })).toBeVisible();

  const emailInput = page.getByPlaceholder("you@example.com");
  await emailInput.fill("e2e@example.com");
  await page.getByRole("button", { name: "Dev Login" }).click();
  await expect(
    page.locator("text=Authenticated. Token stored in memory only.")
  ).toBeVisible();

  await page.getByLabel("Name").fill("Playwright Test Snippet");
  await page.getByLabel("Trigger").fill("ptest");
  await page.getByLabel("Body").fill("Testing body");
  await page.getByLabel("Tags (comma separated)").fill("test");
  await page.getByLabel("Variables (JSON)").fill('{"name": ""}');
  await page.getByRole("button", { name: "Save Snippet" }).click();

  await expect(page.locator("text=Snippet created")).toBeVisible();
  await expect(
    page.locator("article", { hasText: "Playwright Test Snippet" })
  ).toBeVisible();
  await expect(
    page
      .locator("section")
      .filter({ hasText: "Recent Audit Log" })
      .locator("div")
      .filter({ hasText: "create snippet" })
      .first()
  ).toBeVisible();
});
