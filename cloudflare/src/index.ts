import { Container } from "@cloudflare/containers";

// Required for the container's outbound requests to reach outboundByHost below.
export { ContainerProxy } from "@cloudflare/containers";

interface Env {
  FIXMYENGLISH: DurableObjectNamespace<FixMyEnglishContainer>;
  DUKE_AI_GATEWAY_KEY: string;
  // Fallback provider, used by the app only when the Duke Gateway fails
  // (vars in wrangler.jsonc, FALLBACK_API_KEY is a secret).
  FALLBACK_BASE_URL?: string;
  FALLBACK_MODEL?: string;
  FALLBACK_EXTRA_BODY?: string;
  FALLBACK_API_KEY?: string;
  DAILY_CAP?: string;
}

// The container's own internet access fails (seen 2026-11-24: every provider
// call errored in ~0.2s), but the Worker can reach Workers AI. So the container
// calls this plain-http pseudo-host and the Worker forwards the request to
// FALLBACK_BASE_URL, adding the real key. The key never enters the container.
const FALLBACK_RELAY_HOST = "fallback.relay";

export class FixMyEnglishContainer extends Container<Env> {
  defaultPort = 7860;
  sleepAfter = "15m";
  enableInternet = true; // still lets the app try Duke directly first
  envVars = Object.fromEntries(
    Object.entries({
      DUKE_AI_GATEWAY_KEY: this.env.DUKE_AI_GATEWAY_KEY,
      FALLBACK_BASE_URL: `http://${FALLBACK_RELAY_HOST}`,
      FALLBACK_API_KEY: "injected-by-worker", // non-empty so the app enables the fallback
      FALLBACK_MODEL: this.env.FALLBACK_MODEL,
      FALLBACK_EXTRA_BODY: this.env.FALLBACK_EXTRA_BODY,
      DAILY_CAP: this.env.DAILY_CAP,
    }).filter(([, v]) => v !== undefined),
  ) as Record<string, string>;

  static outboundByHost = {
    [FALLBACK_RELAY_HOST]: async (request: Request, env: Env) => {
      const incoming = new URL(request.url);
      const target = `${env.FALLBACK_BASE_URL}${incoming.pathname}${incoming.search}`;
      const relayed = new Request(target, request);
      relayed.headers.delete("host");
      relayed.headers.set("Authorization", `Bearer ${env.FALLBACK_API_KEY}`);
      return fetch(relayed);
    },
  };
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
