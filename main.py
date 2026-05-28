import time
from pathlib import Path
import shutil
import logging
from logging.handlers import RotatingFileHandler

SOURCE_DIR = Path("//ServerName/Share/SourceFolder")

DESTINATION_MAPPING = {
	".txt": Path("//ServerName/Share/Destination/_txt"),
	".pdf": Path("//ServerName/Share/Destination/_pdf"),
	".c":   Path("//ServerName/Share/Destination/_c"),
	".h":   Path("//ServerName/Share/Destination/_h"),
	".m":   Path("//ServerName/Share/Destination/_m"),
	".z":   Path("//ServerName/Share/Destination/_z"),
}

LOG_FILE = Path("//ServerName/Share/AdminScripts/sync_log.txt")
CHECK_INTERVAL_SECONDS = 60

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
	LOG_FILE,
	maxBytes=1 * 1024 * 1024,
	backupCount=3,
	encoding="utf-8"
)
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)

if logger.hasHandlers():
	logger.handlers.clear()
logger.addHandler(handler)

def parse_target_directories(ext: str) -> list[Path]:
	"""
	拡張子からコピー先（複数可）を割り出す安全な判定機能
	例1: ".txt" -> [_txt]
	例2: ".cm"  -> [_c, _m]
	例3: ".doc" -> [] (対象外として無視)
	"""

	if ext in DESTINATION_MAPPING:
		return [DESTINATION_MAPPING[ext]]
	
	# パターンB: 組み合わせ拡張子（.cm -> .c と .m など）の判定
	# 拡張子のドットを外した文字リストを取得 (例: "cm" -> ['c', 'm'])
	chars = list(ext.replace(".", ""))
	
	# 全ての文字がマッピングに存在する安全な組み合わせかチェック（誤爆防止）
	if all(f".{c}" in DESTINATION_MAPPING for c in chars):
		# 該当する全てのベースフォルダのパスを返す
		return [DESTINATION_MAPPING[f".{c}"] for c in chars]
		
	# どちらにも当てはまらない（指定外のファイル）場合は空のリストを返す
	return []


def sync_single_folder(src_dir: Path, dest_base_dir: Path):
	"""1つのフォルダを、指定された1つのベースフォルダへ同期する"""
	try:
		# ベースフォルダの存在保証
		dest_base_dir.mkdir(parents=True, exist_ok=True)
		
		target_dir_path = dest_base_dir / src_dir.name
		needs_copy = False

		if not target_dir_path.exists():
			needs_copy = True
		else:
			# フォルダ内の最新ファイルの更新日時を比較
			src_files = [f for f in src_dir.glob("**/*") if f.is_file()]
			tgt_files = [f for f in target_dir_path.glob("**/*") if f.is_file()]
			
			source_mtime = max([f.stat().st_mtime for f in src_files], default=0)
			target_mtime = max([f.stat().st_mtime for f in tgt_files], default=0)
			
			if source_mtime > target_mtime + 1:
				needs_copy = True
				
		if needs_copy:
			shutil.copytree(
				src_dir, 
				target_dir_path, 
				dirs_exist_ok=True, 
				symlinks=True, 
				ignore_dangling_symlinks=True
			)
			msg = f"同期完了: 【{src_dir.name}】 ➔ 【{dest_base_dir.name}】"
			print(msg)
			logging.info(msg)
			
	except PermissionError:
		logging.warning(f"アクセス拒否: 【{src_dir.name}】内の一部ファイルが使用中のためスキップしました。")
	except Exception as e:
		logging.error(f"エラー: 【{src_dir.name}】の同期処理中に問題発生: {e}")

def smart_sync_controller():
	"""フォルダ内をパトロールし、振り分けと同期を統括する"""
	if not SOURCE_DIR.exists():
		logging.error(f"コピー元フォルダが存在しません: {SOURCE_DIR}")
		return
		
	for dir_path in SOURCE_DIR.iterdir():
		if not dir_path.is_dir():
			continue
		
		ext = dir_path.suffix.lower()
		if not ext:
			continue
			
		# 拡張子からコピーすべき先のリストを取得
		target_dirs = parse_target_directories(ext)
		
		# 取得したコピー先（1箇所、またはCとMのような複数箇所）すべてに対して処理を実行
		for dest_base in target_dirs:
			sync_single_folder(dir_path, dest_base)

if __name__ == "__main__":
	print(f"複数分配対応・フォルダ同期システムを起動しました。（{CHECK_INTERVAL_SECONDS}秒間隔）")
	
	while True:
		try:
			smart_sync_controller()
			time.sleep(CHECK_INTERVAL_SECONDS)
		except KeyboardInterrupt:
			print("システムを停止しました。")
			break
		except Exception as e:
			logging.critical(f"システム全体に影響する致命的エラー: {e}")
			time.sleep(CHECK_INTERVAL_SECONDS)