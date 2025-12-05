# --------------------------------------------------------
# Licensed under the terms of the BSD 3-Clause License
# (see LICENSE for details).
# Copyright © 2025, Alexander Suvorov
# All rights reserved.
# --------------------------------------------------------
# https://github.com/aixandrolab/
# --------------------------------------------------------
import os
import multiprocessing
import subprocess
import concurrent.futures
import threading

from utils.progress_bar import ProgressBar


class RepositoriesManager:
    def __init__(self, github_client, target_dir, verbose=False, timeout=30, max_retries=3, max_workers=None):
        self.github_client = github_client
        self.target_dir = target_dir
        self.verbose = verbose
        self.timeout = timeout
        self.max_retries = max_retries
        self.failed_repos = {}
        
        if max_workers is None:
            try:
                cpu_count = multiprocessing.cpu_count()
                self.max_workers = max(1, cpu_count - 1)
            except:
                self.max_workers = 4
        else:
            self.max_workers = max_workers
        
        print(f"🎯 Using {self.max_workers} parallel workers for downloading")

    def execute(self):
        try:
            self.github_client.fetch_repositories(max_retries=self.max_retries, timeout=self.timeout)
            repos_count = len(self.github_client.repositories)
            print(f"✅ Found {repos_count} repositories")

            if repos_count == 0:
                print("⚠️ No repositories to process")
                return True

            self.failed_repos = self._download_items(
                target_dir=self.target_dir,
                items=self.github_client.repositories,
                item_type="repositories",
                timeout=self.timeout,
                verbose=self.verbose
            )
            
            if self.failed_repos:
                print(f"\n❌ Failed to download {len(self.failed_repos)} repositories:")
                for repo in self.failed_repos.keys():
                    print(f"  - {repo}")
            else:
                print(f"\n✅ Successfully downloaded all {repos_count} repositories")
                
        except Exception as e:
            print(f"❌ Error in execute: {e}")
            return False
        return True

    def _download_items(self, target_dir: str, items: dict, item_type: str, timeout: int, verbose: bool) -> dict:
        print(f"\n📦 Processing {len(items)} {item_type}...")

        if len(items) <= 5 or self.max_workers <= 1:
            return self._download_sequentially(target_dir, items, item_type, timeout, verbose)
        else:
            return self._download_parallel(target_dir, items, item_type, timeout, verbose)

    def _download_sequentially(self, target_dir: str, items: dict, item_type: str, timeout: int, verbose: bool) -> dict:
        failed_dict = {}
        failed_count = 0

        if verbose:
            for index, (name, item_data) in enumerate(items.items(), 1):
                print(f"\n{index}/{len(items)} 🔍 Processing: {name}")
                success = self._download_single_archive(name, item_data, target_dir, timeout)
                if not success:
                    failed_dict[name] = item_data.get('archive_url', '')
                    failed_count += 1
        else:
            progress_bar = ProgressBar()
            for index, (name, item_data) in enumerate(items.items(), 1):
                progress_bar.update(index, len(items), failed_count, f"Processing: {name}")
                success = self._download_single_archive(name, item_data, target_dir, timeout)
                if not success:
                    failed_dict[name] = item_data.get('archive_url', '')
                    failed_count += 1

            if not failed_dict:
                progress_bar.finish(f'Downloading {item_type} completed successfully!')

        if failed_dict:
            print(f"\n🔄 Retrying {len(failed_dict)} failed {item_type}...")
            failed_dict = self._retry_failed_items(failed_dict, target_dir, timeout, verbose)

        return failed_dict

    def _download_parallel(self, target_dir: str, items: dict, item_type: str, timeout: int, verbose: bool) -> dict:
        print(f"🚀 Starting parallel download with {self.max_workers} workers...")
        
        failed_dict = {}
        success_count = 0
        lock = threading.Lock()
        progress_lock = threading.Lock()
        
        download_tasks = []
        for name, item_data in items.items():
            download_tasks.append((name, item_data))
        
        if verbose:
            print(f"📋 Total tasks: {len(download_tasks)}")
        
        def download_single(task):
            name, item_data = task
            try:
                success = self._download_single_archive(name, item_data, target_dir, timeout)
                
                with lock:
                    if success:
                        nonlocal success_count
                        success_count += 1
                        if verbose:
                            print(f"✅ Downloaded: {name}")
                        return (name, True)
                    else:
                        failed_dict[name] = item_data.get('archive_url', '')
                        if verbose:
                            print(f"❌ Failed: {name}")
                        return (name, False)
            except Exception as e:
                with lock:
                    failed_dict[name] = item_data.get('archive_url', '')
                    if verbose:
                        print(f"❌ Error downloading {name}: {e}")
                return (name, False)
        
        if not verbose:
            progress_bar = ProgressBar()
            completed = 0
            total_tasks = len(download_tasks)
            
            def update_progress(future):
                nonlocal completed
                with progress_lock:
                    completed += 1
                    progress_bar.update(completed, total_tasks, len(failed_dict), "Downloading...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            if verbose:
                results = list(executor.map(download_single, download_tasks))
            else:
                futures = [executor.submit(download_single, task) for task in download_tasks]
                
                for future in concurrent.futures.as_completed(futures):
                    update_progress(future)
                    future.result()
        
        if not verbose and not failed_dict:
            progress_bar.finish(f'Parallel download completed! {success_count}/{len(items)} successful')
        
        if failed_dict:
            print(f"\n🔄 Retrying {len(failed_dict)} failed {item_type} in parallel...")
            failed_dict = self._retry_failed_items_parallel(failed_dict, target_dir, timeout, verbose)
        
        return failed_dict

    def _retry_failed_items_parallel(self, failed_items: dict, target_dir: str, timeout: int, verbose: bool) -> dict:
        remaining_failed = failed_items.copy()
        
        if not remaining_failed:
            return {}
        
        print(f"\n🔄 Retrying {len(remaining_failed)} failed repositories in parallel...")
        
        for retry_attempt in range(self.max_retries):
            if not remaining_failed:
                break
                
            print(f"\n📋 Parallel retry attempt {retry_attempt + 1}/{self.max_retries}")
            
            current_failed = remaining_failed.copy()
            remaining_failed = {}
            lock = threading.Lock()
            
            def retry_single(task):
                name, url = task
                
                repo_data = self.github_client.repositories.get(name)
                if not repo_data:
                    with lock:
                        remaining_failed[name] = url
                    if verbose:
                        print(f"❌ No data for repository: {name}")
                    return False
                
                success = self._download_single_archive(name, repo_data, target_dir, timeout)
                
                if not success:
                    with lock:
                        remaining_failed[name] = url
                    if verbose:
                        print(f"⚠️ Still failed after retry: {name}")
                elif verbose:
                    print(f"✅ Successfully downloaded on retry: {name}")
                
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
                        progress_bar.update(completed, len(retry_tasks), len(remaining_failed), "Retrying...")
                    
                    futures = [executor.submit(retry_single, task) for task in retry_tasks]
                    for future in concurrent.futures.as_completed(futures):
                        update_retry_progress(future)
                        future.result()
            
            if remaining_failed:
                print(f"⚠️ Still {len(remaining_failed)} repositories failed after parallel retry {retry_attempt + 1}")
            else:
                print(f"✅ All repositories successfully downloaded after parallel retry {retry_attempt + 1}")
                break
        
        return remaining_failed

    def _download_single_archive(self, name: str, item_data: dict, target_dir: str, timeout: int) -> bool:
        try:
            clean_name = name.split('/')[-1] if '/' in name else name
            file_path = os.path.join(target_dir, f"{clean_name}.zip")
            
            if '/' in name:
                full_repo_name = name
            else:
                full_repo_name = f"{self.github_client.login}/{name}"
            
            if hasattr(self.github_client, 'token') and self.github_client.token:
                url = f"https://{self.github_client.token}@github.com/{full_repo_name}/archive/refs/heads/main.zip"
            else:
                url = f"https://github.com/{full_repo_name}/archive/refs/heads/main.zip"
            
            if self.verbose:
                print(f"🎯 URL: {url}")
                print(f"📁 Saving to: {file_path}")
            
            success = self._download_with_curl(url, file_path, timeout)
            
            if success:
                if self.verbose:
                    print(f"✅ Successfully downloaded: {name}")
                return True
            else:
                if self.verbose:
                    print(f"⚠️ Trying master branch for: {name}")
                
                if hasattr(self.github_client, 'token') and self.github_client.token:
                    url = f"https://{self.github_client.token}@github.com/{full_repo_name}/archive/refs/heads/master.zip"
                else:
                    url = f"https://github.com/{full_repo_name}/archive/refs/heads/master.zip"
                
                success = self._download_with_curl(url, file_path, timeout)
                
                if success:
                    if self.verbose:
                        print(f"✅ Successfully downloaded from master: {name}")
                    return True
                else:
                    if self.verbose:
                        print(f"❌ Failed to download: {name}")
                    return False
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Error downloading {name}: {e}")
            return False

    def _download_with_curl(self, url: str, file_path: str, timeout: int) -> bool:
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
        
        print(f"\n🔄 Retrying {len(remaining_failed)} failed repositories...")
        
        for retry_attempt in range(self.max_retries):
            if not remaining_failed:
                break
                
            print(f"\n📋 Retry attempt {retry_attempt + 1}/{self.max_retries}")
            
            current_failed = remaining_failed.copy()
            remaining_failed = {}
            
            for name, url in current_failed.items():
                if verbose:
                    print(f"🔄 Retrying: {name}")
                
                repo_data = self.github_client.repositories.get(name)
                if not repo_data:
                    if verbose:
                        print(f"❌ No data for repository: {name}")
                    remaining_failed[name] = url
                    continue
                
                success = self._download_single_archive(name, repo_data, target_dir, timeout)
                
                if not success:
                    remaining_failed[name] = url
                elif verbose:
                    print(f"✅ Successfully downloaded on retry: {name}")
            
            if remaining_failed:
                print(f"⚠️ Still {len(remaining_failed)} repositories failed after attempt {retry_attempt + 1}")
        
        return remaining_failed

    def _create_item_path(self, target_dir: str, item_name: str) -> str:
        item_path = os.path.normpath(os.path.join(target_dir, os.path.basename(item_name)))
        if not item_path.startswith(os.path.abspath(target_dir) + os.sep):
            raise ValueError(f"Potential path traversal attack! Blocked: {item_path}")
        return item_path