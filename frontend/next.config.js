/** @type {import('next').NextConfig} */
// Mounted behind nginx at /crm (https://sadot.lavit.io/crm). basePath prefixes
// every route and asset URL so the app works under that sub-path. Keep in sync
// with deploy/nginx-sadot.conf and the backend FRONTEND_BASE_PATH setting.
const nextConfig = {
  basePath: "/crm",
  reactStrictMode: true,
  output: "standalone",
  images: {
    remotePatterns: [{ protocol: "https", hostname: "**" }],
  },
};

module.exports = nextConfig;
