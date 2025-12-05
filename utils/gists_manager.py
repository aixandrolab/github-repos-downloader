# --------------------------------------------------------
# Licensed under the terms of the BSD 3-Clause License
# (see LICENSE for details).
# Copyright © 2025, Alexander Suvorov
# All rights reserved.
# --------------------------------------------------------
# https://github.com/aixandrolab/
# --------------------------------------------------------
import os
import shutil
import subprocess
import concurrent.futures
import threading

from utils.progress_bar import ProgressBar


class GistsManager:
    def __init__(self, github_client, target_dir, verbose=False, timeout=30, max_retries=3, max_workers=None):
        self.github_client = github_client
        self.target_dir = target_dir
        self.verbose = verbose
        self.timeout = timeout
        self.max_retries = max_retries
        self.failed_gists = {}
        
        if max_workers is None:
            try:
                import multiprocessing
                cpu_count = multiprocessing.cpu_count()
                self.max_workers = max(1, cpu_count - 1)
            except:
                self.max_workers = 4
        else:
            self.max_workers = max_workers
        
        print(f"🎯 Using {self.max_workers} parallel workers for downloading gists")

    def execute(self):
        try:
            self.github_client.fetch_gists(max_retries=self.max_retries, timeout=self.timeout)
            gists_count = len(self.github_client.gists)
            print(f"✅ Found {gists_count} gists")

            if gists_count == 0:
                print("⚠️ No gists to process")
                return True

            self.failed_gists = self._download_items(
                target_dir=self.target_dir,
                items=self.github_client.gists,
                item_type="gists",
                timeout=self.timeout,
                verbose=self.verbose
            )
            
            if self.failed_gists:
                print(f"\n❌ Failed to download {len(self.failed_gists)} gists:")
                for gist in self.failed_gists.keys():
                    print(f"  - {gist}")
            else:
                print(f"\n✅ Successfully downloaded all {gists_count} gists")
                
        except Exception as e:
            print(f"❌ Error in execute: {e}")
            return False
        return True

    def _download_items(self, target_dir: str, items: dict, item_type: str, timeout: int, verbose: bool) -> dict:
        print(f"\n📝 Processing {len(items)} {item_type}...")

        if len(items) <= 5 or self.max_workers <= 1:
            return self._download_sequentially(target_dir, items, item_type, timeout, verbose)
        else:
            return self._download_parallel(target_dir, items, item_type, timeout, verbose)

    def _download_sequentially(self, target_dir: str, items: dict, item_type: str, timeout: int, verbose: bool) -> dict:
        failed_dict = {}
        failed_count = 0

        if verbose:
            for index, (gist_id, item_data) in enumerate(items.items(), 1):
                print(f"\n{index}/{len(items)} 🔍 Processing: {gist_id}")
                success = self._download_single_gist(gist_id, item_data, target_dir, timeout)
                if not success:
                    failed_dict[gist_id] = item_data.get('git_pull_url', '')
                    failed_count += 1
        else:
            progress_bar = ProgressBar()
            for index, (gist_id, item_data) in enumerate(items.items(), 1):
                progress_bar.update(index, len(items), failed_count, f"Processing: {gist_id}")
                success = self._download_single_gist(gist_id, item_data, target_dir, timeout)
                if not success:
                    failed_dict[gist_id] = item_data.get('git_pull_url', '')
                    failed_count += 1

            if not failed_dict:
                progress_bar.finish(f'Downloading {item_type} completed successfully!')

        if failed_dict:
            print(f"\n🔄 Retrying {len(failed_dict)} failed {item_type}...")
            failed_dict = self._retry_failed_items(failed_dict, target_dir, timeout, verbose)

        return failed_dict

    def _download_parallel(self, target_dir: str, items: dict, item_type: str, timeout: int, verbose: bool) -> dict:
        print(f"🚀 Starting parallel download of gists with {self.max_workers} workers...")
        
        failed_dict = {}
        success_count = 0
        lock = threading.Lock()
        progress_lock = threading.Lock()
        
        download_tasks = []
        for gist_id, item_data in items.items():
            download_tasks.append((gist_id, item_data))
        
        if verbose:
            print(f"📋 Total gist tasks: {len(download_tasks)}")
        
        def download_single(task):
            gist_id, item_data = task
            try:
                success = self._download_single_gist(gist_id, item_data, target_dir, timeout)
                
                with lock:
                    if success:
                        nonlocal success_count
                        success_count += 1
                        if verbose:
                            print(f"✅ Downloaded gist: {gist_id}")
                        return (gist_id, True)
                    else:
                        failed_dict[gist_id] = item_data.get('git_pull_url', '')
                        if verbose:
                            print(f"❌ Failed gist: {gist_id}")
                        return (gist_id, False)
            except Exception as e:
                with lock:
                    failed_dict[gist_id] = item_data.get('git_pull_url', '')
                    if verbose:
                        print(f"❌ Error downloading gist {gist_id}: {e}")
                return (gist_id, False)
        
        if not verbose:
            progress_bar = ProgressBar()
            completed = 0
            total_tasks = len(download_tasks)
            
            def update_progress(future):
                nonlocal completed
                with progress_lock:
                    completed += 1
                    progress_bar.update(completed, total_tasks, len(failed_dict), "Downloading gists...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            if verbose:
                results = list(executor.map(download_single, download_tasks))
            else:
                futures = [executor.submit(download_single, task) for task in download_tasks]
                
                for future in concurrent.futures.as_completed(futures):
                    update_progress(future)
                    future.result()
        
        if not verbose and not failed_dict:
            progress_bar.finish(f'Parallel download completed! {success_count}/{len(items)} gists successful')
        
        if failed_dict:
            print(f"\n🔄 Retrying {len(failed_dict)} failed {item_type} in parallel...")
            failed_dict = self._retry_failed_items_parallel(failed_dict, target_dir, timeout, verbose)
        
        return failed_dict

    def _retry_failed_items_parallel(self, failed_items: dict, target_dir: str, timeout: int, verbose: bool) -> dict:
        remaining_failed = failed_items.copy()
        
        if not remaining_failed:
            return {}
        
        print(f"\n🔄 Retrying {len(remaining_failed)} failed gists in parallel...")
        
        for retry_attempt in range(self.max_retries):
            if not remaining_failed:
                break
                
            print(f"\n📋 Parallel retry attempt {retry_attempt + 1}/{self.max_retries}")
            
            current_failed = remaining_failed.copy()
            remaining_failed = {}
            lock = threading.Lock()
            
            def retry_single(task):
                gist_id, url = task
                
                gist_data = self.github_client.gists.get(gist_id)
                if not gist_data:
                    with lock:
                        remaining_failed[gist_id] = url
                    if verbose:
                        print(f"❌ No data for gist: {gist_id}")
                    return False
                
                success = self._download_single_gist(gist_id, gist_data, target_dir, timeout)
                
                if not success:
                    with lock:
                        remaining_failed[gist_id] = url
                    if verbose:
                        print(f"⚠️ Still failed after retry: {gist_id}")
                elif verbose:
                    print(f"✅ Successfully downloaded on retry: {gist_id}")
                
                return success
            
            retry_tasks = list(current_failed.items())
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                if verbose:
                    results = list(executor.map(retry_single, retry_tasks))
                else:
                    progress_bar = ProgressBar()
                    completed = 0
                    
                    def update_retry_progress(future):
                        nonlocal completed
                        completed += 1
                        progress_bar.update(completed, len(retry_tasks), len(remaining_failed), "Retrying gists...")
                    
                    futures = [executor.submit(retry_single, task) for task in retry_tasks]
                    for future in concurrent.futures.as_completed(futures):
                        update_retry_progress(future)
                        future.result()
            
            if remaining_failed:
                print(f"⚠️ Still {len(remaining_failed)} gists failed after parallel retry {retry_attempt + 1}")
            else:
                print(f"✅ All gists successfully downloaded after parallel retry {retry_attempt + 1}")
                break
        
        return remaining_failed

    def _download_single_gist(self, gist_id: str, item_data: dict, target_dir: str, timeout: int) -> bool:
        try:
            file_path = os.path.join(target_dir, f"{gist_id}.zip")
            
            username = self.github_client.login if hasattr(self.github_client, 'login') else 'anonymous'
            
            if hasattr(self.github_client, 'token') and self.github_client.token:
                url = f"https://{self.github_client.token}@gist.github.com/{username}/{gist_id}/archive/master.zip"
            else:
                url = f"https://gist.github.com/{username}/{gist_id}/archive/master.zip"
            
            if self.verbose:
                print(f"🎯 Gist URL: {url}")
                print(f"📁 Saving to: {file_path}")
            
            success = self._download_with_curl(url, file_path, timeout)
            
            if success:
                if self.verbose:
                    print(f"✅ Successfully downloaded gist: {gist_id}")
                return True
            else:
                if self.verbose:
                    print(f"⚠️ Trying alternative URL for gist: {gist_id}")
                
                if hasattr(self.github_client, 'token') and self.github_client.token:
                    url = f"https://api.github.com/gists/{gist_id}"
                    cmd = [
                        'curl', '-s', '-H', f'Authorization: token {self.github_client.token}',
                        '-H', 'Accept: application/vnd.github.v3+json', url
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
                    if result.returncode == 0:
                        import json
                        try:
                            gist_info = json.loads(result.stdout)
                            git_pull_url = gist_info.get('git_pull_url')
                            if git_pull_url:
                                if '/gist.github.com/' in git_pull_url:
                                    archive_url = git_pull_url.replace('.git', '/archive/master.zip')
                                    success = self._download_with_curl(archive_url, file_path, timeout)
                                    if success:
                                        if self.verbose:
                                            print(f"✅ Downloaded via API: {gist_id}")
                                        return True
                        except:
                            pass
                
                if self.verbose:
                    print(f"❌ Failed to download gist: {gist_id}")
                return False
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Error downloading gist {gist_id}: {e}")
            return False

    def _download_with_curl(self, url: str, file_path: str, timeout: int) -> bool:
        """Скачивает файл с помощью curl"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            cmd = [
                'curl', 
                '-L',
                '-o', file_path,
                '--connect-timeout', '30',
                '--max-time', str(timeout),
                '--retry', '3',
                '--retry-delay', '5',
            ]
            
            if not self.verbose:
                cmd.append('--silent')
            
            cmd.append(url)
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout + 10
            )
            
            if result.returncode == 0:
                if os.path.exists(file_path) and os.path.getsize(file_path) > 100:
                    with open(file_path, 'rb') as f:
                        header = f.read(4)
                        if header == b'PK\x03\x04':
                            return True
                        else:
                            if self.verbose:
                                print(f"⚠️ File is not a valid ZIP: {os.path.basename(file_path)}")
                            os.remove(file_path)
                            return False
                else:
                    if self.verbose:
                        print(f"⚠️ Downloaded file is empty or missing")
                    return False
            else:
                if self.verbose:
                    print(f"⚠️ Download failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            if self.verbose:
                print(f"⏰ Download timeout")
            return False
        except Exception as e:
            if self.verbose:
                print(f"❌ Error downloading: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return False

    def _retry_failed_items(self, failed_items: dict, target_dir: str, timeout: int, verbose: bool) -> dict:
        remaining_failed = failed_items.copy()
        
        if not remaining_failed:
            return {}
        
        print(f"\n🔄 Retrying {len(remaining_failed)} failed gists...")
        
        for retry_attempt in range(self.max_retries):
            if not remaining_failed:
                break
                
            print(f"\n📋 Retry attempt {retry_attempt + 1}/{self.max_retries}")
            
            current_failed = remaining_failed.copy()
            remaining_failed = {}
            
            for gist_id, url in current_failed.items():
                if verbose:
                    print(f"🔄 Retrying: {gist_id}")
                
                gist_data = self.github_client.gists.get(gist_id)
                if not gist_data:
                    if verbose:
                        print(f"❌ No data for gist: {gist_id}")
                    remaining_failed[gist_id] = url
                    continue
                
                success = self._download_single_gist(gist_id, gist_data, target_dir, timeout)
                
                if not success:
                    remaining_failed[gist_id] = url
                elif verbose:
                    print(f"✅ Successfully downloaded on retry: {gist_id}")
            
            if remaining_failed:
                print(f"⚠️ Still {len(remaining_failed)} gists failed after attempt {retry_attempt + 1}")
        
        return remaining_failed

    def _create_item_path(self, target_dir: str, item_name: str) -> str:
        item_path = os.path.normpath(os.path.join(target_dir, os.path.basename(item_name)))
        if not item_path.startswith(os.path.abspath(target_dir) + os.sep):
            raise ValueError(f"Potential path traversal attack! Blocked: {item_path}")
        return item_path