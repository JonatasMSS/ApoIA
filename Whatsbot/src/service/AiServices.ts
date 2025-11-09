import type { Message } from 'whatsapp-web.js';
export async function sendAudioBase64(message: Message, numero: string = "unknown"): Promise<any> {
    if (message.type !== 'ptt') {
        throw new Error('Message is not an audio');
    }

    const media = await message.downloadMedia();
    const audioBase64 = media.data;

    const response = await fetch('http://localhost:8000/audio/processar_base64', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            audio: audioBase64,
            numero: numero
        }),
    });
    console.log('Media sent:', response.status);

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, statusText: ${response.statusText}, body: ${errorText}`);
    }

    const data = await response.json();
    return data.resposta_audio_base64.split(',')[1];
}
