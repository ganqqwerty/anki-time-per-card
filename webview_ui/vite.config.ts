import { resolve } from "node:path";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [svelte()],
  build: {
    cssCodeSplit: false,
    emptyOutDir: true,
    lib: {
      entry: resolve(__dirname, "src/main.ts"),
      name: "AnkiTimePerCard",
      formats: ["iife"],
      fileName: () => "time_per_card.js"
    },
    outDir: resolve(__dirname, "../addon/anki_time_per_card/web"),
    rollupOptions: {
      output: {
        assetFileNames: (assetInfo) => {
          if (assetInfo.name?.endsWith(".css")) {
            return "time_per_card.css";
          }
          return "time_per_card-[name][extname]";
        }
      }
    }
  }
});
