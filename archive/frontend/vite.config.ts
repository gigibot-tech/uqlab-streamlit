import path from "node:path";
import { tanstackRouter } from "@tanstack/router-plugin/vite";
import react from "@vitejs/plugin-react-swc";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tanstackRouter({
      target: "react",
      autoCodeSplitting: true,
    }),
  ],
  css: {
    preprocessorOptions: {
      scss: {
        silenceDeprecations: ["mixed-decls"],
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "~@ibm": path.resolve(__dirname, "node_modules/@ibm"),
    },
  },
  build: {
    // Enable cache busting with content hashes in filenames
    rollupOptions: {
      output: {
        entryFileNames: `assets/[name].[hash].js`,
        chunkFileNames: `assets/[name].[hash].js`,
        assetFileNames: `assets/[name].[hash].[ext]`,
      },
    },
  },
});
