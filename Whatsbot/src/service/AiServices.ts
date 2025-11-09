import type { Message } from 'whatsapp-web.js';

interface AudioResponse {
    status: string;
    tipo: 'audio' | 'imagem' | 'imagem_com_audio' | 'exercicio_leitura';
    usuario: string;
    texto_usuario: string;
    resposta_texto: string;
    resposta_audio_base64?: string;
    imagem_base64?: string;
    texto_audio_base64?: string;  // Áudio da IA lendo o texto (exercícios)
    texto_titulo?: string;  // Título do texto de leitura
    is_test_image?: boolean;  // Flag para imagens de teste de alfabetização
    is_reading_exercise?: boolean;  // Flag para exercícios de leitura
}

export async function sendAudioBase64(message: Message, numero: string = "unknown"): Promise<AudioResponse> {
    // Aceita tanto áudio (ptt) quanto texto (chat)
    if (message.type === 'ptt') {
        // Mensagem de áudio - processa com transcrição
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
        console.log('Audio sent:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! status: ${response.status}, statusText: ${response.statusText}, body: ${errorText}`);
        }

        const data: AudioResponse = await response.json();
        return data;
        
    } else if (message.type === 'chat') {
        // Mensagem de texto - envia como texto vazio simulando áudio vazio
        // O backend vai processar apenas o texto
        const response = await fetch('http://localhost:8000/audio/processar_base64', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                audio: "",  // Áudio vazio para mensagem de texto
                numero: numero,
                texto_direto: message.body  // Envia o texto diretamente
            }),
        });
        console.log('Text message sent:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! status: ${response.status}, statusText: ${response.statusText}, body: ${errorText}`);
        }

        const data: AudioResponse = await response.json();
        return data;
    } else {
        throw new Error('Message type not supported. Only audio (ptt) and text (chat) are accepted.');
    }
}
