import { test, expect } from "@playwright/test";
import { login, BASE_PATH, TOKEN_KEY } from "./helpers";

// Read-only: safe to run against the live site.
test("@smoke admin can log in and reach the dashboard", async ({ page }) => {
  await login(page);
});

// Regression for the bug fixed in PR #1: a present-but-invalid token used to
// dead-end on a raw "Could not validate credentials" error with no way back in.
// It must now clear the token and bounce to the login screen.
test("@smoke invalid/expired token redirects to login", async ({ page }) => {
  // Load the app origin first so localStorage is writable for it.
  await page.goto(`${BASE_PATH}/admin/login`);
  await page.evaluate(
    (key) => localStorage.setItem(key, "invalid.token.value"),
    TOKEN_KEY
  );

  // Visiting a protected page with the dead token must redirect to login.
  await page.goto(`${BASE_PATH}/admin`);
  await page.waitForURL("**/admin/login");

  // ...and the dead token must have been cleared by the 401 handler.
  const token = await page.evaluate((key) => localStorage.getItem(key), TOKEN_KEY);
  expect(token).toBeNull();
});
