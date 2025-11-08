import type { FastifyPluginAsync } from "fastify";
import type { Client as WhatsAppClient } from "whatsapp-web.js";
import rootRoutes from "./root";
import sendRoutes from "./send";

/**
 * Factory that returns a Fastify plugin registering all route plugins.
 * The returned plugin will be registered with option { client } so sub-plugins can use it.
 */
export default function buildRoutes(client: WhatsAppClient): FastifyPluginAsync {
  const plugin: FastifyPluginAsync = async (app) => {
    app.register(rootRoutes);
    // cast to any because Fastify's register options type is strict;
    // sendRoutes reads the `client` option at runtime.
    app.register(sendRoutes as any, { client } as any);
  };
  return plugin;
}
