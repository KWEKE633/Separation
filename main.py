import time
from pathlib import Path
import shutil
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

SOURCE_DIR = Path(r"")

DESTINATION_MAPPING = {
	".txt": Path(r""),
	".pdf": Path(r""),
	".": Path(r""),
}

OTHER_DST_DIR = Path(r"")

LOG_FILE =  Path(r"")

CHECK_INTERVAL_SECONDS = 60

# logging.basicConfig(
#     filename=LOG_FILE,
#     level=logging.INFO,
#     format="[%(asctime)s] %(levelname)s: %(message)s",
#     datefmt="%Y-%m-%d %H:%M:%S",
#     encoding="utf-8"
# )

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
	LOG_FILE,
	maxBytes=1 * 1024 * 1024,	# 1MB
	backupCount=3,				# 古いログを３つまで残す
	encoding="utf-8"
)
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)

if logger.hasHandlers():
	logger.handlers.clear()
logger.addHandler(handler)

def smart_sync_files():
	if not SOURCE_DIR.exists():
		logging.error(f"コピー元フォルダが存在しません: {SOURCE_DIR}")
		return
	for file_path in SOURCE_DIR.iterdir():
		if not file_path.is_file():
			continue
		
		ext = file_path.suffix.lower()
		filename = file_path.name
		dest_dir = DESTINATION_MAPPING.get(ext, OTHER_DST_DIR)

		try:
			dest_dir.mkdir(parents=True, exist_ok=True)
			target_path	= dest_dir / filename

			needs_copy = False

			if not target_path.exists():
				needs_copy = True
			else:
				source_mtime = file_path.stat().st_mtime
				target_mtime = target_path.stat().st_mtime
				
				if source_mtime > target_mtime + 1:
					needs_copy = True
			if needs_copy:
				shutil.copy2(file_path, target_path)
				msg = f"同期完了（上書き/新規）: {filename} ➔ {dest_dir.name}"
				print(msg)
				logging.info(msg)
		
		except PermissionError:
			logging.warning(f"アクセス拒否: {filename} は現在他の人が開いているため上書きできませんでした。")
		except Exception as e:
			logging.error(f"エラー: {filename} の処理中に問題発生: {e}")

if __name__ == "__main__":
	print(f"自動同期システムを起動しました。（{CHECK_INTERVAL_SECONDS}秒間隔でパトロールします）")
	print("終了するにはこの画面を閉じるか、Ctrl+C を押してください。\n")

	while True:
		try:
			smart_sync_files()

			time.sleep(CHECK_INTERVAL_SECONDS)
		except KeyboardInterrupt:
			print("システムを自動で停止しました。")
			break
		except Exception as e:
			logging.critical(f"システム全体に影響する致命的エラー: {e}")
			time.sleep(CHECK_INTERVAL_SECONDS)