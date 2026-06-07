👉 這是你現在在用 Whisper pipeline 最適合的方法

步驟 1️ 建立清單檔

建立一個 list.txt

file 'audio1.m4a'
file 'audio2.m4a'
file 'audio3.m4a'
步驟 2️ 合併
ffmpeg -f concat -safe 0 -i list.txt -c copy output.m4a

