import { Container } from "@cloudflare/containers";

interface Env {
  FIXMYENGLISH: DurableObjectNamespace<FixMyEnglishContainer>;
  DUKE_AI_GATEWAY_KEY: string;
}

export class FixMyEnglishContainer extends Container<Env> {
  defaultPort = 7860;
  sleepAfter = "15m";
  enableInternet = true; // outbound call to the Duke AI Gateway
  envVars = {
    DUKE_AI_GATEWAY_KEY: this.env.DUKE_AI_GATEWAY_KEY,
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
