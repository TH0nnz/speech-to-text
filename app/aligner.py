"""
aligner.py
對齊模組：將 WhisperX 逐字稿與 pyannote 說話人標籤合併
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def assign_speaker(segment: dict, diarization: List[Dict]) -> str:
    """
    根據時間重疊比例，將最匹配的說話人標籤指派給一個轉錄片段。
    """
    seg_start = segment.get("start", 0.0)
    seg_end = segment.get("end", 0.0)
    seg_duration = seg_end - seg_start

    best_speaker = "UNKNOWN"
    best_overlap = 0.0

    for d in diarization:
        overlap_start = max(seg_start, d["start"])
        overlap_end = min(seg_end, d["end"])
        overlap = max(0.0, overlap_end - overlap_start)

        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = d["speaker"]

    # fallback：若無重疊，以片段中點落點判斷
    if best_overlap == 0.0:
        mid = (seg_start + seg_end) / 2.0
        for d in diarization:
            if d["start"] <= mid <= d["end"]:
                best_speaker = d["speaker"]
                break

    return best_speaker


def align_speakers(transcript: dict, diarization: List[Dict], config: dict) -> List[Dict]:
    """
    合併逐字稿與說話人分割結果，回傳含說話人標籤的片段列表。

    Returns:
        list: [
            {
                'start': float,
                'end': float,
                'speaker': str,
                'text': str,
                'words': list
            },
            ...
        ]
    """
    segments = transcript.get("segments", [])
    result = []

    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        speaker = assign_speaker(seg, diarization)
        result.append(
            {
                "start": round(seg["start"], 3),
                "end": round(seg["end"], 3),
                "speaker": speaker,
                "text": text,
                "words": seg.get("words", []),
            }
        )

    # 合併相鄰同說話人片段
    if config.get("merge_consecutive", True):
        gap = float(config.get("merge_gap", 1.0))
        result = _merge_consecutive(result, gap)

    logger.info(f"  最終共 {len(result)} 段（合併後）")
    return result


def _merge_consecutive(segments: List[Dict], gap_threshold: float) -> List[Dict]:
    """合併相鄰且說話人相同、間隔在 gap_threshold 秒以內的片段"""
    if not segments:
        return segments

    merged = [segments[0].copy()]
    merged[0]["words"] = list(merged[0].get("words", []))

    for seg in segments[1:]:
        last = merged[-1]
        gap = seg["start"] - last["end"]

        if seg["speaker"] == last["speaker"] and gap <= gap_threshold:
            last["end"] = seg["end"]
            last["text"] = last["text"] + " " + seg["text"]
            last["words"].extend(seg.get("words", []))
        else:
            new_seg = seg.copy()
            new_seg["words"] = list(new_seg.get("words", []))
            merged.append(new_seg)

    return merged
