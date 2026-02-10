import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..");
const docsDir = path.join(repoRoot, "docs");
const indexPath = path.join(docsDir, "index.html");
const notFoundPath = path.join(docsDir, "404.html");
const noJekyllPath = path.join(docsDir, ".nojekyll");

if (!fs.existsSync(docsDir)) {
  console.error("docs/ not found. Run the build first.");
  process.exit(1);
}

if (fs.existsSync(indexPath)) {
  fs.copyFileSync(indexPath, notFoundPath);
} else {
  console.error("index.html not found in docs/. Build may have failed.");
  process.exit(1);
}

fs.writeFileSync(noJekyllPath, "");
console.log("GitHub Pages helper files created.");
