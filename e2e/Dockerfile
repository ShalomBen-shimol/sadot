# Official Playwright image ships Chromium/Firefox/WebKit + OS deps, so the
# container can actually drive a real browser. Keep the tag in sync with the
# @playwright/test version in package.json.
FROM mcr.microsoft.com/playwright:v1.48.0-jammy

WORKDIR /e2e
COPY package.json package-lock.json* ./
RUN npm install
COPY . .

# Default: run the whole suite. Override args at `docker run` (e.g. --grep @smoke).
ENTRYPOINT ["npx", "playwright", "test"]
