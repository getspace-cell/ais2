"""
Утилиты для обработки медиа файлов (видео/аудио)
"""
import subprocess
import logging
import tempfile
import os
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)

# Для Speech-to-Text можно использовать OpenAI Whisper или другой сервис
WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"
WHISPER_API_KEY = "your-openai-api-key"  # Загружать из .env


def convert_video_to_audio(video_path: str, output_audio_path: str) -> bool:
    """
    Конвертация видео в аудио формат MP3
    
    Args:
        video_path: Путь к видео файлу (.mp4)
        output_audio_path: Путь для сохранения аудио (.mp3)
    
    Returns:
        True если конвертация успешна
    """
    try:
        command = [
            '/opt/homebrew/bin/ffmpeg',
            '-i', video_path,
            '-vn',  # Без видео
            '-acodec', 'libmp3lame',
            '-ab', '192k',
            '-ar', '44100',
            '-y',  # Перезаписать если существует
            output_audio_path
        ]
        
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        
        logger.info(f"Видео конвертировано в аудио: {output_audio_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при конвертации видео: {e.stderr.decode()}")
        return False
    except FileNotFoundError:
        logger.error("FFmpeg не найден. Установите: apt-get install ffmpeg")
        return False

'''
на будущее если планируется перенос сервисов на отдельные хосты
async def transcribe_audio_to_text(audio_path: str) -> str:
    """
    Преобразование аудио в текст с использованием Whisper API
    
    Args:
        audio_path: Путь к аудио файлу
    
    Returns:
        Транскрибированный текст
    """
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            with open(audio_path, 'rb') as audio_file:
                files = {
                    'file': ('audio.mp3', audio_file, 'audio/mpeg'),
                    'model': (None, 'whisper-1')
                }
                
                response = await client.post(
                    WHISPER_API_URL,
                    headers={
                        "Authorization": f"Bearer {WHISPER_API_KEY}"
                    },
                    files=files
                )
                response.raise_for_status()
                result = response.json()
                
                return result['text']
                
    except Exception as e:
        logger.error(f"Ошибка при транскрибации аудио: {e}")
        raise
'''
'''
для использования не на маке
async def transcribe_audio_to_text(audio_path: str) -> str:
    import whisper
    import asyncio
    import logging

    """
    Преобразование аудио в текст с использованием Whisper API
    
    Args:
        audio_path: Путь к аудио файлу
    
    Returns:
        Транскрибированный текст
    """
    model = whisper.load_model("large")  # можно medium/large, если ресурсы позволяют


    try:
        # Whisper не асинхронный, поэтому выполняем в отдельном потоке
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, model.transcribe, audio_path)
        return result['text']
        
    except Exception as e:
        logger.error(f"Ошибка при транскрибации аудио: {e}")
        raise
'''
async def transcribe_audio_to_text(audio_path: str) -> str:
    """
    Преобразование аудио в текст с использованием Whisper API
    
    Args:
        audio_path: Путь к аудио файлу
    
    Returns:
        Транскрибированный текст
    """
    import asyncio
    import logging
    import mlx_whisper 

    try:
        text = mlx_whisper.transcribe(audio_path, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language="ru")["text"]
        print(text)

        # В result хранится dict с ключом "text"
        return text
        
    except Exception as e:
        logger.error(f"Ошибка при транскрибации аудио: {e}")
        raise

async def process_interview_video(video_bytes: bytes, candidate_id: int, vacancy_id: int) -> tuple[str, str, str]:
    """
    Полная обработка видео интервью
    
    Args:
        video_bytes: Байты видео файла
        candidate_id: ID кандидата
        vacancy_id: ID вакансии
    
    Returns:
        (video_path, audio_path, transcribed_text)
    """
    # Создаем временные директории
    media_dir = Path("media/interviews")
    media_dir.mkdir(parents=True, exist_ok=True)
    
    video_filename = f"interview_c{candidate_id}_v{vacancy_id}.webm"
    audio_filename = f"interview_c{candidate_id}_v{vacancy_id}.mp3"
    
    video_path = str(media_dir / video_filename)
    audio_path = str(media_dir / audio_filename)
    
    # Сохраняем видео
    with open(video_path, 'wb') as f:
        f.write(video_bytes)
    
    logger.info(f"Видео сохранено: {video_path}")
    
    # Конвертируем в аудио
    convert_success = convert_video_to_audio(video_path, audio_path)
    if not convert_success:
        raise Exception("Не удалось конвертировать видео в аудио")
    
    # Транскрибируем аудио в текст
    transcribed_text = await transcribe_audio_to_text(audio_path)
    
    logger.info(f"Аудио транскрибировано, длина текста: {len(transcribed_text)} символов")
    
    return video_path, audio_path, transcribed_text

