# 🔒 Security Policy

## 🛡️ Security Overview

Windows Computer Use takes security seriously. **Face recognition is optional** and only exposed when **`WINDOWS_COMPUTER_USE_MCP_ENABLE_FACE=1`** and the **`face`** extra are installed (see **`docs/SAFETY.md` §5**). Core desktop automation does not require it.

## 🚨 Reporting Security Vulnerabilities

If you discover a security vulnerability, please report it responsibly:

### 📧 Contact Information
- **Email**: security@example.com (replace with actual security contact)
- **Response Time**: We aim to respond within 48 hours
- **Disclosure**: We follow responsible disclosure practices

### 📋 What to Include
When reporting a vulnerability, please provide:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fixes (if any)
- Your contact information for follow-up

## 🔐 Security Features

### Face recognition (when enabled)
- **Opt-in**: Runtime flag **`WINDOWS_COMPUTER_USE_MCP_ENABLE_FACE`** plus **`face`** extra — see **`docs/SAFETY.md`**.
- **Encrypted storage**: Face data is stored with strong encryption
- **Local-only**: Intended for local operator-presence workflows; data does not leave the machine by design

### System Security
- **Process Isolation**: Automation operations are sandboxed
- **Input Validation**: All user inputs are validated and sanitized
- **Error Handling**: Secure error messages that don't leak sensitive information

### Network Security
- **Local Only**: By default, server only accepts local connections
- **Authentication**: Optional JWT-based authentication for API endpoints
- **HTTPS Support**: SSL/TLS encryption when configured

## 🛠️ Security Best Practices

### For Users
1. **Run in Virtual Environment**: Use virtual environments to isolate the installation
2. **Limit Permissions**: Run with minimal required Windows permissions
3. **Network Access**: Only expose the server on localhost unless necessary
4. **Regular Updates**: Keep Windows Computer Use and dependencies updated

### For Developers
1. **Code Review**: All changes undergo security review
2. **Dependency Scanning**: Automated vulnerability scanning of dependencies
3. **Input Validation**: Validate all inputs and sanitize outputs
4. **Error Handling**: Implement proper error handling without information leakage

## 🔍 Security Testing

### Automated Security Tests
- Dependency vulnerability scanning
- Static code analysis for security issues
- Input validation testing
- Authentication and authorization testing

### Manual Security Review
- Code review for security implications
- Architecture security assessment
- Penetration testing of exposed endpoints

## 📊 Security Metrics

### Current Security Posture
- **Dependency Vulnerabilities**: Monitored via GitHub Dependabot
- **Code Quality**: Static analysis with security-focused linters
- **Test Coverage**: Security-critical paths have comprehensive test coverage

### Security Updates
- **Critical Updates**: Released within 7 days of discovery
- **Regular Updates**: Security patches included in regular releases
- **Backporting**: Critical fixes backported to supported versions

## 📜 Security-Related Files

### Sensitive Configuration
- `.env` files contain sensitive configuration
- Never commit secrets or credentials
- Use environment variables for sensitive data

### Face Recognition Data
- Stored in `data/known_faces/` directory
- Encrypted using industry-standard algorithms
- Local storage only, no cloud transmission

## 🚫 Prohibited Activities

Windows Computer Use should not be used for:
- Unauthorized access to systems
- Malware or virus creation
- Privacy violations
- Automated attacks or testing without permission
- Any illegal activities

## 📞 Support

For security-related questions or concerns:
- Check existing documentation first
- Review GitHub Issues for similar concerns
- Contact maintainers through appropriate channels

## 🙏 Acknowledgments

Security is a collaborative effort. We appreciate the security research community for their contributions to keeping open source software secure.

---

*This security policy applies to Windows Computer Use and its associated repositories.*
