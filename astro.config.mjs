import { defineConfig } from "astro/config";

// Static output only. Registry and submission services are hosted separately.
export default defineConfig({
  site: "https://spectra.yashaektefaie.com",
  devToolbar: { enabled: false },
});
