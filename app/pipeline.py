"""
pipeline.py
主處理流程：串接轉錄、分割、對齊、輸出
"""
import logging
import os
from pathlib import Path

from transcriber import transcribe
from diarizer import diarize
from aligner import align_speakers
from exporters import export_all

logger = logging.getLogger(__name__)


def _fmt(seconds: float) -> str:
    """將秒數格式化為 HH:MM:SS"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _is_verbose(config: dict) -> bool:
    """從 config.yml 讀取 verbose_output，預設為 true"""
    return bool(config.get("verbose_output", True))


def process_file(input_path: str, output_dir: str, config: dict) -> list:
    """
    處理單一音訊檔案的完整流程。

    Args:
        input_path: 輸入音訊路徑
        output_dir: 輸出資料夾
        config:     設定字典

    Returns:
        list: 對齊後的片段列表
    """
    input_path = Path(input_path)
    stem = input_path.stem
    verbose = _is_verbose(config)

    logger.info("=" * 55)
    logger.info(f"  開始處理：{input_path.name}")
    logger.info("=" * 55)

    # ── 步驟 1：語音辨識 ──────────────────────────────────
    logger.info("📝 [1/3] 語音辨識中...")
    transcript = transcribe(str(input_path), config)

    # ── 步驟 2：說話人分割 ────────────────────────────────
    logger.info("👥 [2/3] 說話人分割中...")
    diarization = diarize(str(input_path), config)

    # ── 步驟 3：對齊合併 ──────────────────────────────────
    logger.info("🔗 [3/3] 對齊說話人與文字...")
    segments = align_speakers(transcript, diarization, config)

    # ── 逐句印出（由 VERBOSE_OUTPUT 控制）────────────────
    if verbose:
        logger.info("─" * 55)
        for seg in segments:
            start = _fmt(seg["start"])
            end   = _fmt(seg["end"])
            logger.info(f"  [{start}-{end}] {seg['speaker']}: {seg['text']}")
        logger.info("─" * 55)

    # ── 輸出檔案 ──────────────────────────────────────────
    logger.info("💾 輸出檔案中...")
    output_base = os.path.join(output_dir, stem)
    export_all(segments, output_base, config)

    logger.info(f"✅ 完成！輸出目錄：{output_dir}/")
    return segments
