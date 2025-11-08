import type { FastifyPluginAsync } from "fastify";

const rootRoutes: FastifyPluginAsync = async (app) => {
  app.get("/", async () => {
    return { Ok: true, message: "WhatsBot API está funcionando!" };
  });
};

export default rootRoutes;
