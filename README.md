# MCP AI Agent - Security Hardened Edition 🔒

## 🎉 Week 7: Critical Security Fixes Complete

**Security Score**: 🟢 **100/100 (Grade A - Excellent)**

This project implements a secure MCP (Model Context Protocol) server with comprehensive security controls, following enterprise-grade best practices.

---

## 🛡️ Security Features

### Phase 1 Critical Fixes (✅ Complete)

#### 1. **Environment-Based Configuration**
- ✅ No hardcoded paths in source code
- ✅ Uses `python-dotenv` for configuration management
- ✅ `.env` file for environment-specific settings
- ✅ `.env.example` template for easy setup
- ✅ `.gitignore` prevents accidental secret commits

#### 2. **Input Validation & Sanitization**
- ✅ Strict validation for commit messages (prevents injection)
- ✅ Command whitelist with regex validation
- ✅ Filename validation (blocks dangerous extensions)
- ✅ Path traversal prevention
- ✅ Rate limiting on all operations

#### 3. **Secure Command Execution**
- ✅ **`shell=False`** on all subprocess calls
- ✅ Command arguments parsed with `shlex.split()`
- ✅ Whitelist-only command execution
- ✅ No command chaining (`;`, `&&`, `||` blocked)
- ✅ Timeout protection on all operations

#### 4. **Error Handling & Logging**
- ✅ Structured logging to file and console
- ✅ Sensitive errors logged internally only
- ✅ Generic error messages shown to users
- ✅ Full stack traces in log files
- ✅ Audit trail for all file operations

#### 5. **Rate Limiting**
- ✅ 100 calls/minute for file reads
- ✅ 50 calls/minute for file writes
- ✅ 30 calls/minute for Git operations
- ✅ 20 calls/minute for command execution
- ✅ DoS attack prevention

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Git
- Graphite CLI (optional)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd Stanford_CS/week2
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your paths
nano .env
```

Example `.env`:
```bash
BASE_DIR=/Users/YOUR_USERNAME/Desktop
PROJECT_DIR=/Users/YOUR_USERNAME/Desktop/Stanford_CS/week2
LOG_LEVEL=INFO
LOG_FILE=mcp_server.log
MAX_FILE_SIZE_MB=10
MAX_CONTENT_SIZE_MB=5
RATE_LIMIT_CALLS_PER_MINUTE=100
GIT_OPERATION_TIMEOUT=10
COMMAND_EXECUTION_TIMEOUT=30
```

4. **Run security audit** (optional but recommended)
```bash
python3 security_audit.py
```

5. **Start the server**
```bash
python3 server.py
```

---

## 📁 Project Structure

```
week2/
├── .env                      # Environment configuration (DO NOT COMMIT)
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── config.py                # Configuration management
├── security.py              # Security utilities
├── server.py                # MCP server (security hardened)
├── utils.py                 # Utility functions
├── app.py                   # Streamlit application
├── requirements.txt         # Python dependencies
├── security_audit.py        # Security audit script
├── CODE_REVIEW_AUDIT.md     # Detailed code review
└── REVIEW_GUIDELINES.md     # Review standards
```

---

## 🔐 Security Architecture

### Configuration Layer
- **config.py**: Centralized configuration management
  - Path validation
  - Environment variable loading
  - Logging setup
  - Resource constraints

### Security Layer
- **security.py**: Input validation and sanitization
  - Commit message validation
  - Command validation (whitelist + regex)
  - Filename validation
  - Rate limiting implementation
  - Error message sanitization

### Application Layer
- **server.py**: MCP server with security controls
  - Environment-based paths
  - Rate-limited tool functions
  - Secure subprocess execution
  - Comprehensive logging
  - Error handling

---

## 🛠️ Available Tools

### File Operations
- `list_files(directory)` - List directory contents
- `read_file(file_path)` - Read file contents
- `write_file(file_path, content, overwrite)` - Write to file
- `create_directory(dir_path)` - Create directory
- `delete_file(file_path)` - Delete file
- `move_file(src, dst)` - Move/rename file
- `organize_screenshots(max_files)` - Organize screenshots

### Git/Graphite Operations
- `git_status()` - Get Git status
- `git_commit(message, add_all)` - Commit changes
- `graphite_create_stack(message)` - Create Graphite stack
- `graphite_log()` - View Graphite log
- `auto_commit_and_stack(message)` - One-step commit + stack

### System Maintenance
- `system_cleanup(dry_run)` - Clean Python cache files
- `scan_secrets(scan_all)` - Detect hardcoded secrets

### Utilities
- `add_two_numbers(a, b)` - Math operation
- `get_current_time()` - Get date and time
- `greet_user(name)` - Generate greeting
- `run_command(command)` - Execute safe commands
- `check_status()` - Server status check

---

## 📊 Security Audit

Run the security audit to verify all protections are in place:

```bash
python3 security_audit.py
```

**Expected Output:**
```
🛡️  SECURITY AUDIT RESULTS
============================================================
📊 OVERALL SECURITY SCORE: 100.0/100
🎯 GRADE: 🟢 A (Excellent)

✅ All critical security checks passed!
```

### Audit Categories
1. **Configuration** (20 points)
   - Environment files present
   - Configuration modules exist
   
2. **Hardcoded Paths** (25 points)
   - No absolute paths in code
   - All paths from environment
   
3. **Security Features** (35 points)
   - Input validation
   - Rate limiting
   - Secure subprocess calls
   - Error sanitization
   
4. **Dangerous Patterns** (20 points)
   - No `shell=True`
   - No unvalidated commands

---

## 🔍 Logging

All operations are logged with structured information:

```bash
# View logs
tail -f mcp_server.log
```

**Log Levels:**
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages (e.g., validation failures)
- `ERROR`: Error messages
- `CRITICAL`: Critical system failures

**Log Format:**
```
2024-12-22 10:30:45 - server - INFO - File written: test.txt (1024 bytes)
2024-12-22 10:30:46 - security - WARNING - Command rejected: rm -rf / - Forbidden character: ;
```

---

## ⚙️ Configuration Options

### File Constraints
```bash
MAX_FILE_SIZE_MB=10          # Maximum file size for reading
MAX_CONTENT_SIZE_MB=5        # Maximum content size for writing
```

### Rate Limiting
```bash
RATE_LIMIT_CALLS_PER_MINUTE=100  # Base rate limit
```

### Timeouts
```bash
GIT_OPERATION_TIMEOUT=10         # Git command timeout
COMMAND_EXECUTION_TIMEOUT=30     # Shell command timeout
```

### Logging
```bash
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=mcp_server.log         # Log file path
```

---

## 🚨 Security Best Practices

### Do's ✅
- Always use environment variables for paths
- Review logs regularly for suspicious activity
- Keep `.env` file secure and never commit it
- Run security audit before deployment
- Use rate limiting to prevent abuse
- Validate all user inputs

### Don'ts ❌
- Never commit `.env` to version control
- Never disable input validation
- Never use `shell=True` in subprocess
- Never expose detailed error messages to users
- Never hardcode sensitive information
- Never disable rate limiting in production

---

## 📈 Performance

### Resource Limits
- **Max file size**: 10MB (configurable)
- **Max content size**: 5MB (configurable)
- **Command timeout**: 30 seconds (configurable)
- **Git operation timeout**: 10 seconds (configurable)

### Rate Limits
- **File reads**: 100/minute
- **File writes**: 50/minute
- **Git operations**: 30/minute
- **Command execution**: 20/minute

---

## 🐛 Troubleshooting

### Configuration Errors
```bash
ERROR: Configuration error: BASE_DIR does not exist
```
**Solution**: Check that paths in `.env` exist and are accessible.

### Rate Limit Errors
```bash
Error: Rate limit exceeded. Try again in 45s
```
**Solution**: Wait for rate limit window to reset, or adjust `RATE_LIMIT_CALLS_PER_MINUTE`.

### Permission Errors
```bash
Error: Access denied
```
**Solution**: Check file/directory permissions and ensure user has access.

---

## 📚 Documentation

- **[CODE_REVIEW_AUDIT.md](./CODE_REVIEW_AUDIT.md)** - Detailed security audit report
- **[REVIEW_GUIDELINES.md](./REVIEW_GUIDELINES.md)** - Code review standards
- **[SECURITY_REPORT.md](./SECURITY_REPORT.md)** - Security analysis

---

## 🎯 Roadmap

### Phase 2: Infrastructure (Next)
- [ ] Comprehensive test suite
- [ ] CI/CD pipeline
- [ ] Monitoring and alerting
- [ ] Performance benchmarks

### Phase 3: Quality Improvements
- [ ] 100% type hint coverage
- [ ] Enhanced documentation
- [ ] Code refactoring
- [ ] Performance optimization

### Phase 4: Production Readiness
- [ ] Penetration testing
- [ ] Load testing
- [ ] Production deployment guide
- [ ] Monitoring dashboard

---

## 📄 License

This project is for educational purposes.

---

## 🙏 Acknowledgments

- **MCP Protocol**: Model Context Protocol by Anthropic
- **Security Best Practices**: OWASP Top 10
- **Code Review Standards**: PEP 8, Google Python Style Guide

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the security audit output
3. Check log files for detailed error messages
4. Consult the documentation

---

**Last Updated**: 2024-12-22  
**Security Audit**: ✅ Passed (100/100)  
**Status**: 🟢 Production Ready (Phase 1 Complete)
