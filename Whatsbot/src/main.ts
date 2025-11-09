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

// Robust error handling for Windows file-locks during LocalAuth logout
process.on('uncaughtException', (err: any) => {
  const msg = String(err?.message || err);
  // Ignore EBUSY unlink errors on Chromium cookie journal during logout (Windows-specific)
  if (msg.includes('EBUSY') && msg.includes('Cookies-journal')) {
    console.warn('⚠️ Ignorando erro EBUSY em Cookies-journal durante logout (Windows).');
    return;
  }
  throw err;
});

process.on('unhandledRejection', (reason: any) => {
  const msg = String((reason as any)?.message || reason);
  if (msg.includes('EBUSY') && msg.includes('Cookies-journal')) {
    console.warn('⚠️ Ignorando rejeição EBUSY em Cookies-journal durante logout (Windows).');
    return;
  }
  console.error('Unhandled rejection:', reason);
});

const client = new Client({
  // Increase rmMaxRetries to mitigate transient file locks on Windows
  authStrategy: new LocalAuth({ rmMaxRetries: 10 }),
  puppeteer: { headless: true, args: ["--no-sandbox"] },
});

client.on("qr", (qr: string) => qrcodeTerminal.generate(qr, { small: true }));
client.on("ready", () => console.log("✅ Conectado ao WhatsApp!"));
client.on("authenticated", () => console.log("🔐 Autenticado!"));
client.on("auth_failure", (msg: string) => console.log("❌ Falha na autenticação:", msg));
client.on("disconnected", async (reason: string) => {
  console.log("🔌Desconectado:", reason);
  // Pequeno atraso para permitir que o Chromium libere locks de arquivo em Windows
  if (reason === 'LOGOUT') {
    await new Promise((r) => setTimeout(r, 500));
  }
});

client.on("loading_screen", (percent: number, message: string) => console.log(`📱 Carregando: ${percent}% - ${message}`));

client.on("message", async (message: Message) => {
    const chat = await message.getChat();
    console.log(`Mensagem de ${message.from}: ${message.body}`);
    console.log(`Mensagem tem mídia: ${message.hasMedia} e tipo: ${message.type}`);
    
    // Verifica se não é mensagem própria, não é grupo e é do número permitido
    if(!message.fromMe && !chat.isGroup && message.from.split("@")[0] == "558388083711") {
        // Aceita mensagens de áudio (ptt) ou texto
        if ((message.hasMedia && message.type === 'ptt') || message.type === 'chat') {
          console.log(`📩 Mensagem recebida de ${message.from}`);
          // Mensagem de espera minimalista (sem texto longo)
          await chat.sendMessage("⏳ Espera...");
          
          const data = await sendAudioBase64(message, message.from);
          
          // Verifica o tipo de resposta
          if (data.tipo === 'exercicio_leitura') {
            console.log('📖 Enviando exercício de leitura');
            
            // 1) Envia o áudio explicativo
            const audioExplicacao = data.resposta_audio_base64!.split(',')[1];
            const audioExplicacaoMedia = new MessageMedia('audio/wav', audioExplicacao);
            await chat.sendMessage(audioExplicacaoMedia);
            
            // 2) Envia a imagem com o texto (sem legenda/caption)
            const imageBase64 = data.imagem_base64!.split(',')[1];
            const imageMedia = new MessageMedia('image/png', imageBase64);
            await chat.sendMessage(imageMedia);
            
            // 3) Envia o áudio da IA lendo o texto
            const audioTexto = (data as any).texto_audio_base64!.split(',')[1];
            const audioTextoMedia = new MessageMedia('audio/wav', audioTexto);
            await chat.sendMessage(audioTextoMedia);
            
            // 4) Instrução final simplificada (sem frase longa)
            await chat.sendMessage("🎤 Ler e mandar áudio.");
            
          } else if (data.tipo === 'imagem_com_audio') {
            console.log('🎨🔊 Enviando imagem de teste + áudio explicativo');
            
            // 1) Envia o áudio explicativo primeiro
            const audioBase64 = data.resposta_audio_base64!.split(',')[1];
            const audioMedia = new MessageMedia('audio/wav', audioBase64);
            await chat.sendMessage(audioMedia);
            
            // 2) Envia a imagem sem legenda
            const imageBase64 = data.imagem_base64!.split(',')[1];
            const imageMedia = new MessageMedia('image/png', imageBase64);
            await chat.sendMessage(imageMedia);
            
          } else if (data.tipo === 'imagem') {
            console.log('🎨 Enviando apenas imagem');
            // Envia apenas a imagem
            const imageBase64 = data.imagem_base64!.split(',')[1];
            const imageMedia = new MessageMedia('image/png', imageBase64);
            await chat.sendMessage(imageMedia);
            
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
