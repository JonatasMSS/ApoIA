import type { FastifyPluginAsync } from "fastify";
import type { Client as WhatsAppClient } from "whatsapp-web.js";

const sendRoutes: FastifyPluginAsync = async (app, opts) => {
  const client = (opts as any)?.client as WhatsAppClient;

  app.post("/send", async (req: any, reply: any) => {
    const { to, message } = req.body || {};
    if (!to || !message)
      return reply.code(400).send({ error: "Faltam parâmetros" });

    const id = await client.getNumberId(to.replace(/\D/g, ""));
    if (!id) return reply.code(404).send({ error: "Número sem WhatsApp" });

    const sent = await client.sendMessage(id._serialized, message);
    return { ok: true, id: sent.id._serialized };
  });
};

export default sendRoutes;
