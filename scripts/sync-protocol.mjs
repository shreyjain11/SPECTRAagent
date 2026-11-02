import { copyFile, mkdir } from "node:fs/promises";

const root = new URL("../", import.meta.url);
await mkdir(new URL("public/", root), { recursive: true });
for (const name of ["protocol.md", "finish.md", "agents.md", "prompt.md", "submit.md"]) {
  await copyFile(new URL(`protocol/${name}`, root), new URL(`public/${name}`, root));
}
console.log("Copied all five canonical guides to public/.");
