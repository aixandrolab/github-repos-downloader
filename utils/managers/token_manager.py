

import datetime
import getpass
import json
import re


class TokenManager:

    def __init__(self, config_file):
        self.config_file = config_file

    def get_token(self):
        token = self._load_token()

        if token:
            return token
        
        return self._request_valid_token()
    
    def _load_token(self):
        try:
            if not self.config_file.exists():
                return None

            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            token = config.get('github_token', '').strip()
            return token if token and self._validate_token(token) else None

        except Exception as e:
            print(e)
            return None
    
    def _request_valid_token(self):
        while True:
            try:
                token = getpass.getpass("Enter your GItHub token: ").strip()

                if not token:
                    print('Token cannot be empty!\n')
                    continue

                if not self._validate_token(token):
                    print("Invalid token format!\n")
                    continue

                if self._save_token(token):
                    return token
                else:
                    print("Failed to save token!\n")
                    return None
            except KeyboardInterrupt:
                print("\nOperation was canceled...\n")
                return None
            except Exception as e:
                print(e)
                return None
    
    def _save_token(self, token):
        try:
            config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding="utf-8") as f:
                    json.load(f)
            
            config['github_token'] = token
            config['created_at'] = datetime.datetime.now().isoformat()

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            
            return True

        except Exception as e:
            print(e)
            return None
    
    @staticmethod
    def _validate_token(token):
        pattern = r'^[a-zA-Z0-9_-]{10,}$'
        return bool(token and re.match(pattern, token))
    
    def delete_config(self):
        try:
            if not self.config_file.exists():
                print('Config file does not exist...')
                return True

            self.config_file.unlink()
            print("Config file was successfully deleted!")
            return True
        
        except Exception as e:
            print(e)
            return False