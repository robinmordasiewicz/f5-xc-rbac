# mTLS Proxy Authentication Research - F5 XC User Sync Tool

## Problem Statement

Remote user testing F5 XC user sync tool reports redirects to OIDC login page when using corporate HTTPS proxy with mTLS client certificates, despite proxy and CA bundle being properly configured.

**Working**: Token-based authentication
**Failing**: mTLS certificate-based authentication through corporate proxy

## Error Analysis

### Error 1: OIDC Redirect (Primary Issue)
```
Error: API error listing users: 400 Bad Request for url:
https://login.ves.volterra.io/auth/realms/capitalone-mtnhdpat/protocol/openid-connect/auth
```

**Environment**:
- HTTPS_PROXY=http://crtproxy.kdc.capitalone.com:8099
- HTTP_PROXY=http://crtproxy.kdc.capitalone.com:8099
- REQUESTS_CA_BUNDLE=/Users/olg982/certs/capitalone.crt

**Behavior**: Redirected to OIDC login despite mTLS certificates configured

### Error 2: Alternative Proxy Certificate Expiry
```
Error: HTTPSConnectionPool(host='capitalone.console.ves.volterra.io', port=443):
Max retries exceeded with url: /api/web/custom/namespaces/system/user_roles
(Caused by SSLError(SSLCertVerificationError(1,
'[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired')))
```

**Environment**: Using different corporate proxy (proxy-onprem-nlb-us-east-1.cof-prd-bacloudproxy.aws.cb4good.com:8099)

**Behavior**: Proper certificate validation (confirms proxy works), but certificate expired

## Root Cause: Corporate HTTPS Proxy TLS Termination

### The Fundamental Problem

Corporate HTTPS proxies that perform TLS termination/inspection **cannot pass mTLS client certificates** to the destination server. This is a fundamental architectural limitation:

1. **TLS Handshake Separation**:
   - Client ↔ Proxy: First TLS handshake (with MITM cert)
   - Proxy ↔ Server: Second TLS handshake (re-encrypted)

2. **Certificate Stripping**:
   - Proxy terminates original TLS connection
   - Client certificate presented to proxy, not destination server
   - Proxy cannot forward client cert (lacks matching private key)
   - Cannot create new cert (won't be trusted by server)

3. **OIDC Fallback Behavior**:
   - F5 XC API expects mTLS client certificate
   - No certificate received → authentication fails
   - System redirects to OIDC login page as fallback

### Why Token Authentication Works

Token-based auth uses HTTP Authorization header:
- Header passes through proxy unchanged
- No TLS-layer authentication required
- Works with TLS terminating proxies

## Technical Background

### Python Requests Library Limitations

**Challenge with Multiple Certificate Contexts**:
- Python `requests` library uses single `cert` parameter
- Cannot specify different certs for proxy vs destination
- When proxy requires client cert AND destination requires different client cert, only first cert is used
- Documented limitation in `requests`/`urllib3` architecture

**CONNECT Tunnel Behavior**:
- HTTP CONNECT creates tunnel through proxy
- TLS handshake occurs between client and destination server
- No TLS handshake between client and proxy for tunneled connections
- Client cert presented directly to destination (if no TLS termination)

### Corporate Proxy TLS Inspection

**How MitM Proxies Work**:
1. Client initiates HTTPS connection
2. Proxy intercepts, presents its own certificate (signed by corporate CA)
3. Client validates proxy cert using REQUESTS_CA_BUNDLE
4. Proxy establishes separate connection to destination
5. Proxy decrypts, inspects, re-encrypts traffic

**What Breaks**:
- mTLS client authentication occurs in TLS handshake
- Proxy termination means client cert never reaches destination
- Application data headers (like Authorization) pass through
- TLS-layer authentication cannot pass through

## Solutions and Workarounds

### Solution 1: Token-Based Authentication (Recommended)
**Status**: Already working for this user

**Advantages**:
- Works through TLS terminating proxies
- No certificate management complexity
- Compatible with corporate environments

**Implementation**: Use API tokens instead of P12 certificates

### Solution 2: TLS Passthrough Proxy Configuration
**Status**: Requires corporate IT involvement

**Requirements**:
- Configure proxy to NOT terminate TLS for F5 XC domains
- Use TCP-level routing (no inspection) for specific destinations
- Preserves end-to-end TLS and client certificates

**Domains to Whitelist**:
- `*.ves.volterra.io`
- `*.console.ves.volterra.io`
- F5 XC tenant-specific domains

**Challenges**:
- Corporate security policies may prevent TLS passthrough
- Defeats purpose of corporate proxy inspection
- Requires security approval and proxy reconfiguration

### Solution 3: Direct Connection Bypass
**Status**: May violate corporate policy

**Options**:
- VPN to network segment without proxy requirement
- Run from cloud environment (AWS, as user mentioned)
- Use network that doesn't enforce proxy

**Recommended Approach**:
- Productionize tool in AWS or cloud environment
- Avoids corporate proxy entirely
- No Byzantine proxy configuration issues

### Solution 4: Custom HTTP Adapter (Advanced)
**Status**: Experimental, complex implementation

**Concept**:
- Create custom `HTTPAdapter` for `requests`
- Manage separate SSL contexts for proxy vs destination
- Configure `proxy_ssl_context` in `urllib3.ProxyManager`

**Limitations**:
- Still cannot work with TLS terminating proxies
- Only helps with TLS passthrough proxies requiring separate auth
- Complex to implement and maintain

## Recommendations

### Immediate/Short-term
1. **Use token-based authentication** (already working)
   - Sufficient for current workstation testing
   - Compatible with corporate proxy environment

### Medium-term
2. **Request proxy TLS passthrough** for F5 XC domains
   - Work with corporate IT/security
   - Explain mTLS requirement for API authentication
   - Provide specific domain whitelist

### Long-term (Production)
3. **Deploy to cloud environment** (AWS/Azure/GCP)
   - User already mentioned this approach
   - Avoids corporate proxy entirely
   - Production deployment best practice
   - No workstation configuration complexity

### Not Recommended
- ❌ Custom SSL context implementations (too complex, won't fix root cause)
- ❌ Disabling SSL verification (security risk)
- ❌ Alternative unapproved proxies (policy violation)

## Additional Context

### F5 XC API Authentication
- Supports both mTLS (P12 certificates) and token-based auth
- mTLS provides stronger security via mutual authentication
- Tokens use one-way TLS with Authorization header

### User's Current State
- ✅ Token authentication: Working
- ❌ mTLS authentication: Failing (OIDC redirect)
- 🎯 Production plan: Deploy to AWS (will avoid proxy issues)

## References

### Technical Documentation
- Python requests library mTLS limitations with proxies
- Corporate proxy TLS termination and client certificate stripping
- OIDC authentication redirect behavior with failed mTLS
- F5 Distributed Cloud API authentication methods

### Key Insights
1. Corporate HTTPS proxies performing TLS termination **fundamentally cannot** pass mTLS client certificates
2. This is architectural limitation, not configuration issue
3. Token-based authentication is appropriate workaround
4. Production deployment in cloud environment is best long-term solution
