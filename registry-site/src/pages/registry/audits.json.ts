import type { APIRoute } from "astro";
import {
  investigations,
  models,
  auditURL,
  figureURL,
} from "../../lib/paper-registry";
export const GET: APIRoute = () =>
  new Response(
    JSON.stringify(
      {
        schemaVersion: 1,
        collection: "AutoSPECTRA manuscript investigations",
        models: models.map((m) => ({
          name: m.name,
          figure: m.figure,
          main: figureURL(m.name, "main"),
          supplementary: figureURL(m.name, "expanded"),
        })),
        investigations: investigations.map((a) => ({ ...a, url: auditURL(a) })),
      },
      null,
      2,
    ) + "\n",
    { headers: { "Content-Type": "application/json" } },
  );
