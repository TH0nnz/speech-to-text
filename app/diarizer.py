"""
diarizer.py
說話人分割模組：使用 pyannote.audio 識別每段音訊的說話人
"""
import logging
import os
import torch
from pyannote.audio import Pipeline

logger = logging.getLogger(__name__)

_pipeline = None


def get_pipeline(config: dict) -> Pipeline:
    """載入並快取 pyannote 說話人分割 Pipeline"""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    # 優先從環境變數讀取 Token
    hf_token = os.environ.get("HF_TOKEN") or config.get("hf_token")
    if not hf_token or hf_token == "YOUR_HF_TOKEN_HERE":
        raise ValueError(
            "缺少 HuggingFace Token！\n"
            "請在 config.yml 設定 hf_token 或設定環境變數 HF_TOKEN。\n"
            "申請網址：https://huggingface.co/settings/tokens\n"
            "並至以下頁面同意使用條款：\n"
            "  - https://huggingface.co/pyannote/speaker-diarization-3.1\n"
            "  - https://huggingface.co/pyannote/segmentation-3.0"
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"  載入 pyannote 說話人分割模型（device={device}）")

    _pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token,          # huggingface_hub 新版：use_auth_token 改為 token
    )
    _pipeline = _pipeline.to(device)

    return _pipeline


def diarize(audio_path: str, config: dict) -> list:
    """
    對音訊執行說話人分割。

    Returns:
        list: [{'start': float, 'end': float, 'speaker': str}, ...]
    """
    pipeline = get_pipeline(config)

    diarize_kwargs = {}
    if config.get("num_speakers"):
        diarize_kwargs["num_speakers"] = int(config["num_speakers"])
    else:
        if config.get("min_speakers"):
            diarize_kwargs["min_speakers"] = int(config["min_speakers"])
        if config.get("max_speakers"):
            diarize_kwargs["max_speakers"] = int(config["max_speakers"])

    logger.info(f"  執行說話人分割（kwargs={diarize_kwargs}）...")
    diarization = pipeline(audio_path, **diarize_kwargs)

    segments = []
    speakers_found = set()
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append(
            {
                "start": round(turn.start, 3),
                "end": round(turn.end, 3),
                "speaker": speaker,
            }
        )
        speakers_found.add(speaker)

    logger.info(f"  偵測到 {len(speakers_found)} 位說話人，共 {len(segments)} 段")
    return segments
