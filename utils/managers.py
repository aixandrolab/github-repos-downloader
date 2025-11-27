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
import argparse
import sys
from typing import Dict
import platform
from datetime import datetime, timezone

from utils.backup_reporter import BackupReporter
from utils.config import Config
from utils.github_tools import GitHubDataMaster
from utils.parsers import ConfigParser
from utils.printers import SmartPrinter
from utils.progress_bar import ProgressBar

import concurrent.futures
import threading


class AppManager:
    def __init__(
            self,
            config=Config(),
            printer=SmartPrinter(),
            config_parser=ConfigParser(),
            github_data_master=GitHubDataMaster(),
            timeout=60
    ):
        self.config = config
        self.printer = printer
        self.config_parser = config_parser
        self.github_data_master = github_data_master
        self.shutdown_flag = False
        self.verbose = False
        self.timeout = timeout

    def graceful_shutdown(self):
        if self.shutdown_flag:
            return
        self.shutdown_flag = True
        print("\n🛑 Shutting down gracefully...")
        self.stop()
        sys.exit(0)

    @staticmethod
    def _parse_arguments():
        parser = argparse.ArgumentParser(description="GitHub Repos Download Tools")
        parser.add_argument("-r", action="store_true", help="Download repositories")
        parser.add_argument("-g", action="store_true", help="Download gists")
        parser.add_argument("--timeout", type=int, default=60,
                            help="Timeout for download operations in seconds (default: 60)", )
        mutex_group = parser.add_mutually_exclusive_group()
        mutex_group.add_argument("--shutdown", action="store_true", help="Shutdown after completion")
        mutex_group.add_argument("--reboot", action="store_true", help="Reboot after completion")
        parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
        return parser.parse_args()

    @staticmethod
    def _create_download_directory(login) -> str:
        home_directory = os.path.expanduser('~')
        download_path = os.path.join(home_directory, f'{login}_github_downloads')
        os.makedirs(download_path, exist_ok=True)
        return download_path

    @staticmethod
    def shutdown():
        print()
        if platform.system() == "Windows":
            os.system("shutdown /s /t 60")
        else:
            os.system("shutdown -h +1")
        print()

    @staticmethod
    def reboot():
        print()
        if platform.system() == "Windows":
            os.system("shutdown /r /t 60")
        else:
            os.system("shutdown -r +1")
        print()

    @staticmethod
    def get_yes_no(arg):
        return '✅' if arg else '⚠️'

    @staticmethod
    def create_item_path(target_dir: str, item_name: str) -> str:
        clean_name = "".join(c for c in item_name if c.isalnum() or c in ('-', '_', '.')).rstrip()
        item_path = os.path.normpath(os.path.join(target_dir, clean_name + ".zip"))
        return item_path

    def _download_with_curl(self, url: str, file_path: str) -> bool:
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if os.path.exists(file_path):
                os.remove(file_path)
            
            cmd = [
                'curl', 
                '-L',
                '-o', file_path,
                '--connect-timeout', '30',
                '--max-time', '60',
                '--retry', '3',
                '--retry-delay', '5',
                '--progress-bar',
                url
            ]
            
            if not self.verbose:
                cmd.remove('--progress-bar')
                cmd.append('--silent')
            else:
                print(f"🔗 Downloading: {url}")
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                if os.path.exists(file_path) and os.path.getsize(file_path) > 100:
                    with open(file_path, 'rb') as f:
                        header = f.read(4)
                        if header == b'PK\x03\x04':
                            if self.verbose:
                                print(f"✅ Valid ZIP downloaded: {os.path.basename(file_path)}")
                            return True
                        else:
                            if self.verbose:
                                print(f"⚠️ File is not a ZIP: {os.path.basename(file_path)}")
                                print(f"File header: {header}")
                            os.remove(file_path)
                            return False
                else:
                    if self.verbose:
                        print(f"⚠️ File is empty or missing: {os.path.basename(file_path)}")
                    return False
            else:
                if self.verbose:
                    print(f"⚠️ Download failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            if self.verbose:
                print(f"⚠️ Download timeout: {os.path.basename(file_path)}")
            return False
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Download error: {str(e)}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return False

    def _get_download_url(self, repo_name: str, repo_data: dict, item_type: str) -> str:
        if item_type == "repositories":
            if '/' in repo_name:
                full_repo_name = repo_name
            else:
                full_repo_name = f"aixandrolab/{repo_name}"
            
            if hasattr(self.github_data_master, 'token') and self.github_data_master.token:
                url = f"https://{self.github_data_master.token}@github.com/{full_repo_name}/archive/master.zip"
            else:
                url = f"https://github.com/{full_repo_name}/archive/master.zip"
            
            if self.verbose:
                print(f"🎯 Using authenticated URL for repository: {full_repo_name}")
            
            return url 
        
        elif item_type == "gists":
            gist_id = repo_name
            
            if hasattr(self.github_data_master, 'token') and self.github_data_master.token:
                url = f"https://{self.github_data_master.token}@gist.github.com/{self.github_data_master.login}/{gist_id}/archive/master.zip"
            else:
                url = f"https://gist.github.com/{self.github_data_master.login}/{gist_id}/archive/master.zip"
            
            if self.verbose:
                print(f"🎯 Using URL for gist: {gist_id}")
            
            return url
        
        return ""

    def _check_url_exists(self, url: str) -> bool:
        try:
            cmd = ['curl', '--head', '--silent', '--fail', '--connect-timeout', '10', url]
            result = subprocess.run(cmd, timeout=10, capture_output=True)
            return result.returncode == 0
        except:
            return False

    def start(self):
        self.printer.show_head(text=self.config.name)
        self.printer.print_center()
        print()
        token = self.config_parser.get_token()
        print(f'Getting a token from a .config.ini file: {self.get_yes_no(token)}\n')

        if not token:
            print("⚠️ ERROR! Please provide GitHub token in the config file.")
            return

        print('Parsing arguments:\n')
        args = self._parse_arguments()
        self.timeout = args.timeout
        print(f'Download operations timeout: {self.timeout} seconds ✅')
        download_repos = args.r
        download_gists = args.g
        exec_shutdown = args.shutdown
        exec_reboot = args.reboot
        self.verbose = args.verbose

        print(f'Download repositories: {self.get_yes_no(download_repos)}')
        print(f'Download gists: {self.get_yes_no(download_gists)}')
        print(f'Shutdown: {self.get_yes_no(exec_shutdown)}')
        print(f'Reboot: {self.get_yes_no(exec_reboot)}')
        print(f'Verbose: {self.get_yes_no(self.verbose)}\n')

        self.github_data_master.token = token
        print(f'Checking the token for validity:')
        is_token_valid = self.github_data_master.is_token_valid()
        print(f'Token is valid: {self.get_yes_no(is_token_valid)}\n')

        if not is_token_valid:
            print('⚠️ Error! Token is not valid.')
            return

        print('Getting user login:')
        self.github_data_master.fetch_user_data()
        login = self.github_data_master.login

        if not login:
            print('⚠️ Login failed.')
            return

        print(f'✅ Login: {login}\n')

        print('Forming a path to the directory:')
        path = self._create_download_directory(login)
        print(f'✅ Path: {path}\n')

        repos_failed = {}
        gists_failed = {}

        if download_repos:
            repos_target_dir = os.path.join(path, "repositories")
            repos_failed = self.download_items(repos_target_dir, self.github_data_master.fetch_repositories, "repositories")

        if download_gists:
            gists_target_dir = os.path.join(path, "gists")
            gists_failed = self.download_items(gists_target_dir, self.github_data_master.fetch_gists, "gists")

        try:
            repos_data_for_report = {}
            if hasattr(self.github_data_master, "repositories"):
                for name, data in self.github_data_master.repositories.items():
                    if isinstance(data, dict):
                        repos_data_for_report[name] = data['ssh_url']
                    else:
                        repos_data_for_report[name] = data

            gists_data_for_report = {}
            if hasattr(self.github_data_master, "gists"):
                for name, data in self.github_data_master.gists.items():
                    if isinstance(data, dict):
                        gists_data_for_report[name] = data.get('git_pull_url', 'N/A')
                    else:
                        gists_data_for_report[name] = data

            report = BackupReporter.generate(
                download_repos=download_repos,
                download_gists=download_gists,
                repos_data=repos_data_for_report,
                gists_data=gists_data_for_report,
                failed_repos=repos_failed,
                failed_gists=gists_failed,
                backup_path=path
            )
            self.printer.print_center(text=' REPORT: ')
            print(report)
        except Exception as e:
            print(f'Report generation failed: {str(e)}')

        if exec_shutdown:
            self.shutdown()
        elif exec_reboot:
            self.reboot()

    def download_items(self, target_dir: str, fetch_method, item_type: str) -> Dict[str, bool]:
        print()
        self.printer.print_center()
        self.printer.print_center(text=f'Downloading {item_type}: ')
        self.printer.print_center()
        print()
        os.makedirs(target_dir, exist_ok=True)
        print(f'Target directory: {target_dir}\n')
        print(f'Getting {item_type}:\n')
        fetch_method()
        items = getattr(self.github_data_master, item_type)
        count = len(items)

        if not count:
            self.printer.print_framed(f'⚠️ No {item_type} found. \n')
            return {}
        else:
            self.printer.print_framed(f'✅ Found {count} {item_type} ')
        print()
        
        failed_dict = {}
        success_count = 0
        skipped_count = 0
        download_tasks = []
        
        if not self.verbose:
            progress_bar = ProgressBar()

        for index, (name, item_data) in enumerate(items.items(), start=1):
            clean_name = name.split('/')[-1] if '/' in name else name
            file_path = self.create_item_path(target_dir, clean_name)
            
            if not self.verbose:
                progress_bar.update(index, count, len(failed_dict), f"Checking: {name}")
            else:
                self.printer.print_framed(f'{index}/{count}/{len(failed_dict)}: Checking: {name}')

            download_url = self._get_download_url(name, item_data, item_type)
            
            if not download_url:
                if self.verbose:
                    print(f"   ⚠️ Could not get download URL for: {name}")
                failed_dict[name] = "No download URL"
                continue

            download_tasks.append((name, download_url, file_path))

        total_to_process = len(download_tasks)
        
        if item_type == "repositories":
            if self.verbose:
                print(f"\n🚀 Starting PARALLEL download of {total_to_process} repositories... (skipped {skipped_count})")
            else:
                print(f"🚀 Starting PARALLEL download of {total_to_process} repositories... (skipped {skipped_count})")
            
            failed_dict = {}
            success_count = 0
            lock = threading.Lock()
            
            def download_single(task):
                name, url, file_path = task
                try:
                    success = self._download_with_curl(url, file_path)
                    
                    with lock:
                        if success:
                            nonlocal success_count
                            success_count += 1
                            if self.verbose:
                                print(f"✅ Downloaded: {name}")
                            return True
                        else:
                            failed_dict[name] = url
                            if self.verbose:
                                print(f"❌ Failed: {name}")
                            return False
                except Exception as e:
                    with lock:
                        failed_dict[name] = url
                        if self.verbose:
                            print(f"❌ Error downloading {name}: {e}")
                    return False

            if not self.verbose:
                progress_bar_parallel = ProgressBar()
                completed = 0
                total_tasks = len(download_tasks)
                
                def update_progress(future):
                    nonlocal completed
                    completed += 1
                    progress_bar_parallel.update(completed, total_tasks, len(failed_dict), "Downloading...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                if self.verbose:
                    results = list(executor.map(download_single, download_tasks))
                else:
                    futures = [executor.submit(download_single, task) for task in download_tasks]
                    for future in concurrent.futures.as_completed(futures):
                        update_progress(future)
                    results = [future.result() for future in futures]
                    
        else:
            if self.verbose:
                print(f"\n🚀 Starting download of {total_to_process} gists... (skipped {skipped_count})")
            else:
                print(f"🚀 Starting download of {total_to_process} gists... (skipped {skipped_count})")

            for index, (name, url, file_path) in enumerate(download_tasks, start=1):
                current_position = skipped_count + index
                
                if not self.verbose:
                    progress_bar.update(current_position, count, len(failed_dict), f"Downloading: {name}")
                else:
                    self.printer.print_framed(f'Downloading {index}/{total_to_process}: {name}')
                    print(f"   📦 Downloading archive...")

                success = self._download_with_curl(url, file_path)

                if success:
                    success_count += 1
                    if self.verbose:
                        print(f"   ✅ Successfully downloaded: {name}")
                        print('-' * 50)
                else:
                    failed_dict[name] = url
                    if self.verbose:
                        print(f"   ❌ Failed to download: {name}")
                        print('-' * 50)

        retry_count = 0
        max_retries = 2
        
        while failed_dict and retry_count < max_retries:
            retry_count += 1
            if self.verbose:
                self.printer.print_center()
                print()
                self.printer.print_framed(f"🔄 Retry attempt {retry_count}/{max_retries}: {len(failed_dict)} {item_type} remaining")
                print()
                self.printer.print_center()
            else:
                print(f"\n🔄 Retry attempt {retry_count}/{max_retries}: {len(failed_dict)} {item_type} remaining")

            current_failed = failed_dict.copy()
            failed_dict.clear()

            if item_type == "repositories":
                def retry_single(task):
                    name, url = task
                    clean_name = name.split('/')[-1] if '/' in name else name
                    file_path = self.create_item_path(target_dir, clean_name)
                    
                    success = self._download_with_curl(url, file_path)
                    
                    with lock:
                        if success:
                            nonlocal success_count
                            success_count += 1
                            if self.verbose:
                                print(f"✅ Successfully downloaded on retry: {name}")
                            return True
                        else:
                            failed_dict[name] = url
                            if self.verbose:
                                print(f"⚠️ Still failed after retry: {name}")
                            return False

                if not self.verbose:
                    progress_bar_retry = ProgressBar()
                    completed_retry = 0
                    
                    def update_retry_progress(future):
                        nonlocal completed_retry
                        completed_retry += 1
                        progress_bar_retry.update(completed_retry, len(current_failed), len(failed_dict), "Retrying...")

                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    if self.verbose:
                        results = list(executor.map(retry_single, current_failed.items()))
                    else:
                        futures = [executor.submit(retry_single, task) for task in current_failed.items()]
                        for future in concurrent.futures.as_completed(futures):
                            update_retry_progress(future)
            else:
                for index, (name, url) in enumerate(current_failed.items(), start=1):
                    current_position = skipped_count + success_count + index
                    
                    if not self.verbose:
                        progress_bar.update(current_position, count, len(failed_dict), f"Retrying: {name}")
                    else:
                        self.printer.print_framed(f'Retry {retry_count}/{max_retries}: {index}/{len(current_failed)}: {name}')

                    clean_name = name.split('/')[-1] if '/' in name else name
                    file_path = self.create_item_path(target_dir, clean_name)

                    success = self._download_with_curl(url, file_path)

                    if success:
                        success_count += 1
                        if self.verbose:
                            print(f"   ✅ Successfully downloaded on retry: {name}")
                    else:
                        failed_dict[name] = url
                        if self.verbose:
                            print(f"   ❌ Still failed after retry: {name}")

            if failed_dict and retry_count < max_retries:
                if self.verbose:
                    print(f"\n⏳ Waiting 5 seconds before next retry...")
                import time
                time.sleep(5)

        if not self.verbose:
            if item_type == "repositories":
                progress_bar_parallel.finish(message=f'Completed {success_count + skipped_count}/{count} {item_type}!')
            else:
                progress_bar.finish(message=f'Completed {success_count + skipped_count}/{count} {item_type}!')

        print(f"\n📊 Final Results: {success_count} downloaded, {skipped_count} skipped, {len(failed_dict)} failed")
        
        if failed_dict:
            print(f"\n❌ Failed {item_type} after {max_retries} retries:")
            for failed_name in failed_dict.keys():
                print(f"   - {failed_name}")
        
        return failed_dict

    def stop(self, shutdown=False):
        self.printer.print_center()
        self.printer.show_footer(url=self.config.url, copyright_=self.config.info)
        if shutdown:
            self.shutdown()

    def run(self):
        try:
            self.start()
            self.stop()
        except KeyboardInterrupt:
            print("\n🛑 Detected Ctrl+C. Shutting down...")
            self.graceful_shutdown()
        except Exception as e:
            print(f"⚠️ An unexpected error occurred: {e}")
            self.graceful_shutdown()
        finally:
            print("\n✅ Application has been terminated. You can now close the console.")
            sys.exit(0)