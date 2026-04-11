import os
import json
import logging
import argparse
import concurrent.futures
import shutil
from pathlib import Path
from datetime import datetime
from lib.NekoRes import NekoRes

# config logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(threadName)s: %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    # get cli input
    parser = argparse.ArgumentParser(description="NekoLab Mirror Sync Script")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    parser.add_argument("--workers", type=int, default=5, help="Number of concurrent download workers")
    parser.add_argument("--working-dir", help="Override working directory")
    args = parser.parse_args()

    # load config file
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Config file not found: {args.config}")
        return
    
    config = json.loads(config_path.read_text(encoding="utf-8"))
    working_dir = Path(
        args.working_dir or os.getenv("TUNASYNC_WORKING_DIR") or config.get("working_dir", ".")
    ).resolve()
    working_dir.mkdir(parents=True, exist_ok=True)

    res_handler = NekoRes(f"https://api.github.com/repos/{config['repo']}/releases")
    
    try:
        all_releases = res_handler.get_releases()
        # ignore prerelease
        releases = [r for r in all_releases if not r.get("prerelease", False)]
    except Exception as e:
        logger.error(f"API Error: {e}")
        return

    target_releases = releases[:config.get("keep_versions", 1)]
    
    download_tasks = []
    downloaded_version_names = []
    version_metadata_map = {} 

    # init download
    for i, rel in enumerate(target_releases):
        version_name = rel["tag_name"]
        display_name = rel.get("name") or version_name
        version_dir = working_dir / version_name
        version_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_version_names.append(version_name)
        is_latest = (i == 0)
        url_path = "LatestRelease" if is_latest else version_name

        metadata = {
            "name": display_name,
            "tag_name": version_name,
            "assets": [],
            "sync_at": datetime.now().isoformat()
        }

        for asset in rel.get("assets", []):
            safe_asset_name = NekoRes.ensure_safe_name(asset["name"])
            zip_path = version_dir / safe_asset_name
            ts = datetime.strptime(asset["updated_at"], "%Y-%m-%dT%H:%M:%SZ").timestamp()

            final_download_url = f"{config['base_mirror_url']}/{version_name}/{safe_asset_name}"
            
            # download
            download_tasks.append({
                "url": asset["browser_download_url"],
                "dst": zip_path,
                "size": asset["size"],
                "ts": ts,
                "version": version_name,
                "is_latest": is_latest
            })

            # write metadata["assets"]
            metadata["assets"].append({
                "name": safe_asset_name,
                "content_type": asset["content_type"],
                "browser_download_url": final_download_url,
                "size": asset["size"]
            })
        
        version_metadata_map[version_name] = metadata

    # download release file
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers, thread_name_prefix="Worker") as executor:
        future_to_task = {
            executor.submit(
                NekoRes.download_file, t["url"], t["dst"], t["size"], t["ts"]
            ): t for t in download_tasks
        }

        successful_versions = set()
        for future in concurrent.futures.as_completed(future_to_task):
            task = future_to_task[future]
            if future.result():
                successful_versions.add(task["version"])
                if task["is_latest"]:
                    link_latest(working_dir, task["version"])

    # write release file
    for v_name in successful_versions:
        res_info_path = working_dir / v_name / "release"
        res_info_path.write_text(
            json.dumps(version_metadata_map[v_name], indent=4, ensure_ascii=False),
            encoding="utf-8"
        )
        logger.info(f"Metadata saved for {v_name}")

    cleanup_old_versions(working_dir, downloaded_version_names)
    logger.info("Sync completed.")

def link_latest(working_dir: Path, target_name: str):
    link_path = working_dir / "LatestRelease"
    try:
        if link_path.is_symlink() or link_path.exists():
            link_path.unlink()
        link_path.symlink_to(target_name, target_is_directory=True)
        logger.info(f"LatestRelease -> {target_name}")
    except Exception as e:
        logger.error(f"Symlink error: {e}")

def cleanup_old_versions(working_dir: Path, keep_list: list):
    for folder in working_dir.iterdir():
        if folder.is_dir() and not folder.is_symlink():
            if folder.name.startswith("v") and folder.name not in keep_list:
                logger.info(f"Cleanup: {folder.name}")
                shutil.rmtree(folder)

if __name__ == "__main__":
    main()
