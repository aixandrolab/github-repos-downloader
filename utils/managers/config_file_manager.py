import datetime
import json
from pathlib import Path


class ConfigPathManager:

    @classmethod
    def get_config_path(cls, dir_name="github_repos_downloader"):
        return Path.home() / ".config" / dir_name / "github_token.json"

    @classmethod
    def config_exists(cls, dir_name="github_repos_downloader"):
        try:
            config_file = cls.get_config_path(dir_name)

            config_file.parent.mkdir(parents=True, exist_ok=True)

            if not config_file.exists():
                cls._create_default_config(config_file)

            return config_file
        except Exception as e:
            print(e)
            return None
    
    @classmethod
    def _create_default_config(cls, config_path):
        default_config = {
            "github_token": "",
            "created_at": datetime.datetime.now().isoformat()
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)