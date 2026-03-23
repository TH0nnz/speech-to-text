"""
exporters/__init__.py
統一輸出介面：依照 config 決定產出哪些格式
"""
import logging
from .txt_exporter import export_txt
from .tsv_exporter import export_tsv
from .srt_exporter import export_srt
from .vtt_exporter import export_vtt

logger = logging.getLogger(__name__)

_EXPORTERS = {
    "txt": (export_txt, ".txt"),
    "tsv": (export_tsv, ".tsv"),
    "srt": (export_srt, ".srt"),
    "vtt": (export_vtt, ".vtt"),
}


def export_all(segments: list, output_base: str, config: dict):
    """根據 config 的 output_formats 輸出所有指定格式"""
    formats = config.get("output_formats", list(_EXPORTERS.keys()))

    for fmt in formats:
        if fmt not in _EXPORTERS:
            logger.warning(f"  不支援的輸出格式：{fmt}，跳過")
            continue
        func, ext = _EXPORTERS[fmt]
        path = f"{output_base}{ext}"
        try:
            func(segments, path)
            logger.info(f"  ✓ {fmt.upper():<4} → {path}")
        except Exception as e:
            logger.error(f"  ✗ {fmt.upper()} 輸出失敗：{e}")
