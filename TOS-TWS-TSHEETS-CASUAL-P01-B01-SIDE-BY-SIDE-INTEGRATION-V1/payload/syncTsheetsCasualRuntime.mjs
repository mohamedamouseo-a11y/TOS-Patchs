import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(here, "..");
const source = resolve(frontendRoot, "../vendor/tsheets-casual-upstream/apps/web/dist");
const destination = resolve(frontendRoot, "dist/tws-casual-runtime");
const required = process.env.TOS_REQUIRE_TSHEETS_CASUAL_RUNTIME === "1";

if (!existsSync(resolve(source, "index.html"))) {
  const message = "TSheets Casual runtime not found at " + source + ". Run P00/P01 runtime build first.";
  if (required) {
    console.error(message);
    process.exit(1);
  }
  console.warn("[tsheets-casual] " + message + " Skipping runtime sync.");
  process.exit(0);
}

rmSync(destination, { recursive: true, force: true });
mkdirSync(destination, { recursive: true });
cpSync(source, destination, { recursive: true });
console.log("[tsheets-casual] runtime synced to " + destination);
