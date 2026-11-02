import { copyFile, mkdir } from "node:fs/promises";

const root = new URL("../", import.meta.url);
await mkdir(new URL("public/", root), { recursive: true });
for (const name of ["protocol.md", "finish.md", "agents.md"]) {
  await copyFile(new URL(`protocol/${name}`, root), new URL(`public/${name}`, root));
}
console.log("Copied protocol, finish review, and agent guide to public/.");
