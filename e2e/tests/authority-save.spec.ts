import { test, expect, Page } from "@playwright/test";
import { login, BASE_PATH } from "./helpers";

// This test mutates data (edits an authority). It is ON by default (CI uses an
// ephemeral DB) and must be explicitly disabled for the live site by setting
// E2E_ALLOW_WRITES=0.
const WRITES_ENABLED = process.env.E2E_ALLOW_WRITES !== "0";

// Filter the authorities table to one authority and return its row.
async function rowFor(page: Page, city: string) {
  const search = page.locator('input[placeholder*="חיפוש"]').first();
  await search.fill(city);
  const row = page.locator("table tbody tr", { hasText: city }).first();
  await expect(row).toBeVisible();
  return row;
}

test.describe("@write authority edits persist", () => {
  test.skip(!WRITES_ENABLED, "writes disabled (E2E_ALLOW_WRITES=0)");

  test("editing an authority email saves and survives a reload", async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_PATH}/admin/authorities`);

    // Pick the first authority in the directory.
    const firstRow = page.locator("table tbody tr").first();
    await expect(firstRow).toBeVisible();
    const city = (await firstRow.locator("td").first().innerText()).trim();

    // Open its edit modal.
    await firstRow.getByText("עריכה").click();
    const modal = page.locator(".fixed.inset-0");
    await expect(modal.getByRole("heading", { name: city })).toBeVisible();

    // Modal inputs are [vet_name, email, phone]; remember the original email so
    // we can restore it (when one existed) and keep the live site clean.
    const emailInput = modal.locator("input").nth(1);
    const originalEmail = (await emailInput.inputValue()).trim();

    const newEmail = `e2e+${Date.now()}@sadot.test`;
    await emailInput.fill(newEmail);
    await modal.getByRole("button", { name: "שמירה" }).click();

    // Modal closes and the list reloads — the table's email column must show it.
    await expect(modal).toBeHidden();
    await expect(await rowFor(page, city)).toContainText(newEmail);

    // Hard reload to prove it persisted to the backend, not just React state.
    await page.reload();
    await expect(await rowFor(page, city)).toContainText(newEmail);

    // Restore the original value when there was one (backend cannot clear a
    // field back to empty, so a blank original is left as the test value).
    if (originalEmail) {
      await (await rowFor(page, city)).getByText("עריכה").click();
      const modal2 = page.locator(".fixed.inset-0");
      await modal2.locator("input").nth(1).fill(originalEmail);
      await modal2.getByRole("button", { name: "שמירה" }).click();
      await expect(modal2).toBeHidden();
    }
  });
});
