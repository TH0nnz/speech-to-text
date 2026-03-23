# Speech-to-Text 語音轉文字系統

基於 WhisperX + pyannote.audio 的語音辨識系統，支援多說話人分割，輸出 TXT / TSV / SRT / VTT 四種格式。

---

## 功能特色

- **語音辨識**：使用 WhisperX（OpenAI Whisper large-v3），支援中文、英文及中英混合
- **說話人分割**：自動識別每位發言者（SPEAKER_00、SPEAKER_01…）
- **字詞級時間戳**：精確到毫秒的時間對齊
- **四種輸出格式**：TXT、TSV、SRT（字幕）、VTT（Web 字幕）
- **三種執行模式**：自動監控、批次處理、單一檔案
- **GPU 加速**：支援 NVIDIA CUDA 12.1，速度提升 5–10 倍
- **模型快取**：首次下載後快取至 Docker volume，重啟不重新下載

---

## 環境需求

| 項目 | 需求 |
|------|------|
| Docker | 20.10+ |
| Docker Compose | 2.x |
| NVIDIA Driver | 支援 CUDA 12.1 向下相容（Driver 470+） |
| GPU 記憶體 | 建議 8GB+（large-v3） |

> CPU 模式亦可運行，程式會自動偵測並切換，但速度顯著較慢。

---

## 快速開始

### 步驟 1：取得 HuggingFace Token

1. 至 https://huggingface.co/settings/tokens 建立 Access Token（免費）
2. 至以下兩頁點選 **Agree** 同意使用條款（只需一次）：
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0

### 步驟 2：設定 Token

建立 `.env` 檔案並填入 Token：

```env
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

或直接在 `config.yml` 中設定 `hf_token`（環境變數優先）。

### 步驟 3：建置並啟動（自動監控模式）

```bash
docker-compose up -d --build
```

> 首次啟動會下載 Whisper large-v3（約 3GB）及 pyannote 模型（約 300MB）。

### 步驟 4：放入音訊，自動處理

```bash
cp meeting.mp3 ./input/
```

完成後，結果出現在 `output/`：

```
output/
├── meeting.txt
├── meeting.tsv
├── meeting.srt
└── meeting.vtt
```

---

## 支援的音訊格式

`.mp3` `.mp4` `.wav` `.m4a` `.flac` `.ogg` `.aac` `.wma` `.mkv` `.webm` `.mov` `.avi`

非 WAV 格式會自動透過 ffmpeg 轉換為 16kHz 單聲道 WAV 後處理。

---

## 執行模式

### 模式一：自動監控（Container 預設）

Container 持續監控 `input/`，偵測到新音訊檔案即自動觸發處理。

```bash
# 啟動
docker-compose up -d

# 查看即時 log
docker-compose logs -f

# 停止
docker-compose down
```

### 模式二：批次處理 input/ 下所有檔案

```bash
docker-compose run --rm --profile manual stt-manual --batch
```

### 模式三：單一檔案

```bash
docker-compose run --rm --profile manual stt-manual --file /input/meeting.mp3
```

---

## CLI 參數

| 參數 | 縮寫 | 說明 | 預設值 |
|------|------|------|--------|
| `--file` | `-f` | 指定單一音訊檔案 | — |
| `--batch` | `-b` | 批次處理 input/ 所有檔案 | — |
| `--watch` | `-w` | 監控 input/ 資料夾（Container 預設）| — |
| `--input-dir` | `-i` | 輸入資料夾 | `/input` |
| `--output-dir` | `-o` | 輸出資料夾 | `/output` |
| `--language` | `-l` | 語言代碼（`zh`/`en`/省略=自動偵測）| config.yml |
| `--num-speakers` | `-n` | 指定說話人數（省略=自動偵測）| config.yml |
| `--model` | `-m` | Whisper 模型大小 | config.yml |
| `--hf-token` | — | HuggingFace Token | 環境變數/config.yml |
| `--config` | `-c` | 設定檔路徑 | `/app/config.yml` |

CLI 參數的優先順序：**CLI 參數 > 環境變數 > config.yml**

範例：指定 3 位說話人、鎖定中文：

```bash
docker-compose run --rm --profile manual stt-manual \
  --file /input/meeting.mp3 \
  --language zh \
  --num-speakers 3
```

---

## 設定檔 `config.yml`

```yaml
# 模型設定
model: large-v3           # tiny / base / small / medium / large-v2 / large-v3
compute_type: float16     # GPU: float16 | CPU: int8

# 語言設定
language: null            # null=自動偵測 | zh=中文 | en=英文

# HuggingFace Token（環境變數 HF_TOKEN 優先）
hf_token: "YOUR_HF_TOKEN_HERE"

# 說話人分割
num_speakers: null        # null=自動偵測 | 數字=指定人數
min_speakers: 1           # 自動偵測時的最少人數
max_speakers: 10          # 自動偵測時的最多人數

# 批次處理
batch_size: 16            # GPU 記憶體不足時降低為 8 或 4

# 輸出格式
output_formats:
  - txt
  - tsv
  - srt
  - vtt

# 後處理
merge_consecutive: true   # 合併相鄰同說話人片段
merge_gap: 1.0            # 合併間隔閾值（秒）

# Log
verbose_output: true      # true=逐句印出結果 | false=只顯示步驟進度
```

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

### SRT — 標準字幕格式

```
1
00:00:05,200 --> 00:00:12,400
[SPEAKER_00] 大家好，今天我們來討論第三季的業績報告。

2
00:00:13,100 --> 00:00:20,800
[SPEAKER_01] 好的，我先報告一下業務端的狀況。
```

### VTT — Web 字幕格式（HTML5 / 瀏覽器）

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

## 模型大小對照

| 模型 | 參數量 | 檔案大小 | 建議用途 |
|------|--------|----------|----------|
| `tiny` | 39M | 75MB | 測試、快速驗證 |
| `base` | 74M | 142MB | 快速轉錄 |
| `small` | 244M | 466MB | 一般使用 |
| `medium` | 769M | 1.5GB | 較高精度 |
| `large-v3` | 1550M | 3.1GB | **最高精度（預設）** |

---

## 處理流程

```
音訊輸入
  │
  ├─ [ffmpeg] 非 WAV 格式轉換為 16kHz 單聲道 WAV
  │
  ├─ [1/3] transcriber.py — WhisperX 語音辨識 + 字詞級時間戳對齊
  │
  ├─ [2/3] diarizer.py — pyannote.audio 說話人分割
  │
  ├─ [3/3] aligner.py — 依時間重疊比例合併說話人標籤與逐字稿
  │           └─ merge_consecutive: 合併相鄰同說話人片段
  │
  └─ exporters/ — 輸出 TXT / TSV / SRT / VTT
```

---

## 專案結構

```
speech-to-text/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── config.yml
├── input/                     ← 放入待處理音訊
├── output/                    ← 轉換結果輸出
└── app/
    ├── main.py                ← 入口：監控 / 批次 / 單檔模式
    ├── pipeline.py            ← 主流程串接（轉錄→分割→對齊→輸出）
    ├── transcriber.py         ← WhisperX 語音辨識模組
    ├── diarizer.py            ← pyannote.audio 說話人分割模組
    ├── aligner.py             ← 說話人標籤與逐字稿時間對齊
    └── exporters/
        ├── __init__.py        ← 統一輸出介面
        ├── txt_exporter.py
        ├── tsv_exporter.py
        ├── srt_exporter.py
        └── vtt_exporter.py
```

---

## 常見問題

**Q：首次啟動很慢？**
模型首次下載後快取至 Docker volume（`huggingface_cache`、`whisper_cache`），之後重啟不需重新下載。

**Q：GPU 記憶體不足（CUDA OOM）？**
在 `config.yml` 中降低 `batch_size`：

```yaml
batch_size: 8   # 或 4
```

**Q：說話人辨識不準確？**
指定確切人數可提升準確率：

```yaml
num_speakers: 3
```

**Q：中英混合辨識效果差？**
保持 `language: null` 讓 WhisperX 自動偵測語言。

**Q：如何重新啟動 Container？**

```bash
docker-compose restart
```

---

## 技術棧

| 元件 | 用途 |
|------|------|
| [WhisperX](https://github.com/m-bain/whisperX) | 語音辨識 + 字詞級時間戳對齊 |
| [pyannote.audio 3.3.2](https://github.com/pyannote/pyannote-audio) | 說話人分割 |
| [PyTorch 2.5.1 (CUDA 12.1)](https://pytorch.org/) | 深度學習推論 |
| [ffmpeg](https://ffmpeg.org/) | 音訊格式轉換 |
| [watchdog](https://github.com/gorakhargosh/watchdog) | 資料夾監控 |
| nvidia/cuda:12.1.1-cudnn8 | Container 基礎映像 |
