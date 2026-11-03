import type { APIRoute } from "astro";
import { investigations } from "../../../lib/paper-registry";
export function getStaticPaths() {
  return investigations.map((a) => ({
    params: { model: a.model.toLowerCase(), audit: a.id },
    props: { a },
  }));
}
export const GET: APIRoute = ({ props }) =>
  new Response(JSON.stringify(props.a, null, 2) + "\n", {
    headers: { "Content-Type": "application/json" },
  });
