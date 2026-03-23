"""
transcriber.py
語音辨識模組：使用 WhisperX 轉錄音訊並取得字詞級時間戳
"""
import logging
import torch
import whisperx

logger = logging.getLogger(__name__)

_model = None
_model_name = None


def get_model(config: dict):
    """載入並快取 Whisper 模型（避免重複載入）"""
    global _model, _model_name

    model_name = config.get("model", "large-v3")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = config.get("compute_type", "float16") if device == "cuda" else "int8"

    if _model is None or _model_name != model_name:
        logger.info(f"載入 Whisper 模型：{model_name}（device={device}, compute_type={compute_type}）")
        _model = whisperx.load_model(
            model_name,
            device=device,
            compute_type=compute_type,
            language=config.get("language") or None,
        )
        _model_name = model_name

    return _model, device


def transcribe(audio_path: str, config: dict) -> dict:
    """
    對音訊檔進行語音辨識，回傳含字詞級時間戳的結果。

    Returns:
        dict: {
            'segments': [{'start', 'end', 'text', 'words': [{'word', 'start', 'end'}]}],
            'language': str
        }
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, _ = get_model(config)

    logger.info(f"  讀取音訊：{audio_path}")
    audio = whisperx.load_audio(audio_path)

    # --- 第一步：轉錄 ---
    logger.info("  執行語音辨識...")
    transcribe_kwargs = {"batch_size": config.get("batch_size", 16)}
    if config.get("language"):
        transcribe_kwargs["language"] = config["language"]

    result = model.transcribe(audio, **transcribe_kwargs)
    detected_lang = result.get("language", "zh")
    logger.info(f"  偵測語言：{detected_lang}，共 {len(result.get('segments', []))} 片段")

    # --- 第二步：字詞級時間戳對齊 ---
    logger.info("  對齊字詞時間戳...")
    try:
        model_a, metadata = whisperx.load_align_model(
            language_code=detected_lang,
            device=device,
        )
        result = whisperx.align(
            result["segments"],
            model_a,
            metadata,
            audio,
            device,
            return_char_alignments=False,
        )
    except Exception as e:
        logger.warning(f"  字詞對齊失敗，使用原始結果：{e}")

    return result
