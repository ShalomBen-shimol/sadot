import { test, expect } from "@playwright/test";
import { login, BASE_PATH } from "./helpers";

// Writes the email_settings row, so gated like the other @write test.
const WRITES_ENABLED = process.env.E2E_ALLOW_WRITES !== "0";

test.describe("@write email settings", () => {
  test.skip(!WRITES_ENABLED, "writes disabled (E2E_ALLOW_WRITES=0)");

  test("admin can save the Gmail sending account", async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_PATH}/admin/settings`);

    await expect(page.getByRole("heading", { name: "הגדרות דוא״ל" })).toBeVisible();

    await page.fill('input[placeholder="basadot@gmail.com"]', "e2e-bot@gmail.com");
    await page.fill('input[placeholder="פנסיון בשדות"]', "פנסיון בשדות (בדיקה)");
    await page.getByRole("button", { name: "שמירה" }).click();

    // Saved confirmation + the password-state indicator updates from the reload.
    await expect(page.getByText("נשמר")).toBeVisible();

    // Reload proves it persisted: the username is rehydrated from the backend.
    await page.reload();
    await expect(page.locator('input[placeholder="basadot@gmail.com"]')).toHaveValue(
      "e2e-bot@gmail.com"
    );
  });
});
