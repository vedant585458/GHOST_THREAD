import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Backend origin for the dev proxy. Inside docker compose this is the `api`
// service; on a bare `npm run dev` it is the local uvicorn process.
const API_TARGET = process.env.VITE_API_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    // Dev-only: accept forwarded hosts (containers, remote preview proxies).
    allowedHosts: true,
    // Browsers never talk to the backend directly: everything goes through
    // this relative /api prefix so the app works behind remote previews.
    proxy: {
      "/api": {
        target: API_TARGET,
        changeOrigin: true,
        ws: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  preview: {
    host: "0.0.0.0",
    port: 4173,
  },
});
