import { Page, expect } from "@playwright/test";

// next.config.js basePath. Every admin route lives under here.
export const BASE_PATH = "/crm";

// Defaults match the backend's seeded first-admin (app/core/config.py). For the
// live site these MUST be overridden with the real credentials via env.
export const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL || "admin@sadot.local";
export const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || "admin1234";

export const TOKEN_KEY = "sadot_token";

// Log in through the real login form and land on the dashboard.
export async function login(page: Page): Promise<void> {
  await page.goto(`${BASE_PATH}/admin/login`);
  await page.fill('input[name="email"]', ADMIN_EMAIL);
  await page.fill('input[name="password"]', ADMIN_PASSWORD);
  await page.click('button[type="submit"]');
  // login() pushes to /admin on success.
  await page.waitForURL("**/admin");
  await expect(page.getByRole("heading", { name: "לוח בקרה" })).toBeVisible();
}
