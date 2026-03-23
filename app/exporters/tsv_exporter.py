"""
tsv_exporter.py
輸出 TSV（Tab-Separated Values）格式

欄位：start  end  speaker  text

範例：
start    end      speaker     text
5.200    12.400   SPEAKER_00  大家好，今天我們來討論第三季的業績報告。
13.100   20.800   SPEAKER_01  好的，我先報告一下業務端的狀況。
"""
import csv


def export_tsv(segments: list, output_path: str):
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["start", "end", "speaker", "text"])
        for seg in segments:
            writer.writerow(
                [
                    f"{seg['start']:.3f}",
                    f"{seg['end']:.3f}",
                    seg["speaker"],
                    seg["text"],
                ]
            )
