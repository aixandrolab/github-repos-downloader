# GitHub Repos Downloader <sup>v0.2.0</sup>

## 🚀 Complete GitHub Backup Solution

A powerful, feature-rich tool for comprehensive GitHub backups with parallel downloads, intelligent reporting, and system automation.

## ✨ **What's New in v2.0.0**

- **Parallel Processing**: Download multiple repositories simultaneously using all available CPU cores
- **Smart Archiving**: Create organized backup archives with automatic compression
- **Quality Reports**: Generate detailed analytics with insights and recommendations
- **System Integration**: Automate shutdown/reboot after backup completion
- **Enhanced Reliability**: Advanced retry mechanisms and error handling

## 🎯 **Core Features**

### ✅ **Multi-Core Parallel Downloads**
- Automatically detects CPU cores and uses optimal number of workers
- Parallel processing for both repositories and gists
- Adaptive strategy: sequential for ≤5 items, parallel for larger batches

### ✅ **Intelligent Backup Management**
- Structured directory organization: `~/username_github_downloads/`
- Automatic detection of existing content
- Smart retry logic with configurable attempts
- Progress tracking with real-time updates

### ✅ **Comprehensive Reporting**
- Detailed quality reports with success statistics
- Analytics on repository sizes and update times
- Failure analysis with actionable recommendations
- Multiple report formats: JSON, TXT, and short summaries

### ✅ **System Automation**
- Schedule system shutdown after completion
- Option to reboot system when done
- Graceful handling of interruptions (Ctrl+C)

### ✅ **Security & Reliability**
- Secure token storage with validation
- Protection against path traversal attacks
- File integrity verification (ZIP validation)
- Connection timeout management

## 📋 **System Requirements**

### **Required:**
- Python 3.7+
- `curl` command-line tool
- GitHub personal access token

### **Recommended:**
- 4+ CPU cores for optimal parallel performance
- 2GB+ RAM for large backups
- Stable internet connection

## 🚀 **Quick Start**

### **1. Installation**
```bash
git clone https://github.com/aixandrolab/github-repos-downloader.git
cd github-repos-downloader
```

### **2. GitHub Token Setup**
1. Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Configure token:
   - **Name**: "GitHub Backup Tool"
   - **Expiration**: "No expiration" (recommended)
   - **Scopes**: Select all `repo` and `gist` permissions
4. Copy the generated token

### **3. First Run (Token Configuration)**
```bash
python app.py -t
```
This will prompt you to enter your GitHub token for initial setup.

## 📖 **Complete Usage Guide**

### **Basic Operations**

**Download all repositories:**
```bash
python app.py -r
```

**Download all gists:**
```bash
python app.py -g
```

**Download both repositories and gists:**
```bash
python app.py -r -g
```

### **Advanced Options**

**Verbose mode with detailed logging:**
```bash
python app.py -r --verbose
```

**Download with custom timeout (120 seconds):**
```bash
python app.py -r --timeout 120
```

**Download and create archive:**
```bash
python app.py -r --archive
```

**Download with system shutdown after completion:**
```bash
python app.py -r --shutdown
```

**Download with system reboot:**
```bash
python app.py -r --reboot
```

**Maximum parallel performance:**
```bash
python app.py -r -g --archive --timeout 180
```

### **Command Line Reference**

| Argument | Description | Default | Example |
|----------|-------------|---------|---------|
| `-r, --repos` | Download repositories | False | `-r` |
| `-g, --gists` | Download gists | False | `-g` |
| `-t, --token` | Update GitHub token | False | `-t` |
| `--archive` | Create backup archive | False | `--archive` |
| `--timeout N` | Download timeout in seconds | 30 | `--timeout 90` |
| `--verbose` | Enable verbose output | False | `--verbose` |
| `--shutdown` | Shutdown system after completion | False | `--shutdown` |
| `--reboot` | Reboot system after completion | False | `--reboot` |

## 🏗️ **Project Architecture**

```
github-repos-downloader/
├── app.py                           # Application entry point
├── core/                            # Core application modules
│   ├── app_manager.py               # Main application controller
│   └── github_tools.py              # GitHub API client
├── utils/                           # Utility modules
│   ├── managers/                    # Feature managers
│   │   ├── archive_manager.py       # Archive creation
│   │   ├── args_manager.py          # Arguments parsing
│   │   ├── auth_manager.py          # GitHub Authenticate
│   │   ├── config_file_manager.py   # Config file creation
│   │   ├── directory_manager.py     # Backup directory creation
│   │   ├── gists_manager.py         # Gists downloader
│   │   ├── repo_manager.py          # Repositories downloader
│   │   ├── report_manager.py        # Quality reporting
│   │   ├── system_action_manager.py # System control
│   │   └── token_manager.py         # Create/Check GitHub token
│   ├── archive_creator.py           # Configuration parsers
│   ├── config.py                    # App configuration
│   ├── printers.py                  # Console output
│   └── progress_bar.py              # Progress visualization
```

## 🔄 **How It Works**

### **1. Authentication & Setup**
```
1. Parse command line arguments
2. Load/validate GitHub token
3. Authenticate with GitHub API
4. Create backup directory structure
```

### **2. Intelligent Download Process**
```
1. Fetch repository/gist metadata from GitHub
2. Determine optimal parallel workers (CPU cores - 1)
3. Download archives in parallel batches
4. Validate ZIP file integrity
5. Retry failed downloads automatically
6. Track progress with visual indicators
```

### **3. Post-Processing**
```
1. Generate detailed quality reports
2. Create compressed archive (if requested)
3. Save reports to backup directory
4. Execute system actions (shutdown/reboot)
```

## ⚡ **Performance Optimization**

### **Parallel Processing Strategy**
- **Small batches (≤5 items)**: Sequential processing
- **Large batches**: Parallel with `(CPU cores - 1)` workers
- **Memory efficient**: Streaming downloads, no large in-memory storage
- **Network optimized**: Connection reuse and pipelining

### **Timeout Management**
```bash
# For fast connections and small repositories
--timeout 30

# For slow connections or large repositories
--timeout 120

# For comprehensive backups with archives
--timeout 180
```

### **Memory Usage**
- Downloads stream directly to disk
- Minimal RAM usage (~100-200MB)
- Suitable for systems with limited memory

## 📊 **Reporting System**

### **Generated Reports**

**Quality Report (`backup_report_TIMESTAMP.txt`):**
- Executive summary with success rates
- Top 10 largest repositories
- Recently updated content
- Failure analysis and recommendations
- Performance metrics and duration

**JSON Report (`backup_report_TIMESTAMP.json`):**
- Structured data for programmatic analysis
- Complete statistics in machine-readable format
- Repository/gist details with metadata

**Summary Report (`backup_summary_TIMESTAMP.txt`):**
- Quick overview of backup results
- Success/failure counts
- Backup size and location

### **Report Insights**
```
✅ Success Rate: 95%+
   - Excellent performance
   - Minimal intervention needed

⚠️ Success Rate: 80-95%
   - Good results
   - Check failed items

🔴 Success Rate: <80%
   - Needs attention
   - Review network/token permissions
```

## 🛡️ **Security Features**

### **Token Security**
- Encrypted storage in user config directory
- Validation against GitHub API
- No token logging in verbose mode
- Automatic token update capability

### **File Safety**
- Path traversal protection
- File integrity verification
- Safe temporary file handling
- Cleanup of failed downloads

### **System Protection**
- Graceful interruption handling
- Safe system shutdown/reboot
- Disk space monitoring
- Network failure recovery

## 🔧 **Troubleshooting Guide**

### **Common Issues & Solutions**

**Issue: "Token validation failed"**
```
Solution:
1. Run: python app.py -t (update token)
2. Verify token has required scopes
3. Check token expiration date
```

**Issue: "Download timeout"**
```
Solution:
1. Increase timeout: --timeout 120
2. Check internet connection
3. Verify GitHub API status
```

**Issue: "Incomplete downloads"**
```
Solution:
1. Enable verbose mode: --verbose
2. Check disk space
3. Verify network stability
```

**Issue: "Parallel download errors"**
```
Solution:
1. Reduce workers: modify max_workers parameter
2. Check system resources
3. Monitor network bandwidth
```

### **Debug Commands**
```bash
# Full debug with maximum information
python app.py -r -g --verbose --timeout 180

# Test with small subset
# (Manually limit in code for testing)

# Check system compatibility
python -c "import multiprocessing; print(f'CPU Cores: {multiprocessing.cpu_count()}')"
```

## 📈 **Performance Benchmarks**

### **Typical Performance**
```
Repositories: 50 items
Gists: 20 items
Time: 5-10 minutes
Speed: 5-10 items/minute
```

### **Factors Affecting Performance**
- **Network speed**: Primary bottleneck
- **Repository size**: Large repos take longer
- **CPU cores**: More cores = better parallelism
- **GitHub API rate limits**: 5000 requests/hour

### **Optimization Tips**
```bash
# Optimal for high-speed connections
python app.py -r -g --timeout 60

# For slow connections or large backups
python app.py -r --timeout 180 --archive

# For minimal system impact
python app.py -r --timeout 30
```

## 🤝 **Contributing**

### **Development Setup**
```bash
git clone https://github.com/aixandrolab/github-repos-downloader.git
cd github-repos-downloader
```

### **Contribution Guidelines**
1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

## 📄 **License**

BSD 3-Clause License - See [LICENSE](LICENSE) file for details.


## 📞 **Support & Resources**

### **Getting Help**
- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: This README and code comments
- **Community**: GitHub Discussions

### **Version Compatibility**
```
v2.0.0: Current stable release
v1.x: Legacy version (deprecated)
Future: Regular updates planned
```

---

**Maintainer**: Alexander Suvorov  
**Repository**: https://github.com/aixandrolab/github-repos-downloader  
**Documentation**: https://github.com/aixandrolab/github-repos-downloader/wiki  
**Issues**: https://github.com/aixandrolab/github-repos-downloader/issues  

*Last Updated: December 2025*  
*Version: 2.0.0*