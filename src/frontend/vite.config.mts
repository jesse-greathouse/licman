import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import fs from "fs";
import pathMod from "path";

function excludeDotGitkeepPlugin() {
  return {
    name: "exclude-dot-gitkeep",
    closeBundle() {
      const outDir = pathMod.resolve(__dirname, "../../var/www/html");
      const gitkeepPath = pathMod.join(outDir, ".gitkeep");
      if (fs.existsSync(gitkeepPath)) {
        fs.unlinkSync(gitkeepPath);
        console.log("🧹 Removed .gitkeep from build output.");
      }
    },
  };
}

export default defineConfig({
  root: __dirname,
  plugins: [
    react(),
    excludeDotGitkeepPlugin(),
  ],
  publicDir: path.resolve(__dirname, "public"),
  build: {
    outDir: path.resolve(__dirname, "../../var/www/html"),
    emptyOutDir: true,
  },
});
