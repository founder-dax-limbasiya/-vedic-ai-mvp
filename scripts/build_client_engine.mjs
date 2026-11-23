import { copyFile, mkdir } from "node:fs/promises";
import { build } from "esbuild";
import { resolve } from "node:path";

const root = process.cwd();
const wasmSource = resolve(root, "node_modules/@swisseph/browser/dist/swisseph.wasm");
const wasmTarget = resolve(root, "web/swisseph.wasm");
const bundleTarget = resolve(root, "web/engine.bundle.js");

await mkdir(resolve(root, "web"), { recursive: true });
await build({
  entryPoints: [resolve(root, "web/engine/index.js")],
  outfile: bundleTarget,
  bundle: true,
  format: "esm",
  platform: "browser",
  target: ["es2022"],
  sourcemap: false,
  legalComments: "eof"
});
await copyFile(wasmSource, wasmTarget);
console.log("Built Jyoti client engine bundle and copied Swiss Ephemeris WASM.");
