import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5174,
    strictPort: true,
    allowedHosts: true,
    hmr: {
      clientPort: 5174,
    },
  },
  preview: {
    host: "0.0.0.0",
    port: 5174,
    strictPort: true,
    allowedHosts: true,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          "vendor-react": ["react", "react-dom", "react-router-dom", "zustand"],
          "vendor-tiptap": [
            "@tiptap/react",
            "@tiptap/starter-kit",
            "@tiptap/extension-color",
            "@tiptap/extension-image",
            "@tiptap/extension-subscript",
            "@tiptap/extension-superscript",
            "@tiptap/extension-table",
            "@tiptap/extension-table-cell",
            "@tiptap/extension-table-header",
            "@tiptap/extension-table-row",
            "@tiptap/extension-text-align",
            "@tiptap/extension-text-style",
            "@tiptap/extension-underline",
          ],
        },
      },
    },
  },
});
