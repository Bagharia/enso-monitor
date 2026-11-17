import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom", // simule un navigateur pour les tests
    setupFiles: ["./src/test/setup.ts"],
  },
});
