import { defineConfig } from "astro/config";
import { resolve } from "node:path";

const bundle = process.env.SPECTRA_REGISTRY_BUNDLE;
if (!bundle) {
  throw new Error("Set SPECTRA_REGISTRY_BUNDLE to the folder containing investigations.json and public/.");
}

export default defineConfig({
  site: "https://spectra.yashaektefaie.com",
  srcDir: "./registry-site/src",
  publicDir: resolve(bundle, "public"),
  outDir: "./.registry-build",
  build: { assets: "registry/_assets" },
  devToolbar: { enabled: false },
});
