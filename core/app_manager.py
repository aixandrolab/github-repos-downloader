import os
import signal
import sys
from utils.managers.auth_manager import GithubAuthManager
from utils.config import Config
from utils.managers.archive_manager import ArchiveManager
from utils.managers.args_manager import ArgumentsManager
from utils.managers.config_file_manager import ConfigPathManager
from utils.managers.directory_manager import DirectoryManager
from utils.managers.gists_manager import GistsManager
from utils.managers.repo_manager import RepositoriesManager
from utils.managers.report_manager import QualityReportManager
from utils.managers.system_action_manager import SystemActionManager
from utils.printers import SmartPrinter
from utils.managers.token_manager import TokenManager


class AppManager:
    
    def __init__(self):
        self.printer = SmartPrinter()
        self.config = Config()
        self.args_manager = None
        self.token_manager = None
        self.github_client = None
        self.repo_manager = None
        self.gists_manager = None
        self.report_manager = None
        self.archive_manager = None
        self.system_action_manager = None

    def _signal_handler(self, signum, frame):
        _ = signum, frame
        print(f"\n\n🛑 Received Ctrl+C - exiting immediately\n")
        self._show_footer()
        os._exit(1)
    
    def run(self):
        signal.signal(signal.SIGINT, self._signal_handler)
        self._show_header()

        print('Arguments parse...')
        args_manager_status = self._parse_args()

        if not args_manager_status:
            print('❌ Error! No arguments found...')
            self._exit()

        config_file = self._create_config()

        if not config_file:
            print('❌ Error creating configuration...')
            self._exit()
        
        print(f"\nConfiguration directory: {config_file}")

        self.token_manager = TokenManager(config_file)

        token = self._get_token()

        if not token:
            print('❌ Failed to get token')
            self._exit()
        
        print('Token obtained successfully!')

        if self.args_manager.args.token:
            self._update_token()
        
        timeout = self.args_manager.args.timeout or 30

        token_verify_success, github_client = self._token_verify(token, timeout, 3)

        github_login = github_client.login if github_client else False

        if not all([token_verify_success, github_client]):
            print('Failed to authenticate via GitHub')
            choice = input('Want to update your token? [y/n]: ')
            if choice == 'y':
                self.token_manager.delete_config()
                self.token_manager.get_token()
                print('\nToken updated successfully!')
                print('Rebooting app')
            else:
                print('\nShutting down')
            self._exit()
        
        print(f'Authentication as {github_client.login}')

        self.github_client = github_client

        create_dirs_status = self._create_backup_dirs()

        if not create_dirs_status:
            print(f"❌ Failed to create backup directory")
            self._exit()

        print(f"📁 Main backup directory: {self.dir_manager.backup_path}")

        if self.args_manager.args.repos:
            print("   ✅ repositories/")

        if self.args_manager.args.gists:
            print("   ✅ gists/")
        
        if self.args_manager.args.repos:
            repo_manager_status = self._download_repositories(
                self.github_client,
                self.dir_manager.repo_path
            )

            if not repo_manager_status:
                print(f"❌ Error cloning repositories!\n")
        
        if self.args_manager.args.gists:
            gists_manager_status = self._download_gists(
                self.github_client,
                self.dir_manager.gists_path
            )

            if not gists_manager_status:
                print(f"❌ Error cloning gists!\n")
        
        report_status = self._get_report()

        if not report_status:
            print('❌ Generating backup report error!')

        if not self.args_manager.args.no_archive:
            archive_status = self._create_archive()
            if not archive_status:
                print("❌ Archive creation error!")
        
        if self.args_manager.args.shutdown or self.args_manager.args.reboot:
            system_action_status = self._start_system_actions()
            if not system_action_status:
                print("❌ System action error!")

        self._show_footer()
    
    def _start_system_actions(self):
        print("\n⚡ System Actions: ")
        print("Executing system actions (shutdown/reboot)")
        self.system_action_manager = SystemActionManager(
            shutdown_flag=self.args_manager.args.shutdown,
            reboot_flag=self.args_manager.args.reboot
        )
        return self.system_action_manager.execute()

    def _create_archive(self):
        print("\nCreate Archive... ")
        self.archive_manager = ArchiveManager(
            backup_path=self.dir_manager.backup_path,
            github_login=self.github_client.login
        )
        return self.archive_manager.execute()

    def _get_report(self):
        print("\nCreate full report... ")
        self.report_manager = QualityReportManager(
            github_client=self.github_client,
            backup_path=self.dir_manager.backup_path,
            failed_repos=self.repo_manager.failed_repos if self.repo_manager else {},
            failed_gists=self.gists_manager.failed_gists if self.gists_manager else {},
            repo_flag=self.args_manager.args.repos,
            gists_flag=self.args_manager.args.gists,
            timeout=30
        )
        return self.report_manager.execute()

    def _download_gists(self, github_client, target_dir):
        print("\nDownloading gists: ")
        self.gists_manager = GistsManager(
            github_client=github_client,
            target_dir=target_dir,
            verbose=self.args_manager.args.verbose
        )
        return self.gists_manager.execute()

    def _download_repositories(self, github_client, target_dir):
        print("\nDownloading repositories: ")
        self.repo_manager = RepositoriesManager(
            github_client=github_client,
            target_dir=target_dir,
            verbose=self.args_manager.args.verbose
        )
        return self.repo_manager.execute()

    def _create_backup_dirs(self):
        print("\nPrepare backup directories... ")
        self.dir_manager = DirectoryManager(
            github_login=self.github_client.login
        )
        status = self.dir_manager.run()
        return status
    
    @staticmethod
    def _token_verify(token, timeout, max_retries):
        print("\n🔑 GitHub Authentication: ")
        print("Authenticating with GitHub...")
        success, github_client = GithubAuthManager.token_verify(token, timeout, max_retries)
        return success, github_client

    def _update_token(self):
        print('\nUpdate your GitHub token: ')
        print('WARNING! Old token will be completely deleted!\n')
        choice = input('Update token [y/n]: ')
        if choice == 'y':
            self.token_manager.delete_config()
            self.token_manager.get_token()
        self._exit()

    def _get_token(self):
        print('\nGet GitHub token...')
        token = self.token_manager.get_token()
        return token
    
    def _create_config(self):
        print('\nCreate/Check config file: ')
        config_file = ConfigPathManager.config_exists()
        return config_file

    def _parse_args(self):
        print('\nParse Arguments: ')
        self.args_manager = ArgumentsManager()
        args = self.args_manager.args

        if not any([args.repos, args.gists, args.token]):
            self.args_manager.parser.print_usage()
            print("\n❌ Error: Choose one of this arguments (-r or -g or -t)")
            return False

        print("\nParsed arguments:")

        backup_items = []
        if args.repos: backup_items.append("📦 Repositories")
        if args.gists: backup_items.append("📝 Gists")
        if not args.no_archive: backup_items.append("🗄 Archive")

        print(f"   Backup: {', '.join(backup_items)}")
        print(f"   Timeout: {args.timeout}s")
        print(f"   Verbose: {'✅ Enabled' if args.verbose else '❌ Disabled'}")

        if args.shutdown:
            print("   Shutdown: ✅ After completion")
        elif args.reboot:
            print("   Reboot: ✅ After completion")
        else:
            print("   Power: ❌ No action")
        return True
    
    def _exit(self):
        self._show_footer()
        sys.exit(0)

    def _show_header(self):
        self.printer.show_head(text=self.config.name)
        self.printer.print_center()
        print()

    def _show_footer(self):
        self.printer.print_center()
        self.printer.show_footer(
            url=self.config.url,
            copyright_=self.config.info
        )

    