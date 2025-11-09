import Fastify from "fastify";
import cors from "@fastify/cors";
import { Client, LocalAuth } from "whatsapp-web.js";
import qrcodeTerminal from "qrcode-terminal";
import buildRoutes from "./routes";

const app = Fastify({
    logger: true
});

// Register CORS plugin to allow cross-origin requests
app.register(cors, {
  // allow request origin to be reflected (allows any origin)
  origin: true,
  // allow credentials if needed
  credentials: true,
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
});

const client = new Client({
  authStrategy: new LocalAuth(),
  puppeteer: { headless: true, args: ["--no-sandbox"] },
});

client.on("qr", qr => qrcodeTerminal.generate(qr, { small: true }));
client.on("ready", () => console.log("✅ Conectado ao WhatsApp!"));
client.on("authenticated", () => console.log("🔐 Autenticado!"));
client.on("auth_failure", msg => console.log("❌ Falha na autenticação:", msg));
client.on("disconnected", reason => console.log("🔌 Desconectado:", reason));

client.on("loading_screen", (percent, message) => console.log(`📱 Carregando: ${percent}% - ${message}`));


client.initialize();
