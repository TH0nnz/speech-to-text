"""
vtt_exporter.py
輸出 WebVTT 字幕格式（說話人使用 <v> 標籤）

範例：
WEBVTT

1
00:00:05.200 --> 00:00:12.400
<v SPEAKER_00>大家好，今天我們來討論第三季的業績報告。

2
00:00:13.100 --> 00:00:20.800
<v SPEAKER_01>好的，我先報告一下業務端的狀況。
"""


def _fmt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    if ms >= 1000:
        ms = 999
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def export_vtt(segments: list, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for i, seg in enumerate(segments, 1):
            start = _fmt(seg["start"])
            end = _fmt(seg["end"])
            speaker = seg["speaker"]
            text = seg["text"]

            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"<v {speaker}>{text}\n")
            f.write("\n")
