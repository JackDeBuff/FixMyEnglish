import { Container } from "@cloudflare/containers";

interface Env {
  FIXMYENGLISH: DurableObjectNamespace<FixMyEnglishContainer>;
  DUKE_AI_GATEWAY_KEY: string;
  // Fallback provider, used by the app only when the Duke Gateway fails
  // (vars in wrangler.jsonc, FALLBACK_API_KEY is a secret).
  FALLBACK_BASE_URL?: string;
  FALLBACK_MODEL?: string;
  FALLBACK_EXTRA_BODY?: string;
  FALLBACK_API_KEY?: string;
}

export class FixMyEnglishContainer extends Container<Env> {
  defaultPort = 7860;
  sleepAfter = "15m";
  enableInternet = true; // outbound calls to the LLM providers
  envVars = Object.fromEntries(
    Object.entries({
      DUKE_AI_GATEWAY_KEY: this.env.DUKE_AI_GATEWAY_KEY,
      FALLBACK_BASE_URL: this.env.FALLBACK_BASE_URL,
      FALLBACK_MODEL: this.env.FALLBACK_MODEL,
      FALLBACK_EXTRA_BODY: this.env.FALLBACK_EXTRA_BODY,
      FALLBACK_API_KEY: this.env.FALLBACK_API_KEY,
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
