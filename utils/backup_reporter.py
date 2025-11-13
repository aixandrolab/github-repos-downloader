# --------------------------------------------------------
# Licensed under the terms of the BSD 3-Clause License
# (see LICENSE for details).
# Copyright © 2025, Alexander Suvorov
# All rights reserved.
# --------------------------------------------------------
# https://github.com/aixandrolab/
# --------------------------------------------------------
from datetime import datetime
from typing import Dict, List, Optional
import os


class BackupReporter:
    
    @staticmethod
    def generate(
        download_repos: bool = False,
        download_gists: bool = False,
        make_archive: bool = False,
        repos_data: Optional[Dict] = None,
        gists_data: Optional[Dict] = None,
        failed_repos: Optional[Dict] = None,
        failed_gists: Optional[Dict] = None,
        backup_path: str = "",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> str:
        repos_data = repos_data or {}
        gists_data = gists_data or {}
        failed_repos = failed_repos or {}
        failed_gists = failed_gists or {}
        
        total_repos = len(repos_data)
        total_gists = len(gists_data)
        successful_repos = total_repos - len(failed_repos)
        successful_gists = total_gists - len(failed_gists)
        
        execution_time = ""
        if start_time and end_time:
            duration = end_time - start_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            execution_time = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        
        backup_size = BackupReporter._calculate_backup_size(backup_path)
        
        report_lines = []
        
        report_lines.append("📊 GITHUB BACKUP REPORT")
        report_lines.append("=" * 50)
        report_lines.append("")
        
        report_lines.append("📋 SUMMARY")
        report_lines.append("-" * 30)
        report_lines.append(f"Backup location: {backup_path}")
        report_lines.append(f"Backup size: {backup_size}")
        if execution_time:
            report_lines.append(f"Execution time: {execution_time}")
        report_lines.append(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        report_lines.append("🔄 OPERATIONS PERFORMED")
        report_lines.append("-" * 30)
        operations = []
        if download_repos:
            operations.append("✅ Repository download")
        if download_gists:
            operations.append("✅ Gists download")
        if make_archive:
            operations.append("✅ Archive creation")
        
        if operations:
            report_lines.extend(operations)
        else:
            report_lines.append("❌ No operations performed")
        report_lines.append("")
        
        if download_repos and repos_data:
            report_lines.append("📦 REPOSITORIES")
            report_lines.append("-" * 30)
            report_lines.append(f"Total found: {total_repos}")
            report_lines.append(f"Successfully downloaded: {successful_repos}")
            report_lines.append(f"Failed: {len(failed_repos)}")
            report_lines.append(f"Success rate: {(successful_repos/total_repos*100) if total_repos > 0 else 0:.1f}%")
            report_lines.append("")
            
            if repos_data:
                report_lines.append("Top repositories:")
                for i, (repo_name, repo_url) in enumerate(list(repos_data.items())[:10]):
                    status = "❌" if repo_name in failed_repos else "✅"
                    report_lines.append(f"  {status} {repo_name}")
                if total_repos > 10:
                    report_lines.append(f"  ... and {total_repos - 10} more")
            report_lines.append("")
        
        if download_gists and gists_data:
            report_lines.append("💾 GISTS")
            report_lines.append("-" * 30)
            report_lines.append(f"Total found: {total_gists}")
            report_lines.append(f"Successfully downloaded: {successful_gists}")
            report_lines.append(f"Failed: {len(failed_gists)}")
            report_lines.append(f"Success rate: {(successful_gists/total_gists*100) if total_gists > 0 else 0:.1f}%")
            report_lines.append("")
            
            if gists_data:
                report_lines.append("Recent gists:")
                for i, (gist_id, gist_url) in enumerate(list(gists_data.items())[:10]):
                    status = "❌" if gist_id in failed_gists else "✅"
                    report_lines.append(f"  {status} {gist_id}")
                if total_gists > 10:
                    report_lines.append(f"  ... and {total_gists - 10} more")
            report_lines.append("")
        
        if failed_repos or failed_gists:
            report_lines.append("❌ FAILED ITEMS")
            report_lines.append("-" * 30)
            
            if failed_repos:
                report_lines.append("Failed repositories:")
                for repo_name, error in list(failed_repos.items())[:5]:
                    error_msg = error if isinstance(error, str) else "Download failed"
                    report_lines.append(f"  🔴 {repo_name}: {error_msg}")
                if len(failed_repos) > 5:
                    report_lines.append(f"  ... and {len(failed_repos) - 5} more repository failures")
                report_lines.append("")
            
            if failed_gists:
                report_lines.append("Failed gists:")
                for gist_id, error in list(failed_gists.items())[:5]:
                    error_msg = error if isinstance(error, str) else "Download failed"
                    report_lines.append(f"  🔴 {gist_id}: {error_msg}")
                if len(failed_gists) > 5:
                    report_lines.append(f"  ... and {len(failed_gists) - 5} more gist failures")
            report_lines.append("")
        
        report_lines.append("💡 RECOMMENDATIONS")
        report_lines.append("-" * 30)
        
        recommendations = []
        if failed_repos:
            recommendations.append("• Check internet connection for failed repository downloads")
        if failed_gists:
            recommendations.append("• Verify gist access permissions")
        if not download_repos and not download_gists:
            recommendations.append("• Use -r flag to download repositories")
            recommendations.append("• Use -g flag to download gists")
        
        if recommendations:
            report_lines.extend(recommendations)
        else:
            report_lines.append("• All operations completed successfully!")
        
        report_lines.append("")
        report_lines.append("=" * 50)
        report_lines.append("✅ Backup report completed")
        
        return "\n".join(report_lines)
    
    @staticmethod
    def _calculate_backup_size(backup_path: str) -> str:
        try:
            if not os.path.exists(backup_path):
                return "0 B"
            
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(backup_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            
            for unit in ['B', 'KB', 'MB', 'GB']:
                if total_size < 1024.0:
                    return f"{total_size:.1f} {unit}"
                total_size /= 1024.0
            return f"{total_size:.1f} TB"
            
        except Exception:
            return "Unknown"
    
    @staticmethod
    def generate_short_report(
        successful_repos: int,
        failed_repos: int,
        successful_gists: int,
        failed_gists: int,
        backup_path: str
    ) -> str:
        return f"""
🔄 BACKUP COMPLETED
────────────────────
📦 Repositories: {successful_repos} ✅ | {failed_repos} ❌
💾 Gists: {successful_gists} ✅ | {failed_gists} ❌
📁 Location: {backup_path}
        """.strip()
    
    @staticmethod
    def generate_error_report(error: str, operation: str = "") -> str:
        report_lines = [
            "❌ BACKUP ERROR",
            "─" * 30,
            f"Operation: {operation or 'Unknown'}",
            f"Error: {error}",
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "💡 Troubleshooting:",
            "• Check GitHub token validity",
            "• Verify internet connection",
            "• Ensure sufficient disk space",
            "• Check GitHub API rate limits"
        ]
        return "\n".join(report_lines)