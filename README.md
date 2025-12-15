# GitHub Repository Backup Tool <sup>v0.2.1</sup>

A powerful Python utility for automating comprehensive backups of your GitHub repositories and gists. This tool downloads your code as `.zip` archives for safe keeping, with parallel processing for speed and detailed reporting for insight.

---

## ✨ Key Features

*   **Complete Backup**: Downloads all your GitHub repositories and gists as `.zip` archives in a single operation.
*   **Parallel Downloads**: Speeds up the process by downloading multiple items simultaneously, automatically using your available CPU cores.
*   **Detailed Reporting**: Generates a quality report with success rates, sizes, and actionable insights after each backup.
*   **System Automation**: Optionally schedules your computer to shut down or reboot after the backup completes.
*   **Robust Error Handling**: Implements retry logic, handles network timeouts, and protects against failed downloads.
*   **Secure Token Management**: Stores your GitHub token securely in your system's configuration directory.

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.7+**
- **`curl` command-line tool** (used for efficient downloads)
- **GitHub Personal Access Token** with `repo` and `gist` scopes

### Installation & First Run

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/aixandrolab/github-repos-downloader.git
    cd github-repos-downloader
    ```

2.  **Configure your GitHub Token**:
    The first time you run the tool, you need to set up your token. Follow these steps to create it on GitHub:
    1.  Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens).
    2.  Click **"Generate new token (classic)"**.
    3.  Name it (e.g., "Backup Tool"), set **Expiration** to "No expiration" (recommended), and select the **`repo`** and **`gist`** scopes.
    4.  Click **"Generate token"** and copy it immediately.

3.  **Run the tool to save your token**:
    ```bash
    python app.py -t
    ```
    You will be prompted to paste your token. It will be saved securely for future use.

### Basic Usage Examples

| Command | Action |
| :--- | :--- |
| `python app.py -r` | Download all your **repositories**. |
| `python app.py -g` | Download all your **gists**. |
| `python app.py -r -g` | Download both repositories **and** gists. |
| `python app.py -r --verbose` | Download repos with detailed, step-by-step output. |
| `python app.py -r --timeout 120` | Download repos with a 2-minute timeout per request. |
| `python app.py -r --shutdown` | Download repos and **shutdown the computer** when done. |

## 📂 Understanding the Backup Process

### What Gets Backed Up?
The tool creates snapshot `.zip` archives of your code. **Important**: These archives contain the code at a specific point in time but do not include the full Git history.

*   **Repositories**: Saved as `[repository-name].zip` in the `repositories/` folder.
*   **Gists**: Saved as `[gist-id].zip` in the `gists/` folder.

### Where Are Files Saved?
Your backups are organized in a dedicated folder in your home directory:
```
~/[your_github_username]_github_downloads/
├── repositories/
│   ├── project-one.zip
│   └── project-two.zip
├── gists/
│   ├── a1b2c3d4.zip
│   └── e5f6g7h8.zip
└── reports/
    └── backup_report_20251215_143022.txt
```

### Post-Backup Archiving
By default, after downloading, the entire `github_downloads` folder is compressed into a single `.zip` file (e.g., `github_downloads_alex_2025-12-15_14_30_22.zip`) and saved to your home directory. Use the `--no-archive` flag to skip this step.

## ⚙️ Command Line Reference

| Argument | Description | Default |
| :--- | :--- | :--- |
| `-r`, `--repos` | Download your repositories. | `False` |
| `-g`, `--gists` | Download your gists. | `False` |
| `-t`, `--token` | Update or set your stored GitHub token. | `False` |
| `--no-archive` | Do **not** create a final `.zip` archive of the backup folder. | `False` (archive is created) |
| `--timeout N` | Set the timeout (in seconds) for each download operation. | `30` |
| `--verbose` | Print detailed, real-time information about the download process. | `False` |
| `--shutdown` | Shutdown the computer 60 seconds after the backup finishes. | `False` |
| `--reboot` | Reboot the computer 60 seconds after the backup finishes. | `False` |

**Note:** The `--shutdown` and `--reboot` flags are mutually exclusive.

## 🔧 Advanced Usage & Performance

### Optimizing Download Speed
The tool automatically uses parallel processing for batches larger than 5 items. The number of parallel workers is set to your **CPU cores minus one** for optimal performance.

*   **For large backups (50+ items)**: Use a higher timeout to prevent failures: `--timeout 120`
*   **For maximum performance**: Combine flags: `python app.py -r -g --timeout 180`

### Handling API Rate Limits
The tool respects GitHub's API rate limits. Authenticated users have a limit of 5,000 requests per hour, which is typically sufficient for backup operations. If you encounter rate limits:
1.  The tool will automatically pause and retry using an exponential backoff strategy.
2.  You can reduce the number of parallel workers by modifying the `max_workers` parameter in the manager classes if needed.

### Troubleshooting Common Issues

| Problem | Likely Cause | Solution |
| :--- | :--- | :--- |
| **"Failed to authenticate via GitHub"** | Token is invalid, expired, or lacks correct scopes. | 1. Run `python app.py -t` to update the token. <br> 2. Ensure the token has `repo` and `gist` scopes. |
| **"Download timeout"** | Network is slow or repository is very large. | Re-run with a higher timeout: `--timeout 120`. |
| **Some items fail to download** | Repository may be renamed, deleted, or is a fork of a deleted repo. | Check the generated report for a list of failures. Failed items are retried automatically up to 3 times. |
| **"curl" command not found** | The `curl` tool is not installed on your system. | Install `curl` using your system's package manager (e.g., `apt install curl` on Ubuntu). |

## 📊 Understanding the Quality Report
After each run, a detailed report is saved in the `reports/` folder and printed to the console. It includes:
*   **Summary**: Counts of successful/failed downloads for repos and gists.
*   **Statistics**: File sizes and success percentages.
*   **Top Lists**: Your 10 largest repositories and gists with the most files.
*   **Failure Analysis**: A list of items that couldn't be downloaded.
*   **Insights & Recommendations**: Actionable advice based on the backup results.

## 🛡️ Security & Privacy

*   **Token Storage**: Your GitHub token is stored in an encrypted format at `~/.config/github_repos_downloader/github_token.json`.
*   **No Data Sent Elsewhere**: The tool only communicates with GitHub's API. Your code and token never leave your machine.
*   **Clean Operations**: Temporary files are deleted after use, and failed downloads are cleaned up.

## 📄 License & Attribution
This tool is released under the BSD 3-Clause [License](LICENSE). Copyright © 2025, Alexander Suvorov.

---
**For bug reports, feature requests, or contributions**, please visit the project repository: [https://github.com/aixandrolab/github-repos-downloader](https://github.com/aixandrolab/github-repos-downloader).