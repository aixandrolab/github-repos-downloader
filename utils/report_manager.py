# --------------------------------------------------------
# Licensed under the terms of the BSD 3-Clause License
# (see LICENSE for details).
# Copyright © 2025, Alexander Suvorov
# All rights reserved.
# --------------------------------------------------------
# https://github.com/aixandrolab/
# --------------------------------------------------------
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BackupStats:
    total_repos: int = 0
    successful_repos: int = 0
    failed_repos: int = 0
    total_gists: int = 0
    successful_gists: int = 0
    failed_gists: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    backup_size: str = "0 B"
    backup_path: str = ""
    repo_flag: bool = False
    gists_flag: bool = False
    parallel_workers: int = 0
    download_timeout: int = 0
    timeout: int = 30


class QualityReportManager:
    def __init__(self, github_client, backup_path: str, 
                 failed_repos: Dict, failed_gists: Dict,
                 repo_flag: bool = False, gists_flag: bool = False,
                 parallel_workers: int = 0, timeout: int = 30):
        self.github_client = github_client
        self.backup_path = backup_path
        self.failed_repos = failed_repos or {}
        self.failed_gists = failed_gists or {}
        self.repo_flag = repo_flag
        self.gists_flag = gists_flag
        self.parallel_workers = parallel_workers
        self.timeout = timeout
        self.start_time = datetime.now()
        
        self.repo_details = []
        self.gist_details = []
        
    def execute(self) -> Tuple[bool, str]:
        try:
            end_time = datetime.now()
            
            stats = self._collect_stats(end_time)
            
            report = self._generate_detailed_report(stats)
            
            self._save_report_to_file(report, stats)
            
            print("\n" + "="*80)
            print(report)
            print("="*80 + "\n")
            
            self._print_summary(stats)
            
            success = stats.failed_repos == 0 and stats.failed_gists == 0
            return success, report
            
        except Exception as e:
            error_report = self._generate_error_report(str(e))
            print("\n" + "="*80)
            print(error_report)
            print("="*80 + "\n")
            return False, error_report
    
    def _collect_stats(self, end_time: datetime) -> BackupStats:
        stats = BackupStats()
        
        stats.start_time = self.start_time
        stats.end_time = end_time
        
        stats.backup_path = self.backup_path
        stats.backup_size = self._calculate_backup_size()
        
        stats.repo_flag = self.repo_flag
        stats.gists_flag = self.gists_flag
        
        stats.parallel_workers = self.parallel_workers
        stats.download_timeout = self.timeout
        
        if self.repo_flag and hasattr(self.github_client, 'repositories'):
            repos = self.github_client.repositories
            stats.total_repos = len(repos)
            stats.failed_repos = len(self.failed_repos)
            stats.successful_repos = stats.total_repos - stats.failed_repos
            
            for name, data in repos.items():
                status = "❌" if name in self.failed_repos else "✅"
                size = self._get_repo_size(name)
                last_updated = data.get('pushed_at', 'Unknown') if isinstance(data, dict) else 'Unknown'
                self.repo_details.append({
                    'name': name,
                    'status': status,
                    'size': size,
                    'last_updated': last_updated,
                    'url': data.get('html_url', '') if isinstance(data, dict) else name
                })
        
        if self.gists_flag and hasattr(self.github_client, 'gists'):
            gists = self.github_client.gists
            stats.total_gists = len(gists)
            stats.failed_gists = len(self.failed_gists)
            stats.successful_gists = stats.total_gists - stats.failed_gists
            
            for gist_id, data in gists.items():
                status = "❌" if gist_id in self.failed_gists else "✅"
                files = []
                if isinstance(data, dict):
                    files = list(data.get('files', {}).keys())
                self.gist_details.append({
                    'id': gist_id,
                    'status': status,
                    'files': files[:3],
                    'file_count': len(files),
                    'url': data.get('html_url', '') if isinstance(data, dict) else f"https://gist.github.com/{gist_id}"
                })
        
        return stats
    
    def _generate_detailed_report(self, stats: BackupStats) -> str:
        report_lines = []
        
        report_lines.append("📊 QUALITY GITHUB BACKUP REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        report_lines.append("📋 OPERATIONS SUMMARY")
        report_lines.append("-" * 40)
        operations = []
        if stats.repo_flag:
            operations.append(f"📦 Repositories: {stats.total_repos} total")
        if stats.gists_flag:
            operations.append(f"💾 Gists: {stats.total_gists} total")
        
        if operations:
            report_lines.extend(operations)
        else:
            report_lines.append("⚠️ No operations performed")
        report_lines.append(f"💾 Backup location: {stats.backup_path}")
        report_lines.append(f"📁 Backup size: {stats.backup_size}")
        report_lines.append("")
        
        if stats.repo_flag and stats.total_repos > 0:
            report_lines.append("📦 REPOSITORIES DETAILS")
            report_lines.append("-" * 40)
            report_lines.append(f"Total:      {stats.total_repos}")
            report_lines.append(f"Successful: {stats.successful_repos} ({(stats.successful_repos/stats.total_repos*100):.1f}%)")
            report_lines.append(f"Failed:     {stats.failed_repos} ({(stats.failed_repos/stats.total_repos*100):.1f}%)")
            report_lines.append("")
            
            if self.repo_details:
                report_lines.append("🏆 TOP 10 LARGEST REPOSITORIES:")
                sorted_repos = sorted(self.repo_details, 
                                     key=lambda x: self._parse_size(x['size']), 
                                     reverse=True)[:10]
                for i, repo in enumerate(sorted_repos, 1):
                    report_lines.append(f"  {i:2d}. {repo['status']} {repo['name'][:40]:40s} {repo['size']:>10s}")
            report_lines.append("")
            
            if self.repo_details:
                report_lines.append("🕐 RECENTLY UPDATED:")
                repos_with_date = [r for r in self.repo_details if r['last_updated'] != 'Unknown']
                if repos_with_date:
                    try:
                        repos_with_date.sort(key=lambda x: x['last_updated'], reverse=True)
                        for i, repo in enumerate(repos_with_date[:5], 1):
                            report_lines.append(f"  {i:2d}. {repo['status']} {repo['name'][:40]:40s} {repo['last_updated'][:10]}")
                    except:
                        pass
            report_lines.append("")
        
        if stats.gists_flag and stats.total_gists > 0:
            report_lines.append("💾 GISTS DETAILS")
            report_lines.append("-" * 40)
            report_lines.append(f"Total:      {stats.total_gists}")
            report_lines.append(f"Successful: {stats.successful_gists} ({(stats.successful_gists/stats.total_gists*100):.1f}%)")
            report_lines.append(f"Failed:     {stats.failed_gists} ({(stats.failed_gists/stats.total_gists*100):.1f}%)")
            report_lines.append("")
            
            if self.gist_details:
                report_lines.append("📄 GISTS WITH MOST FILES:")
                sorted_gists = sorted(self.gist_details, 
                                     key=lambda x: x['file_count'], 
                                     reverse=True)[:10]
                for i, gist in enumerate(sorted_gists, 1):
                    files_preview = ', '.join(gist['files'][:3])
                    if gist['file_count'] > 3:
                        files_preview += f"... (+{gist['file_count']-3})"
                    report_lines.append(f"  {i:2d}. {gist['status']} {gist['id'][:20]:20s} {gist['file_count']:3d} files")
            report_lines.append("")
        
        if stats.failed_repos > 0 or stats.failed_gists > 0:
            report_lines.append("❌ FAILED ITEMS")
            report_lines.append("-" * 40)
            
            if stats.failed_repos > 0:
                report_lines.append("Failed repositories:")
                failed_repos_list = list(self.failed_repos.keys())
                for i, repo in enumerate(failed_repos_list[:10], 1):
                    report_lines.append(f"  {i:2d}. 🔴 {repo}")
                if len(failed_repos_list) > 10:
                    report_lines.append(f"     ... and {len(failed_repos_list)-10} more")
                report_lines.append("")
            
            if stats.failed_gists > 0:
                report_lines.append("Failed gists:")
                failed_gists_list = list(self.failed_gists.keys())
                for i, gist in enumerate(failed_gists_list[:10], 1):
                    report_lines.append(f"  {i:2d}. 🔴 {gist}")
                if len(failed_gists_list) > 10:
                    report_lines.append(f"     ... and {len(failed_gists_list)-10} more")
                report_lines.append("")
        
        report_lines.append("💡 INSIGHTS & RECOMMENDATIONS")
        report_lines.append("-" * 40)
        
        insights = []
        
        total_items = stats.total_repos + stats.total_gists
        failed_items = stats.failed_repos + stats.failed_gists
        success_rate = ((total_items - failed_items) / total_items * 100) if total_items > 0 else 100
        
        if success_rate == 100:
            insights.append("🎉 PERFECT SUCCESS! All items downloaded successfully.")
        elif success_rate >= 95:
            insights.append("✅ EXCELLENT! Almost all items downloaded successfully.")
        elif success_rate >= 80:
            insights.append("⚠️ GOOD, but some items failed. Consider checking:")
        else:
            insights.append("❌ POOR SUCCESS RATE. Issues detected:")
        
        if stats.failed_repos > 0:
            insights.append(f"  • {stats.failed_repos} repositories failed - check URLs and permissions")
        if stats.failed_gists > 0:
            insights.append(f"  • {stats.failed_gists} gists failed - gists may be private or deleted")
        
        if stats.parallel_workers <= 1:
            insights.append("  • Consider increasing parallel workers for faster downloads")
        if stats.timeout < 60 and total_items > 50:
            insights.append("  • Consider increasing timeout for large downloads")
        
        if not insights:
            insights.append("• No issues detected. Backup completed successfully!")
        
        report_lines.extend(insights)
        report_lines.append("")
        
        report_lines.append("=" * 60)
        report_lines.append("📋 Report saved to: reports/backup_report.json")
        report_lines.append(f"📊 Success rate: {success_rate:.1f}%")
        report_lines.append("✅ Quality report completed")
        
        return "\n".join(report_lines)
    
    def _print_summary(self, stats: BackupStats):
        print("\n" + "✨ " + "="*70 + " ✨")
        print("📋 BACKUP SUMMARY")
        print("-" * 70)
        
        if stats.repo_flag:
            repo_status = "✅ ALL SUCCESS" if stats.failed_repos == 0 else f"⚠️  {stats.failed_repos} FAILED"
            print(f"📦 Repositories: {stats.successful_repos}/{stats.total_repos} {repo_status}")
        
        if stats.gists_flag:
            gist_status = "✅ ALL SUCCESS" if stats.failed_gists == 0 else f"⚠️  {stats.failed_gists} FAILED"
            print(f"💾 Gists: {stats.successful_gists}/{stats.total_gists} {gist_status}")
        
        print(f"💾 Size: {stats.backup_size}")
        
        print(f"📁 Location: {stats.backup_path}")
            
    def _save_report_to_file(self, report: str, stats: BackupStats):
        try:
            reports_dir = Path(self.backup_path) / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            json_report = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "backup_path": str(self.backup_path),
                    "backup_size": stats.backup_size,
                    "parallel_workers": stats.parallel_workers,
                    "timeout": stats.timeout,
                    "duration": str(stats.end_time - stats.start_time) if stats.start_time and stats.end_time else None
                },
                "statistics": {
                    "repositories": {
                        "total": stats.total_repos,
                        "successful": stats.successful_repos,
                        "failed": stats.failed_repos,
                        "success_rate": (stats.successful_repos/stats.total_repos*100) if stats.total_repos > 0 else 0
                    },
                    "gists": {
                        "total": stats.total_gists,
                        "successful": stats.successful_gists,
                        "failed": stats.failed_gists,
                        "success_rate": (stats.successful_gists/stats.total_gists*100) if stats.total_gists > 0 else 0
                    }
                },
                "failed_items": {
                    "repositories": list(self.failed_repos.keys()),
                    "gists": list(self.failed_gists.keys())
                },
                "repository_details": self.repo_details,
                "gist_details": self.gist_details
            }
            
            json_file = reports_dir / f"backup_report_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_report, f, indent=2, ensure_ascii=False)
            
            txt_file = reports_dir / f"backup_report_{timestamp}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            short_report = self._generate_short_report(stats)
            short_file = reports_dir / f"backup_summary_{timestamp}.txt"
            with open(short_file, 'w', encoding='utf-8') as f:
                f.write(short_report)
                
            print(f"📄 Reports saved to: {reports_dir}/")
            
        except Exception as e:
            print(f"⚠️ Could not save report to file: {e}")
    
    def _generate_short_report(self, stats: BackupStats) -> str:
        lines = []
        lines.append("GitHub Backup Summary")
        lines.append("=" * 40)
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        
        if stats.repo_flag:
            lines.append(f"Repositories: {stats.successful_repos}/{stats.total_repos} ({stats.successful_repos/stats.total_repos*100:.0f}%)")
        
        if stats.gists_flag:
            lines.append(f"Gists: {stats.successful_gists}/{stats.total_gists} ({stats.successful_gists/stats.total_gists*100:.0f}%)")
        
        lines.append(f"Size: {stats.backup_size}")
        lines.append(f"Location: {stats.backup_path}")
        lines.append("")
        
        if stats.failed_repos > 0 or stats.failed_gists > 0:
            lines.append("Failed items:")
            if stats.failed_repos > 0:
                lines.append(f"  • Repositories: {stats.failed_repos}")
            if stats.failed_gists > 0:
                lines.append(f"  • Gists: {stats.failed_gists}")
        
        return "\n".join(lines)
    
    def _generate_error_report(self, error: str) -> str:
        lines = []
        lines.append("❌ BACKUP ERROR REPORT")
        lines.append("=" * 60)
        lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Error: {error}")
        lines.append("")
        lines.append("🔧 TROUBLESHOOTING:")
        lines.append("  • Check GitHub token validity and permissions")
        lines.append("  • Verify internet connection")
        lines.append("  • Ensure sufficient disk space")
        lines.append("  • Check GitHub API rate limits")
        lines.append("  • Try running with --verbose flag for details")
        lines.append("")
        lines.append("💡 For assistance, include this report in your issue.")
        return "\n".join(lines)
    
    def _calculate_backup_size(self) -> str:
        try:
            if not os.path.exists(self.backup_path):
                return "0 B"
            
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(self.backup_path):
                if 'reports' in dirnames:
                    dirnames.remove('reports')
                
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if total_size < 1024.0:
                    return f"{total_size:.1f} {unit}"
                total_size /= 1024.0
            return f"{total_size:.1f} PB"
            
        except Exception:
            return "Unknown"
    
    def _get_repo_size(self, repo_name: str) -> str:
        try:
            repo_path = Path(self.backup_path) / "repositories" / f"{repo_name.split('/')[-1]}.zip"
            if repo_path.exists():
                size = repo_path.stat().st_size
                for unit in ['B', 'KB', 'MB']:
                    if size < 1024.0:
                        return f"{size:.1f} {unit}"
                    size /= 1024.0
                return f"{size:.1f} GB"
        except:
            pass
        return "Unknown"
    
    def _parse_size(self, size_str: str) -> float:
        try:
            if size_str == "Unknown":
                return 0
            value, unit = size_str.split()
            value = float(value)
            unit = unit.upper()
            if unit == 'KB':
                return value * 1024
            elif unit == 'MB':
                return value * 1024 * 1024
            elif unit == 'GB':
                return value * 1024 * 1024 * 1024
            else:
                return value
        except:
            return 0