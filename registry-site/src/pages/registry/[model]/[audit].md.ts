import type { APIRoute } from "astro";
import { investigations, auditMarkdown } from "../../../lib/paper-registry";
export function getStaticPaths() {
  return investigations.map((a) => ({
    params: { model: a.model.toLowerCase(), audit: a.id },
    props: { a },
  }));
}
export const GET: APIRoute = ({ props }) =>
  new Response(auditMarkdown(props.a), {
    headers: { "Content-Type": "text/markdown; charset=utf-8" },
  });
