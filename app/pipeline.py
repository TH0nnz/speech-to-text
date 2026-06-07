"""
pipeline.py
主處理流程：串接轉錄、分割、對齊、輸出
"""
import logging
import os
import shutil
import subprocess
import tempfile
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


def _to_wav(input_path: Path, tmp_dir: str) -> Path:
    """
    若輸入檔案不是 WAV，使用 ffmpeg 轉換為 16kHz 單聲道 WAV。
    ffmpeg 支援的格式（m4a, mp3, ogg 等）都能正確轉換。
    """
    if input_path.suffix.lower() == ".wav":
        return input_path
    out_path = Path(tmp_dir) / (input_path.stem + ".wav")
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg 轉換失敗，錯誤輸出：\n{result.stderr}"
        )
    logger.info(f"  已將 {input_path.name} 轉換為 WAV：{out_path.name}")
    return out_path


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

    with tempfile.TemporaryDirectory() as tmp_dir:
        # 非 WAV 格式先轉換，pyannote.audio 只支援 WAV
        wav_path = _to_wav(input_path, tmp_dir)

        # ── 步驟 1：語音辨識 ──────────────────────────────────
        logger.info("📝 [1/3] 語音辨識中...")
        transcript = transcribe(str(input_path), config)

        # ── 步驟 2：說話人分割 ────────────────────────────────
        logger.info("👥 [2/3] 說話人分割中...")
        diarization = diarize(str(wav_path), config)

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

    # ── 建立輸出子目錄：output/<stem>/ ─────────────────────
    file_output_dir = Path(output_dir) / stem
    source_dir = file_output_dir / "source"
    file_output_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(parents=True, exist_ok=True)

    # ── 輸出檔案 ──────────────────────────────────────────
    logger.info("💾 輸出檔案中...")
    output_base = str(file_output_dir / stem)
    export_all(segments, output_base, config)

    # ── 搬移原始檔案至 source/ ────────────────────────────
    dest = source_dir / input_path.name
    shutil.move(str(input_path), str(dest))
    logger.info(f"  原始檔案已移至：{dest}")

    logger.info(f"✅ 完成！輸出目錄：{file_output_dir}/")
    return segments
