# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it by:

1. **DO NOT** open a public GitHub issue
2. Email the maintainer directly with details
3. Include steps to reproduce the vulnerability
4. Include the potential impact

You can expect:
- Acknowledgment within 48 hours
- Assessment within 1 week
- A fix released as soon as possible (typically within 2 weeks)

## Security Measures

This project implements the following security measures:

1. **Dependency Management:**
   - Regular dependency updates via Dependabot
   - Automated security vulnerability scanning
   - Immediate patching of critical vulnerabilities

2. **Code Security:**
   - Input validation on all API endpoints
   - File type verification
   - File size limits to prevent DoS attacks
   - Automatic cleanup of temporary files

3. **Deployment Security:**
   - HTTPS-only in production
   - Secure environment variable handling
   - No secrets committed to repository

## Best Practices for Deployment

1. **Enable HTTPS only** in production
2. **Set file upload limits** based on your requirements
3. **Use environment variables** for sensitive configuration
4. **Keep dependencies updated** regularly
5. **Monitor logs** for suspicious activity
6. **Enable rate limiting** if exposed to public internet
7. **Use Azure's built-in security features** (firewall, DDoS protection)

## Known Limitations

- This API processes user-uploaded files - ensure proper security controls in production
- File size limits should be configured based on your server capacity
- Temporary file cleanup runs every 30 minutes - very large volumes may require adjustment
