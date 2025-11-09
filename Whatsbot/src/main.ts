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
    console.log(`Mensagem de ${message.from}: ${message.body}`);
    console.log(`Mensagem tem mídia: ${message.hasMedia} e tipo: ${message.type}`);
    
    // Verifica se não é mensagem própria, não é grupo e é do número permitido
    if(!message.fromMe && !chat.isGroup && message.from.split("@")[0] == "558388083711") {
        // Aceita mensagens de áudio (ptt) ou texto
        if ((message.hasMedia && message.type === 'ptt') || message.type === 'chat') {
          console.log(`📩 Mensagem recebida de ${message.from}`);
          await chat.sendMessage("⏳ Aguarde um momento, estou processando...");
          
          const data = await sendAudioBase64(message, message.from);
          
          // Verifica o tipo de resposta
          if (data.tipo === 'imagem_com_audio') {
            console.log('🎨🔊 Enviando imagem de teste + áudio explicativo');
            
            // 1) Envia o áudio explicativo primeiro
            const audioBase64 = data.resposta_audio_base64!.split(',')[1];
            const audioMedia = new MessageMedia('audio/wav', audioBase64);
            await chat.sendMessage(audioMedia);
            
            // 2) Envia a imagem com legenda
            const imageBase64 = data.imagem_base64!.split(',')[1];
            const imageMedia = new MessageMedia('image/png', imageBase64);
            await chat.sendMessage(imageMedia, { 
              caption: "👆 Olhe bem as palavras da imagem acima. Depois me diga ou escreva quais palavras você consegue ler! 😊" 
            });
            
          } else if (data.tipo === 'imagem') {
            console.log('🎨 Enviando apenas imagem');
            // Envia apenas a imagem
            const imageBase64 = data.imagem_base64!.split(',')[1];
            const imageMedia = new MessageMedia('image/png', imageBase64);
            await chat.sendMessage(imageMedia, { caption: data.resposta_texto });
            
          } else {
            console.log('🔊 Enviando apenas áudio');
            // Envia apenas o áudio
            const audioBase64 = data.resposta_audio_base64!.split(',')[1];
            const audioMedia = new MessageMedia('audio/wav', audioBase64);
            await chat.sendMessage(audioMedia);
          }
        }
    }
});

client.initialize();
