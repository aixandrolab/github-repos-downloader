# --------------------------------------------------------
# Licensed under the terms of the BSD 3-Clause License
# (see LICENSE for details).
# Copyright © 2025, Alexander Suvorov
# All rights reserved.
# --------------------------------------------------------
# https://github.com/aixadrolab/
# --------------------------------------------------------
import os
from typing import Dict


class BackupReporter:
    @staticmethod
    def _generate_item_report(
            item_type: str,
            icon: str,
            data: Dict[str, str],
            failed_items: Dict[str, str],
            max_errors_to_show: int = 3
    ) -> list:
        report_lines = []
        total = len(data)
        success = total - len(failed_items)
        status = "✅" if not failed_items else "⚠️"

        report_lines.append(f"║ {icon} {item_type.capitalize()}: {success}/{total} downloaded {status}")

        if failed_items:
            report_lines.append(f"║ Failed {item_type}:")
            for item_name in list(failed_items.keys())[:max_errors_to_show]:
                shortened_name = f"{item_name[:40]}..." if len(item_name) > 40 else item_name
                report_lines.append(f"║   - {shortened_name}")

            if len(failed_items) > max_errors_to_show:
                report_lines.append(f"║   + {len(failed_items) - max_errors_to_show} more...")

        return report_lines

    @staticmethod
    def generate(
            download_repos: bool,
            repos_data: Dict[str, str],
            failed_repos: Dict[str, str],
            backup_path: str
    ) -> str:
        try:
            failed_repos = failed_repos or {}
            repos_data = repos_data or {}

            report = []

            if download_repos:
                report.extend(
                    BackupReporter._generate_item_report(
                        item_type="repos",
                        icon="📦",
                        data=repos_data,
                        failed_items=failed_repos
                    )
                )

            return "\n".join(report)

        except Exception as e:
            return f"\n⚠️ Error generating report: {e}\n"