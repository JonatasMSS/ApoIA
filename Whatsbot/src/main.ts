import Fastify from "fastify";
import cors from "@fastify/cors";
import { Client, LocalAuth, type Message } from "whatsapp-web.js";
import qrcodeTerminal from "qrcode-terminal";
import { initializeRedis } from "./lib/redis";
import fs from 'fs';
import { sendAudioBase64 } from "./service/AiServices";
import { MessageMedia } from "whatsapp-web.js";




// const app = Fastify({
//     logger: true
// });

// // Register CORS plugin to allow cross-origin requests
// app.register(cors, {
//   // allow request origin to be reflected (allows any origin)
//   origin: true,
//   // allow credentials if needed
//   credentials: true,
//   methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
// });

const client = new Client({
  authStrategy: new LocalAuth(),
  puppeteer: { headless: true, args: ["--no-sandbox"] },
});

client.on("qr", qr => qrcodeTerminal.generate(qr, { small: true }));
client.on("ready", () => console.log("✅ Conectado ao WhatsApp!"));
client.on("authenticated", () => console.log("🔐 Autenticado!"));
client.on("auth_failure", msg => console.log("❌ Falha na autenticação:", msg));
client.on("disconnected", reason => console.log("🔌Desconectado:", reason));

client.on("loading_screen", (percent, message) => console.log(`📱 Carregando: ${percent}% - ${message}`));

client.on("message", async (message: Message) => {
    const chat = await message.getChat();
    console.log(`Mensage de ${message.from}: ${message.body}`);
    console.log(`Mensage tem midia: ${message.hasMedia} e tipo: ${message.type}`);
    if(!message.fromMe && !chat.isGroup && message.from.split("@")[0] == "558388083711") {
        if (message.hasMedia && message.type === 'ptt') {
          console.log(`📩 Mensagem de áudio recebida de ${message.from}`);
          await chat.sendMessage("Aguarde um pouco, processando seu áudio...");
          const data = await sendAudioBase64(message, message.from)
          const media = new MessageMedia('audio/wav', data);
          await chat.sendMessage(media);
          
            
        }
    }
});

client.initialize();
