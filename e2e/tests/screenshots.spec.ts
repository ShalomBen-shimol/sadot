import { test } from "@playwright/test";
import fs from "fs";
import path from "path";

// Visual-capture "test": drives a real browser (in the Playwright Docker image
// on a host that has one, e.g. aiserver) and writes full-page PNGs to
// e2e/screenshots/. This is how we "see" a page from an environment without a
// browser — run it on the server, then commit/share the PNGs to review + adapt.
//
// Targets: a comma-separated list in E2E_SHOTS as `name|url` pairs, e.g.
//   E2E_SHOTS="orig-adopt|https://sadot.lavit.io/%d7%90%d7%99%d7%9e%d7%95%d7%a5/,new-adopt|https://sadot.lavit.io/crm/adopt"
// Defaults capture the original WordPress adoption page vs. the new CRM catalog.
const DEFAULT_SHOTS = [
  "orig-adopt|https://sadot.lavit.io/%d7%90%d7%99%d7%9e%d7%95%d7%a5/",
  "new-adopt|https://sadot.lavit.io/crm/adopt",
].join(",");

const OUT_DIR = "/e2e/screenshots";

// Desktop + mobile so we can judge responsive layout, not just one width.
const VIEWPORTS = [
  { tag: "desktop", width: 1440, height: 900 },
  { tag: "mobile", width: 390, height: 844 },
];

function parseShots(): { name: string; url: string }[] {
  const raw = process.env.E2E_SHOTS || DEFAULT_SHOTS;
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
    .map((pair) => {
      const idx = pair.indexOf("|");
      const name = pair.slice(0, idx).trim();
      const url = pair.slice(idx + 1).trim();
      return { name, url };
    })
    .filter((s) => s.name && s.url);
}

test.beforeAll(() => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
});

for (const shot of parseShots()) {
  for (const vp of VIEWPORTS) {
    test(`screenshot ${shot.name} @ ${vp.tag}`, async ({ browser }) => {
      const context = await browser.newContext({
        viewport: { width: vp.width, height: vp.height },
        ignoreHTTPSErrors: true,
      });
      const page = await context.newPage();
      await page.goto(shot.url, { waitUntil: "networkidle", timeout: 40_000 });
      // Give lazy images / web fonts a beat to settle before the full-page grab.
      await page.waitForTimeout(1500);
      const file = path.join(OUT_DIR, `${shot.name}-${vp.tag}.png`);
      await page.screenshot({ path: file, fullPage: true });
      await context.close();
    });
  }
}
