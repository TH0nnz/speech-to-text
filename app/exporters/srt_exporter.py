"""
srt_exporter.py
輸出 SRT 字幕格式（說話人以 [SPEAKER_XX] 標示）

範例：
1
00:00:05,200 --> 00:00:12,400
[SPEAKER_00] 大家好，今天我們來討論第三季的業績報告。

2
00:00:13,100 --> 00:00:20,800
[SPEAKER_01] 好的，我先報告一下業務端的狀況。
"""


def _fmt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    # 防止進位導致 ms=1000
    if ms >= 1000:
        ms = 999
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def export_srt(segments: list, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start = _fmt(seg["start"])
            end = _fmt(seg["end"])
            speaker = seg["speaker"]
            text = seg["text"]

            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"[{speaker}] {text}\n")
            f.write("\n")
