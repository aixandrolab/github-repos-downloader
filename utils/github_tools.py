# --------------------------------------------------------
# Licensed under the terms of the BSD 3-Clause License
# (see LICENSE for details).
# Copyright © 2025, Alexander Suvorov
# All rights reserved.
# --------------------------------------------------------
# https://github.com/aixandrolab/
# --------------------------------------------------------
import time
from typing import Optional
import urllib.request
import urllib.error
import json


class GitHubDataMaster:
    def __init__(self, token=None):
        self._token = token
        self.login = None
        self.repositories = {}

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token):
        self._token = token

    @property
    def headers(self) -> dict:
        return {'Authorization': f'token {self._token}'}
    
    def _make_request_with_retry(self, url: str, max_retries: int = 3, timeout: int = 30) -> Optional[dict]:
        retries = 0

        while retries < max_retries:
            current_retry = retries + 1
            print(f"   🔄 Attempt {current_retry}/{max_retries} (timeout: {timeout}s)...", end=' ')

            req = urllib.request.Request(url, headers=self.headers)
            try:
                start_time = time.time()
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    request_time = time.time() - start_time

                    if response.status == 200:
                        print(f"✅ ({request_time:.1f}s)")
                        data = json.loads(response.read().decode('utf-8'))
                        return data
                    else:
                        print(f"❌ HTTP {response.status}")
                        raise Exception(f"Error: {response.status}")

            except urllib.error.HTTPError as e:
                print(f"❌ HTTP {e.code}")
                if e.code == 401:
                    return None
            except urllib.error.URLError as e:
                print(f"❌ Network: {e.reason}")
            except Exception as e:
                print(f"❌ Error: {str(e)}")

            retries += 1
            if retries < max_retries:
                wait_time = 2 ** retries
                print(f"   ⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)

        print(f"❌ Max retries ({max_retries}) reached")
        return None

    def fetch_user_data(self, max_retries: int = 3, timeout: int = 30) -> bool:
        url = "https://api.github.com/user"
        data = self._make_request_with_retry(url, max_retries, timeout)

        if data:
            self.login = data.get('login')
            return True
        return False

    def fetch_repositories(self, max_retries=3, timeout=30):
        url = "https://api.github.com/user/repos"
        self.repositories = self._fetch_data(url, is_repo=True, max_retries=max_retries)

    def fetch_gists(self, max_retries=5, timeout=30):
        url = "https://api.github.com/gists"
        self.gists = self._fetch_data(url, is_repo=False, max_retries=max_retries)

    def _fetch_data(self, url: str, is_repo: bool, max_retries=3) -> dict:
        data_dict = {}
        page = 1
        per_page = 100

        while True:
            retries = 0
            while retries < max_retries:
                paginated_url = f"{url}?page={page}&per_page={per_page}"
                req = urllib.request.Request(paginated_url, headers=self.headers)
                try:
                    with urllib.request.urlopen(req) as response:
                        if response.status == 200:
                            data = json.loads(response.read().decode('utf-8'))
                            if not data:
                                return data_dict
                            for item in data:
                                if is_repo:
                                    data_dict[item['full_name']] = {
                                        'ssh_url': item['ssh_url'],
                                        'archive_url': item['archive_url'],
                                        'updated_at': item['updated_at']
                                    }
                                else:
                                    data_dict[item['id']] = {
                                        'git_pull_url': item['git_pull_url'],
                                        'updated_at': item['updated_at']
                                    }
                            page += 1
                            break
                        else:
                            raise Exception(f"Error: {response.status} - {response.read().decode('utf-8')}")
                except urllib.error.HTTPError as e:
                    print(f"⚠️ HTTP error occurred: {e.code} - {e.reason}")
                except urllib.error.URLError as e:
                    print(f"⚠️ URL error occurred: {e.reason}")
                except Exception as e:
                    print(f"⚠️ An unexpected error occurred: {str(e)}")

                retries += 1
                if retries < max_retries:
                    print()
                    print(f"✅ Retrying... ({retries}/{max_retries})")
                    print()
                    time.sleep(2)

            if retries == max_retries:
                print("⚠️ Max retries reached. Failed to fetch data.")
                return data_dict

    def is_token_valid(self, max_retries=5) -> bool:
        url = "https://api.github.com/user"
        retries = 0

        while retries < max_retries:
            req = urllib.request.Request(url, headers=self.headers)
            try:
                with urllib.request.urlopen(req) as response:
                    return response.status == 200
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    return False
                print(f"⚠️ HTTP error occurred: {e.code} - {e.reason}")
            except urllib.error.URLError as e:
                print(f"⚠️ URL error occurred: {e.reason}")
            except Exception as e:
                print(f"⚠️ An unexpected error occurred: {str(e)}")

            retries += 1
            if retries < max_retries:
                print()
                print(f"✅ Retrying... ({retries}/{max_retries})")
                print()
                time.sleep(2)

        print("⚠️ Max retries reached. Failed to validate token.")
        return False