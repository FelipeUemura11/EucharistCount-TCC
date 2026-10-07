import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Em desenvolvimento (npm run dev, :5173), repassa /api para o backend.
  // Assim o frontend usa sempre endereco relativo, como em producao.
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});