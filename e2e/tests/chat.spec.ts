import { test, expect } from "@playwright/test";
import { login, BASE_PATH } from "./helpers";

// Creates a conversation, so gated like the other @write tests.
const WRITES_ENABLED = process.env.E2E_ALLOW_WRITES !== "0";

test.describe("@write chatbot", () => {
  test.skip(!WRITES_ENABLED, "writes disabled (E2E_ALLOW_WRITES=0)");

  test("public chat widget gets a bot reply", async ({ page }) => {
    await page.goto(`${BASE_PATH}/chat`);
    // Welcome bubble is present.
    await expect(page.getByText("פנסיון בשדות").first()).toBeVisible();

    await page.fill("textarea", "היי, אני שוקל למסור את הכלב");
    await page.getByRole("button", { name: "שליחה" }).click();

    // The bot asks for the name (the scripted mock reply).
    await expect(page.getByText("שמך").first()).toBeVisible({ timeout: 15000 });
  });

  test("admin sees the conversation and the bot console loads", async ({ page }) => {
    await login(page);

    await page.goto(`${BASE_PATH}/admin/conversations`);
    await expect(page.getByRole("heading", { name: "שיחות צ'אט" })).toBeVisible();

    await page.goto(`${BASE_PATH}/admin/chatbot`);
    await expect(page.getByRole("heading", { name: "ניהול הבוט" })).toBeVisible();
    // Test sandbox returns a reply without saving.
    await page.fill('input[placeholder="הודעת בדיקה…"]', "שלום");
    await page.getByRole("button", { name: "בדיקה" }).click();
    await expect(page.getByText("שמך").first()).toBeVisible({ timeout: 15000 });
  });
});
