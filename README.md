# GitHub Repos Backup Tools

A comprehensive solution for backing up GitHub repositories and gists with full automation.

## 🚀 Features

- ✅ Download all user repositories (public and private)
- ✅ Automatic archive creation of downloaded files
- ✅ GitHub token authentication
- ✅ Progress tracking and detailed reporting
- ✅ Support for shutdown/reboot after completion
- ✅ Cross-platform compatibility (Windows, Linux, macOS)

## 📋 Requirements

- Python 3.7+
- `curl` command-line tool
- GitHub personal access token

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/aixandrolab/github-repos-downloader.git
cd github-repos-downloader
```

### 2. Create Configuration File
Create `.config.ini` in the project root:

```ini
[github]
token = your_github_personal_access_token_here
```

### 3. Get GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token" → "Generate new token (classic)"
3. Set token name: "GitHub Backup Tool"
4. Set expiration: "No expiration" (recommended for backups)
5. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `gists` (Full control of gists)
   - ✅ `read:org` (Read org permissions)
   - ✅ `read:user` (Read user profile data)

6. Click "Generate token"
7. Copy the token and paste it in `.config.ini`

## 🛠️ Usage

### Basic Commands

**Download all repositories:**
```bash
python main.py -r
```

**Download all gists:**
```bash
python main.py -g
```

**Verbose mode with detailed output:**
```bash
python main.py -r --verbose
```

**Download with auto-shutdown:**
```bash
python main.py -r --shutdown
```

**Download with auto-reboot:**
```bash
python main.py -r --reboot
```

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `-r` | Download repositories | False |
| `--shutdown` | Shutdown after completion | False |
| `--reboot` | Reboot after completion | False |
| `--verbose` | Enable verbose output | False |
| `--timeout N` | Download timeout in seconds | 60 |

## 📁 Project Structure

```
github-repos-backup-tools/
├── main.py                 # Main application entry point
├── .config.ini            # Configuration file (create this)
├── utils/
│   ├── __init__.py
│   ├── backup_reporter.py # Report generation
│   ├── config.py          # Configuration management
│   ├── github_tools.py    # GitHub API interactions
│   ├── parsers.py         # Configuration parsing
│   ├── printers.py        # Console output formatting
│   └── progress_bar.py    # Progress visualization
```

## 🔄 How It Works

### 1. Authentication
- Reads GitHub token from `.config.ini`
- Validates token against GitHub API
- Fetches user profile data

### 2. Data Collection
- Retrieves list of all repositories (including private)
- Uses GitHub REST API with proper pagination

### 3. Download Process
- Uses `curl` for reliable file downloads
- Downloads repositories as ZIP archives
- Validates ZIP file integrity
- Retries failed downloads automatically

### 4. File Organization
- Creates structured directory: `~/username_github_downloads/`
- Organizes files into `repositories/`
- Uses clean filenames without usernames

### 5. Archive Creation (Optional)
- Creates compressed archive of all downloaded content
- Uses `.zip`
- Archive named: `github_downloads.zip`

### 6. Reporting
- Generates detailed backup report
- Shows success/failure statistics
- Provides summary of downloaded content

## ⚙️ Configuration Details

### GitHub Token Permissions

The token requires these permissions:
- **repo**: Access to private repositories and download capabilities
- **gists**: Access to gists
- **read:org**: Read organization membership (if applicable)
- **read:user**: Read user profile information

### Timeout Settings

Default timeout is 60 seconds. Adjust based on:
- Network speed: Increase for slow connections
- Repository size: Increase for large repositories
- Number of repositories: Increase for extensive backups

## 🐛 Troubleshooting

### Common Issues

**Token not working:**
- Verify token has correct permissions
- Check token hasn't expired
- Ensure `.config.ini` format is correct

**Download failures:**
- Check internet connection
- Increase timeout with `--timeout 120`
- Use `--verbose` for detailed error messages

**Missing repositories:**
- Verify token has `repo` scope
- Check if repositories are in organizations where you have access

**Permission errors:**
- Ensure write permissions in home directory
- Check available disk space

### Debug Mode

Use verbose mode to see detailed process:
```bash
python main.py -r -g --verbose --timeout 120
```

## 🔒 Security Notes

- Store `.config.ini` securely
- GitHub token should be kept confidential
- Consider using token with expiration for production use
- Backup files contain sensitive code - store securely

## 📄 License

BSD 3-Clause License - See [LICENSE](https://github.com/aixandrolab/github-repos-downloader/blob/master/LICENSE) file for details.

## 👥 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📞 Support

For issues and questions:
- Create GitHub Issue
- Check existing documentation
- Review troubleshooting section

## 🎯 Pro Tips

### Scheduled Backups
```bash
# Add to crontab for daily backups at 2 AM
0 2 * * * cd /path/to/backup-tools && python main.py -r --archive
```

---

**Maintainer:** Alexander Suvorov  
**Repository:** https://github.com/aixadrolab/github-repos-downloader