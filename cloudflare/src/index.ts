import { Container } from "@cloudflare/containers";

interface Env {
  FIXMYENGLISH: DurableObjectNamespace<FixMyEnglishContainer>;
  DUKE_AI_GATEWAY_KEY: string;
  // Optional provider override (set in wrangler.jsonc vars + a secret) while the
  // Duke Gateway is unreachable from outside Duke's network. The container app
  // itself is provider-agnostic: it only reads these three env vars.
  GATEWAY_BASE_URL?: string;
  MODEL_NAME?: string;
  LLM_API_KEY?: string;
  LLM_EXTRA_BODY?: string;
}

export class FixMyEnglishContainer extends Container<Env> {
  defaultPort = 7860;
  sleepAfter = "15m";
  enableInternet = true; // outbound call to the LLM provider
  envVars = Object.fromEntries(
    Object.entries({
      DUKE_AI_GATEWAY_KEY: this.env.LLM_API_KEY || this.env.DUKE_AI_GATEWAY_KEY,
      GATEWAY_BASE_URL: this.env.GATEWAY_BASE_URL,
      MODEL_NAME: this.env.MODEL_NAME,
      LLM_EXTRA_BODY: this.env.LLM_EXTRA_BODY,
    }).filter(([, v]) => v !== undefined),
  ) as Record<string, string>;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // one shared instance: the app's in-memory rate limiter stays global
    const container = env.FIXMYENGLISH.getByName("main");
    await container.startAndWaitForPorts();

    // the app rate-limits on x-forwarded-for; give it the real client IP
    const headers = new Headers(request.headers);
    const ip = request.headers.get("CF-Connecting-IP");
    if (ip) headers.set("X-Forwarded-For", ip);

    return container.fetch(new Request(request, { headers }));
  },
};
