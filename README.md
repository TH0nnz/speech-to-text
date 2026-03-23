# 🎙️ Speech-to-Text 語音轉文字系統

> 基於 WhisperX + pyannote.audio 的會議語音辨識系統，支援多說話人分割，輸出 TXT / TSV / SRT / VTT 四種格式。

---

## 功能特色

- **語音辨識**：使用 OpenAI Whisper large-v3，支援中文、英文及中英混合
- **說話人分割**：自動識別會議中每位發言者（SPEAKER_00、SPEAKER_01…）
- **字詞級時間戳**：精確到毫秒的時間對齊
- **四種輸出格式**：TXT、TSV、SRT（字幕）、VTT（Web 字幕）
- **自動監控模式**：丟入 `input/` 資料夾即自動處理
- **GPU 加速**：支援 NVIDIA CUDA，速度提升 5–10 倍

---

## 環境需求

| 項目 | 需求 |
|------|------|
| Docker | 20.10+ |
| Docker Compose | 2.x |
| NVIDIA Driver | 572.x+ |
| CUDA | 12.x |
| GPU 記憶體 | 建議 8GB+（large-v3） |

> CPU 模式亦可運行，但速度較慢（約為音訊長度的 10–20 倍處理時間）。

---

## 快速開始

### 步驟 1：取得 HuggingFace Token

1. 至 [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) 建立 Access Token（免費）
2. 至以下兩頁點選 **Agree** 同意使用條款（只需一次）：
   - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
   - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)

### 步驟 2：設定環境變數

```bash
cp .env.example .env
```

編輯 `.env`，填入您的 Token：

```env
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 步驟 3：建置並啟動

```bash
docker-compose up -d --build
```

> 首次啟動會自動下載模型（Whisper large-v3 約 3GB、pyannote 約 300MB），請確保網路暢通。

### 步驟 4：放入音訊，自動處理

```bash
cp meeting.mp3 ./input/
```

完成後，結果會出現在 `output/` 資料夾：

```
output/
└── meeting.txt
└── meeting.tsv
└── meeting.srt
└── meeting.vtt
```

---

## 支援的音訊格式

`.mp3` `.mp4` `.wav` `.m4a` `.flac` `.ogg` `.aac` `.wma` `.mkv` `.webm` `.mov` `.avi`

---

## 輸出格式說明

### TXT — 人類可讀純文字

```
[00:00:05 - 00:00:12] SPEAKER_00:
大家好，今天我們來討論第三季的業績報告。

[00:00:13 - 00:00:20] SPEAKER_01:
好的，我先報告一下業務端的狀況。
```

### TSV — 可匯入 Excel / 資料庫

```
start     end       speaker     text
5.200     12.400    SPEAKER_00  大家好，今天我們來討論第三季的業績報告。
13.100    20.800    SPEAKER_01  好的，我先報告一下業務端的狀況。
```

### SRT — 標準字幕格式（適用影片播放器）

```
1
00:00:05,200 --> 00:00:12,400
[SPEAKER_00] 大家好，今天我們來討論第三季的業績報告。

2
00:00:13,100 --> 00:00:20,800
[SPEAKER_01] 好的，我先報告一下業務端的狀況。
```

### VTT — Web 字幕格式（適用瀏覽器 / HTML5）

```
WEBVTT

1
00:00:05.200 --> 00:00:12.400
<v SPEAKER_00>大家好，今天我們來討論第三季的業績報告。

2
00:00:13.100 --> 00:00:20.800
<v SPEAKER_01>好的，我先報告一下業務端的狀況。
```

---

## 執行模式

### 模式一：自動監控（推薦，Container 預設）

Container 啟動後持續監控 `input/` 資料夾，有新檔案自動觸發處理。

```bash
docker-compose up -d
```

查看即時 log：

```bash
docker-compose logs -f
```

### 模式二：手動單一檔案

```bash
docker-compose run --rm --profile manual stt-manual \
  --file /input/meeting.mp3
```

### 模式三：批次處理 input/ 全部檔案

```bash
docker-compose run --rm --profile manual stt-manual --batch
```

---

## 進階參數

| 參數 | 說明 | 範例 |
|------|------|------|
| `--file` | 指定單一檔案 | `--file /input/a.mp3` |
| `--language` | 指定語言 | `--language zh` |
| `--num-speakers` | 指定說話人數 | `--num-speakers 3` |
| `--model` | 指定模型大小 | `--model medium` |
| `--output-dir` | 指定輸出目錄 | `--output-dir /output` |

範例：指定 3 位說話人並鎖定中文

```bash
docker-compose run --rm --profile manual stt-manual \
  --file /input/meeting.mp3 \
  --language zh \
  --num-speakers 3
```

---

## 設定檔 `config.yml`

```yaml
model: large-v3           # tiny / base / small / medium / large-v3
compute_type: float16     # GPU: float16 | CPU: int8
language: null            # null=自動偵測 | zh=中文 | en=英文
hf_token: "YOUR_TOKEN"   # 也可透過環境變數 HF_TOKEN 設定

num_speakers: null        # null=自動偵測，或指定數字
min_speakers: 1
max_speakers: 10

batch_size: 16            # GPU 記憶體不足時調低為 8 或 4

output_formats:           # 可選擇性移除不需要的格式
  - txt
  - tsv
  - srt
  - vtt

merge_consecutive: true   # 合併相鄰同說話人片段
merge_gap: 1.0            # 合併間隔閾值（秒）
```

---

## 模型大小對照

| 模型 | 參數量 | 檔案大小 | 相對速度 | 建議用途 |
|------|--------|----------|----------|----------|
| `tiny` | 39M | 75MB | 最快 | 測試用 |
| `base` | 74M | 142MB | 快 | 快速轉錄 |
| `small` | 244M | 466MB | 中 | 一般使用 |
| `medium` | 769M | 1.5GB | 慢 | 較高精度 |
| `large-v3` | 1550M | 3.1GB | 最慢 | **最高精度（推薦）** |

---

## 常見問題

**Q：首次啟動很慢？**
模型會自動下載並快取至 Docker volume，只有第一次需要下載，之後重啟不需重新下載。

**Q：GPU 記憶體不足（CUDA OOM）？**
在 `config.yml` 中降低 `batch_size`：
```yaml
batch_size: 8   # 或 4
```

**Q：說話人辨識不準確？**
若已知說話人數量，建議明確指定：
```yaml
num_speakers: 3
```

**Q：中英混合辨識效果差？**
保持 `language: null`（自動偵測），WhisperX 會自動處理多語言混合。

**Q：如何重新啟動 Container？**
```bash
docker-compose restart
```

---

## 專案結構

```
speech-to-text/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── config.yml
├── .env.example
├── input/                     ← 放入待處理音訊
├── output/                    ← 轉換結果
└── app/
    ├── main.py                ← 入口（監控 / 批次 / 單檔模式）
    ├── pipeline.py            ← 主流程串接
    ├── transcriber.py         ← WhisperX 語音辨識
    ├── diarizer.py            ← pyannote 說話人分割
    ├── aligner.py             ← 時間戳對齊合併
    └── exporters/
        ├── __init__.py
        ├── txt_exporter.py
        ├── tsv_exporter.py
        ├── srt_exporter.py
        └── vtt_exporter.py
```

---

## 技術棧

- [WhisperX](https://github.com/m-bain/whisperX) — 語音辨識 + 字詞對齊
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) — 說話人分割
- [PyTorch](https://pytorch.org/) — 深度學習框架
- [ffmpeg](https://ffmpeg.org/) — 音訊格式轉換
- [watchdog](https://github.com/gorakhargosh/watchdog) — 資料夾監控
