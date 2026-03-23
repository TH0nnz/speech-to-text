"""
txt_exporter.py
輸出純文字格式（含說話人標籤與時間戳）

範例：
[00:00:05 - 00:00:12] SPEAKER_00:
大家好，今天我們來討論第三季的業績報告。

[00:00:13 - 00:00:20] SPEAKER_01:
好的，我先報告一下業務端的狀況。
"""


def _fmt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def export_txt(segments: list, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        for seg in segments:
            start = _fmt(seg["start"])
            end = _fmt(seg["end"])
            speaker = seg["speaker"]
            text = seg["text"]
            f.write(f"[{start} - {end}] {speaker}:\n{text}\n\n")
