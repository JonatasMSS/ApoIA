import { createClient } from "redis";



export const redisClient = createClient({
    socket:{
        host: process.env.REDIS_HOST || "0.0.0.0",
        port: Number(process.env.REDIS_PORT) || 6379
    }
});

redisClient.on("error", function (error: Error) {
  console.error(error);
});



export async function getUserSession(userNumber: string): Promise<string | null> {
    return await redisClient.get(`user_session:${userNumber}`);
}

export async function saveUserSession(userNumber: string, status: string) {
    await redisClient.set(`user_session:${userNumber}`, status);
}

export async function initializeRedis() {
    console.log("🔄 Conectando ao Redis...");
    await redisClient.connect();
    console.log("✅ Conectado ao Redis!");
}