"""
main.py
語音轉文字系統入口
支援三種執行模式：
  1. 自動監控模式（--watch）：監控 input/ 資料夾，有新檔案自動處理
  2. 批次模式（預設）：處理 input/ 資料夾內所有音訊檔案
  3. 單一檔案模式（--file）：指定單一音訊檔案處理
"""
import argparse
import logging
import os
import sys
import time
from pathlib import Path

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# 確保 app/ 目錄在 Python 路徑
sys.path.insert(0, os.path.dirname(__file__))
from pipeline import process_file

# ── 日誌設定 ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── 支援的音訊/影片格式 ─────────────────────────────────────
SUPPORTED_EXTS = {
    ".mp3", ".mp4", ".wav", ".m4a", ".flac",
    ".ogg", ".aac", ".wma", ".mkv", ".webm",
    ".mov", ".avi",
}


# ── Watchdog 事件處理器 ─────────────────────────────────────
class AudioFileHandler(FileSystemEventHandler):
    def __init__(self, output_dir: str, config: dict):
        self.output_dir = output_dir
        self.config = config
        self._processing: set = set()

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in SUPPORTED_EXTS:
            return
        if str(path) in self._processing:
            return

        self._processing.add(str(path))
        logger.info(f"🔔 偵測到新檔案：{path.name}")

        # 等待檔案寫入完成（避免讀取到不完整的檔案）
        self._wait_for_file(path)

        try:
            process_file(str(path), self.output_dir, self.config)
        except Exception as e:
            logger.error(f"處理失敗 [{path.name}]：{e}", exc_info=True)
        finally:
            self._processing.discard(str(path))

    @staticmethod
    def _wait_for_file(path: Path, timeout: int = 30):
        """等待檔案大小穩定，確保複製完成"""
        prev_size = -1
        for _ in range(timeout):
            try:
                curr_size = path.stat().st_size
                if curr_size == prev_size and curr_size > 0:
                    return
                prev_size = curr_size
            except OSError:
                pass
            time.sleep(1)


# ── 主程式 ──────────────────────────────────────────────────
def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description="語音轉文字系統（含說話人分割）",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
使用範例：
  # 自動監控模式（container 預設）
  python main.py --watch

  # 批次處理 input/ 所有檔案
  python main.py --batch

  # 處理單一檔案
  python main.py --file /input/meeting.mp3

  # 指定參數覆蓋 config
  python main.py --file /input/meeting.mp3 --language zh --num-speakers 3
        """,
    )
    parser.add_argument("--file", "-f", help="指定單一音訊檔案路徑")
    parser.add_argument("--batch", "-b", action="store_true", help="批次處理 input/ 所有音訊檔案")
    parser.add_argument("--watch", "-w", action="store_true", help="監控 input/ 資料夾自動處理")
    parser.add_argument("--input-dir", "-i", default="/input", help="輸入資料夾（預設：/input）")
    parser.add_argument("--output-dir", "-o", default="/output", help="輸出資料夾（預設：/output）")
    parser.add_argument("--language", "-l", help="語言代碼（zh/en/null=自動偵測）")
    parser.add_argument("--num-speakers", "-n", type=int, help="說話人數量（不指定則自動偵測）")
    parser.add_argument("--model", "-m", help="Whisper 模型（tiny/base/small/medium/large-v3）")
    parser.add_argument("--hf-token", help="HuggingFace Token")
    parser.add_argument("--config", "-c", default="/app/config.yml", help="設定檔路徑")

    args = parser.parse_args()

    # 載入設定
    config_path = args.config if os.path.exists(args.config) else "config.yml"
    config = load_config(config_path)

    # CLI 參數覆蓋設定檔
    if args.language:
        config["language"] = args.language
    if args.num_speakers:
        config["num_speakers"] = args.num_speakers
    if args.model:
        config["model"] = args.model
    if args.hf_token:
        config["hf_token"] = args.hf_token

    # 環境變數優先
    if os.environ.get("HF_TOKEN"):
        config["hf_token"] = os.environ["HF_TOKEN"]

    # 建立輸出目錄
    output_dir = args.output_dir
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # ── 執行模式選擇 ───────────────────────────────────────

    if args.file:
        # 單一檔案模式
        logger.info(f"🎙️ 單一檔案模式：{args.file}")
        process_file(args.file, output_dir, config)

    elif args.watch:
        # 監控模式
        input_dir = args.input_dir
        Path(input_dir).mkdir(parents=True, exist_ok=True)

        logger.info("=" * 55)
        logger.info("  🎙️  語音轉文字系統 - 監控模式啟動")
        logger.info(f"  監控資料夾：{input_dir}")
        logger.info(f"  輸出資料夾：{output_dir}")
        logger.info(f"  使用模型：{config.get('model', 'large-v3')}")
        logger.info("=" * 55)

        # 先處理現有檔案
        existing = sorted(
            [f for f in Path(input_dir).iterdir() if f.suffix.lower() in SUPPORTED_EXTS]
        )
        if existing:
            logger.info(f"📂 發現 {len(existing)} 個現有檔案，開始處理...")
            for f in existing:
                try:
                    process_file(str(f), output_dir, config)
                except Exception as e:
                    logger.error(f"處理失敗 [{f.name}]：{e}", exc_info=True)

        # 啟動監控
        handler = AudioFileHandler(output_dir, config)
        observer = Observer()
        observer.schedule(handler, input_dir, recursive=False)
        observer.start()
        logger.info("✅ 等待新檔案（按 Ctrl+C 結束）...")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 停止監控...")
            observer.stop()
        observer.join()

    else:
        # 預設：批次模式（處理 input/ 全部檔案）
        input_dir = args.input_dir
        files = sorted(
            [f for f in Path(input_dir).iterdir() if f.suffix.lower() in SUPPORTED_EXTS]
        )

        if not files:
            logger.warning(f"在 {input_dir} 中沒有找到音訊檔案")
            logger.info(f"支援格式：{', '.join(sorted(SUPPORTED_EXTS))}")
            sys.exit(0)

        logger.info(f"🎙️ 批次模式：找到 {len(files)} 個檔案")
        success, failed = 0, 0
        for f in files:
            try:
                process_file(str(f), output_dir, config)
                success += 1
            except Exception as e:
                logger.error(f"處理失敗 [{f.name}]：{e}", exc_info=True)
                failed += 1

        logger.info(f"🏁 批次完成：成功 {success} 個，失敗 {failed} 個")


if __name__ == "__main__":
    main()
