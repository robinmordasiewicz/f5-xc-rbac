# Software Requirements Specification

## F5 Distributed Cloud User and Group Synchronization Tool

**Document ID**: SRS-XC-SYNC-001
**Version**: 1.0.0
**Date**: 2025-11-13
**Status**: Production-Ready
**Standard Compliance**: ISO/IEC/IEEE 29148:2018

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-13 | System | Initial consolidated production specification |

## Document Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Technical Lead | | | |
| Quality Assurance | | | |

---

## Table of Contents

1. [Introduction](#1-introduction)
   1.1 [Purpose](#11-purpose)
   1.2 [Document Scope](#12-document-scope)
   1.3 [Definitions, Acronyms, and Abbreviations](#13-definitions-acronyms-and-abbreviations)
   1.4 [References](#14-references)
   1.5 [Document Overview](#15-document-overview)

2. [Overall Description](#2-overall-description)
   2.1 [Product Perspective](#21-product-perspective)
   2.2 [Product Functions](#22-product-functions)
   2.3 [User Classes and Characteristics](#23-user-classes-and-characteristics)
   2.4 [Operating Environment](#24-operating-environment)
   2.5 [Design and Implementation Constraints](#25-design-and-implementation-constraints)
   2.6 [Assumptions and Dependencies](#26-assumptions-and-dependencies)

3. [System Features](#3-system-features)
   3.1 [Feature 1: CSV-Driven Group Synchronization](#31-feature-1-csv-driven-group-synchronization)
   3.2 [Feature 2: Configuration and Environment Management](#32-feature-2-configuration-and-environment-management)
   3.3 [Feature 3: Advanced Retry and Backoff Mechanisms](#33-feature-3-advanced-retry-and-backoff-mechanisms)
   3.4 [Feature 4: User Experience and CLI Feedback](#34-feature-4-user-experience-and-cli-feedback)
   3.5 [Feature 5: Credential Setup and CI/CD Integration](#35-feature-5-credential-setup-and-cicd-integration)
   3.6 [Feature 6: Resource Pruning and Reconciliation](#36-feature-6-resource-pruning-and-reconciliation)

4. [External Interface Requirements](#4-external-interface-requirements)
   4.1 [User Interfaces](#41-user-interfaces)
   4.2 [Hardware Interfaces](#42-hardware-interfaces)
   4.3 [Software Interfaces](#43-software-interfaces)
   4.4 [Communications Interfaces](#44-communications-interfaces)

5. [Non-Functional Requirements](#5-non-functional-requirements)
   5.1 [Performance Requirements](#51-performance-requirements)
   5.2 [Safety Requirements](#52-safety-requirements)
   5.3 [Security Requirements](#53-security-requirements)
   5.4 [Software Quality Attributes](#54-software-quality-attributes)

6. [Data Requirements](#6-data-requirements)
   6.1 [Data Model](#61-data-model)
   6.2 [CSV Input Format](#62-csv-input-format)
   6.3 [Data Transformations](#63-data-transformations)
   6.4 [Data Validation Rules](#64-data-validation-rules)

7. [Quality Attributes](#7-quality-attributes)
   7.1 [Testability](#71-testability)
   7.2 [Traceability](#72-traceability)
   7.3 [Maintainability](#73-maintainability)

8. [Appendices](#8-appendices)
   8.1 [Appendix A: API Contract Specification](#81-appendix-a-api-contract-specification)
   8.2 [Appendix B: CSV Format Examples](#82-appendix-b-csv-format-examples)
   8.3 [Appendix C: Glossary](#83-appendix-c-glossary)
   8.4 [Appendix D: Change History](#84-appendix-d-change-history)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) document provides a comprehensive description of the F5 Distributed Cloud User and Group Synchronization Tool (XC Group Sync). The document is intended for:

- **Production Development Teams**: Complete functional and non-functional requirements for implementation
- **Quality Assurance Teams**: Acceptance criteria and verification requirements
- **Operations Teams**: Deployment, configuration, and operational requirements
- **Product Management**: Feature scope and business value validation
- **Security Teams**: Security requirements and compliance verification

This document consolidates all functional requirements, enhancement specifications, and operational requirements into a single authoritative source compliant with ISO/IEC/IEEE 29148:2018 standards.

### 1.2 Document Scope

#### In Scope

This specification covers the complete XC Group Sync tool including:

1. **Core Synchronization Functionality**
   - CSV parsing and validation
   - LDAP Distinguished Name (DN) extraction
   - Group membership reconciliation with F5 XC
   - User auto-creation during group operations
   - Idempotent create/update/delete operations

2. **Configuration Management**
   - Hierarchical environment variable loading
   - Multiple authentication methods (P12, PEM certificates, API tokens)
   - Multi-environment support (production, staging, development)
   - Configuration validation and error handling

3. **Reliability Features**
   - Configurable retry mechanisms with exponential backoff
   - Transient error detection and handling
   - Circuit breaker patterns for sustained failures
   - Atomic operations and rollback capabilities

4. **User Experience**
   - Command-line interface with comprehensive feedback
   - Dry-run mode for safe validation
   - Execution time tracking and performance metrics
   - Structured error reporting and user guidance

5. **Operational Requirements**
   - Credential setup automation
   - CI/CD pipeline integration
   - GitHub Actions workflow support
   - Logging and monitoring capabilities

6. **Resource Management**
   - Optional pruning of orphaned resources
   - Full membership reconciliation
   - Resource lifecycle management

#### Out of Scope

The following capabilities are explicitly excluded from this specification:

1. **Multi-Namespace Operations**: Tool operates exclusively in the`system`namespace
2. **User Management Independent of Groups**: Users are only created/managed as part of group membership
3. **Role and RBAC Management**: Role assignments and permission management are not included
4. **Real-Time Synchronization**: Tool operates in batch mode, not continuous sync
5. **Bidirectional Synchronization**: CSV is the authoritative source; XC changes are not synchronized back
6. **User Interface (Web/GUI)**: Tool is command-line only
7. **Multi-Tenant Operations**: Single tenant per execution
8. **Custom Field Mapping**: Fixed CSV schema, no user-defined field mappings

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|------------|
| **AD** | Active Directory - Microsoft's directory service for Windows domain networks |
| **API** | Application Programming Interface |
| **CA** | Certificate Authority |
| **CI/CD** | Continuous Integration / Continuous Deployment |
| **CLI** | Command Line Interface |
| **CN** | Common Name - component of LDAP Distinguished Name |
| **CSV** | Comma-Separated Values - tabular data format |
| **DN** | Distinguished Name - unique identifier in LDAP hierarchy |
| **Dry-Run** | Simulation mode that displays planned actions without executing them |
| **F5 XC** | F5 Distributed Cloud - F5's cloud-native application delivery platform |
| **IAM** | Identity and Access Management |
| **Idempotent** | Operation that produces same result regardless of repetition |
| **LDAP** | Lightweight Directory Access Protocol |
| **OAuth** | Open Authorization standard |
| **P12** | PKCS#12 - file format for storing cryptographic objects |
| **PEM** | Privacy-Enhanced Mail - Base64 encoded certificate format |
| **PKCS** | Public-Key Cryptography Standards |
| **Prune** | Operation to delete resources not present in CSV |
| **RBAC** | Role-Based Access Control |
| **RFC** | Request for Comments - Internet standards documentation |
| **SRS** | Software Requirements Specification |
| **SSL/TLS** | Secure Sockets Layer / Transport Layer Security |
| **XC** | F5 Distributed Cloud (shortened form) |

### 1.4 References

1. **Standards**
   - ISO/IEC/IEEE 29148:2018 - Systems and software engineering — Life cycle processes — Requirements engineering
   - RFC 5322 - Internet Message Format (Email address validation)
   - RFC 4514 - LDAP Distinguished Names string representation
   - RFC 2818 - HTTP Over TLS

2. **F5 Distributed Cloud Documentation**
   - API Usage & Authentication Guide: https://docs.cloud.f5.com/docs-v2/platform/how-to/volt-automation/apis
   - API Reference (OpenAPI): https://docs.cloud.f5.com/docs-v2/api
   - IAM and User Management: https://docs.cloud.f5.com/docs-v2/ves-io/iam

3. **Project Documentation**
   - API Contract: `api/contracts/xc-iam.yaml`
   - Repository: https://github.com/robinmordasiewicz/f5-xc-user-group-sync

4. **Technology Documentation**
   - Python 3.12 Documentation: https://docs.python.org/3.12/
   - Tenacity Library (Retry): https://tenacity.readthedocs.io/
   - Click CLI Framework: https://click.palletsprojects.com/
   - OpenSSL Documentation: https://www.openssl.org/docs/

### 1.5 Document Overview

This document is organized according to ISO/IEC/IEEE 29148:2018 structure:

- **Section 2** provides an overall description of the product, its context, users, and constraints
- **Section 3** details system features with functional requirements organized by capability area
- **Section 4** specifies external interface requirements for user interaction, APIs, and communications
- **Section 5** defines non-functional requirements covering performance, security, and quality attributes
- **Section 6** documents data requirements including data models, formats, and validation rules
- **Section 7** addresses quality attributes including testability, traceability, and maintainability
- **Section 8** provides appendices with supporting information including API contracts and examples

Each functional requirement is identified with a unique ID (e.g., FR-ENV-001) and includes:
- Requirement statement with modal verbs (MUST, SHALL, SHOULD)
- Rationale explaining the business or technical justification
- Acceptance criteria defining measurable validation conditions
- Implementation notes providing technical context (when applicable)
- Testing guidance for verification approaches

---

## 2. Overall Description

### 2.1 Product Perspective

#### System Context

The F5 Distributed Cloud User and Group Synchronization Tool operates as a standalone command-line utility within an enterprise identity management ecosystem. The system interfaces with:

1. **Active Directory (AD) Exports**: Receives CSV exports containing user and group membership data from corporate AD systems
2. **F5 Distributed Cloud IAM API**: Synchronizes group definitions and memberships to F5 XC platform
3. **CI/CD Systems**: Integrates with GitHub Actions and Jenkins for automated synchronization
4. **Credential Management**: Interfaces with secure credential storage (P12 certificates, PEM files, API tokens)

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Enterprise Environment                        │
│                                                                   │
│  ┌──────────────┐         ┌──────────────────┐                  │
│  │   Active     │  CSV    │                  │                  │
│  │  Directory   ├────────>│  XC Group Sync   │                  │
│  │              │         │      Tool        │                  │
│  └──────────────┘         └────────┬─────────┘                  │
│                                    │                             │
│  ┌──────────────┐                  │ HTTPS/TLS                  │
│  │   GitHub     │                  │ (REST API)                 │
│  │   Actions/   │                  │                             │
│  │   Jenkins    │                  v                             │
│  └──────────────┘         ┌────────────────────┐                │
│                           │                     │                │
│  ┌──────────────┐         │  F5 Distributed    │                │
│  │ Credentials  │────────>│  Cloud IAM API     │                │
│  │ (P12/PEM/    │         │                     │                │
│  │  Token)      │         └────────────────────┘                │
│  └──────────────┘                                                │
└─────────────────────────────────────────────────────────────────┘
```

#### Product Position

- **Category**: Infrastructure automation and identity synchronization tool
- **Deployment Model**: Command-line utility executed on-demand or scheduled via CI/CD
- **Integration Pattern**: Extract-Transform-Load (ETL) pipeline for identity data
- **Operational Mode**: Batch processing with optional scheduling

#### Relationship to Other Systems

The tool does **NOT**:
- Replace Active Directory or F5 XC as authoritative identity sources
- Provide real-time synchronization or event-driven updates
- Manage user authentication flows or session management
- Store or maintain persistent state between executions
- Provide a user interface beyond command-line interaction

### 2.2 Product Functions

The XC Group Sync tool provides six primary functional capabilities:

#### F1: CSV-Driven Group Synchronization (Core)

Parses Active Directory CSV exports, extracts group definitions from LDAP Distinguished Names, and performs idempotent synchronization of group memberships to F5 Distributed Cloud.

**Key Operations**:
- CSV parsing and schema validation
- LDAP DN parsing to extract group Common Names (CN)
- User email aggregation by group membership
- Create/Update/Delete operations against F5 XC API
- Dry-run mode for safe validation before execution
- Full membership reconciliation (CSV is authoritative)

#### F2: Configuration and Environment Management

Supports flexible configuration through hierarchical environment variable loading, multiple authentication methods, and multi-environment deployments.

**Key Operations**:
- Hierarchical .env file loading (project root, secrets directory, custom paths)
- Multiple authentication methods (P12 certificates, PEM files, API tokens)
- Automatic environment detection (production vs staging from certificate filenames)
- Custom API endpoint configuration for non-production environments

#### F3: Advanced Retry and Backoff Mechanisms

Implements intelligent retry logic with exponential backoff for transient API failures, configurable retry attempts, and smart error classification.

**Key Operations**:
- Automatic retry on transient failures (network errors, rate limits, server errors)
- Configurable exponential backoff with min/max bounds
- Fast-fail on permanent errors (authentication, validation, not found)
- Layered retry architecture (HTTP transport + business logic layers)

#### F4: User Experience and CLI Feedback

Provides comprehensive command-line feedback with execution timing, progress visibility, structured error reporting, and user-friendly output formatting.

**Key Operations**:
- Execution time tracking and performance metrics
- Pre-operation summaries showing planned changes
- Prominent dry-run mode indicators
- Structured error reporting with actionable guidance
- Human-readable operation summaries

#### F5: Credential Setup and CI/CD Integration

Automates credential extraction from P12 certificates, environment detection, secrets management, and CI/CD pipeline integration.

**Key Operations**:
- Automatic P12-to-PEM conversion with OpenSSL compatibility
- Environment type detection (production/staging) from certificate filenames
- GitHub Actions secrets configuration
- Atomic file operations with proper permissions
- Cleanup and error handling

#### F6: Resource Pruning and Reconciliation

Optional deletion of F5 XC resources (groups and users) not present in CSV, with explicit opt-in safety controls.

**Key Operations**:
- Optional prune mode (explicit --prune flag required)
- Orphaned group detection and deletion
- Orphaned user detection and deletion
- Separate prune operation reporting
- Safety warnings and confirmation mechanisms

### 2.3 User Classes and Characteristics

#### UC1: DevOps Engineers

**Characteristics**:
- Highly technical users familiar with CLI tools and automation
- Responsible for CI/CD pipeline implementation and maintenance
- Primary executors of the tool in automated workflows
- Require detailed logging and error diagnostics

**Usage Patterns**:
- Configure CI/CD pipelines (GitHub Actions, Jenkins)
- Troubleshoot synchronization failures
- Tune retry and performance parameters
- Monitor execution metrics and logs

**Expertise**: Advanced (system administration, scripting, API integration)

#### UC2: Identity and Access Management (IAM) Administrators

**Characteristics**:
- Responsible for corporate identity and access control policies
- May have limited programming experience but strong AD/LDAP knowledge
- Focus on data accuracy and compliance with policies
- Require clear validation before changes

**Usage Patterns**:
- Export user and group data from Active Directory
- Perform dry-run validations before applying changes
- Review synchronization summaries for accuracy
- Maintain mapping between AD groups and F5 XC groups

**Expertise**: Intermediate (identity management, directory services)

#### UC3: Platform Engineers

**Characteristics**:
- Responsible for F5 Distributed Cloud platform configuration
- Familiar with F5 XC APIs and IAM concepts
- Focus on reliability and security of integrations
- Require audit trails and compliance reporting

**Usage Patterns**:
- Configure authentication methods (certificates, tokens)
- Establish environment-specific configurations
- Review security compliance of synchronization operations
- Monitor API usage and rate limiting

**Expertise**: Advanced (cloud platforms, security, API integration)

#### UC4: System Administrators

**Characteristics**:
- Responsible for server maintenance and scheduled tasks
- May execute tool manually or via cron jobs
- Focus on operational reliability and error handling
- Require clear documentation and troubleshooting guidance

**Usage Patterns**:
- Schedule periodic synchronization runs
- Respond to and resolve execution failures
- Maintain credential updates and rotations
- Monitor system resource usage

**Expertise**: Intermediate (system administration, command-line tools)

### 2.4 Operating Environment

#### Hardware Environment

**Minimum Requirements**:
- **CPU**: 1 core (2+ cores recommended for large datasets)
- **Memory**: 512 MB available RAM (1 GB+ recommended for >10,000 users)
- **Storage**: 100 MB available disk space (+ space for CSV files and logs)
- **Network**: Internet connectivity with access to F5 XC API endpoints

**Supported Platforms**:
- Linux (Ubuntu 20.04+, RHEL 8+, Debian 11+)
- macOS (10.15 Catalina+, Apple Silicon supported)
- Windows (via WSL2 - Windows Subsystem for Linux 2)

#### Software Environment

**Required Dependencies**:
- **Python**: Version 3.9 minimum, 3.12 recommended
- **OpenSSL**: Version 1.1.1+ or 3.0+ (for P12 certificate handling)
- **Operating System**: POSIX-compliant shell (bash, zsh) for setup scripts

**Optional Dependencies**:
- **GitHub CLI (gh)**: For automated GitHub secrets configuration
- **Git**: For version control integration (if using git-based workflows)

**Python Package Dependencies**:
- requests >= 2.31.0 (HTTP client)
- click >= 8.1.0 (CLI framework)
- pydantic >= 2.0.0 (data validation)
- python-dotenv >= 1.0.0 (environment configuration)
- tenacity >= 8.2.0 (retry mechanisms)
- ldap3 >= 2.9.0 (LDAP DN parsing)

#### Network Environment

**Outbound Connectivity Requirements**:
- HTTPS (443) to`*.console.ves.volterra.io`(production endpoints)
- HTTPS (443) to`*.staging.volterra.us`(staging endpoints)
- TLS 1.2 minimum (TLS 1.3 recommended)

**Proxy Support**:
- HTTP/HTTPS proxy support via standard environment variables (HTTP_PROXY, HTTPS_PROXY)
- Certificate bundle customization via REQUESTS_CA_BUNDLE

**Firewall Requirements**:
- Outbound HTTPS allowed to F5 XC API endpoints
- No inbound connectivity required

### 2.5 Design and Implementation Constraints

#### C1: F5 XC API Constraints

The tool MUST operate within F5 Distributed Cloud API limitations:

- **Namespace Restriction**: All operations confined to`system`namespace
- **Rate Limiting**: Subject to F5 XC API rate limits (429 responses)
- **Group Name Constraints**: Alphanumeric, hyphens, underscores only; max 128 characters
- **API Versioning**: Uses documented public API endpoints (may change with platform updates)
- **Authentication Methods**: Limited to documented authentication schemes (P12, PEM certificates, API tokens)

#### C2: CSV Format Constraints

The tool requires specific CSV structure from Active Directory exports:

- **Required Columns**:`Email`,`Entitlement Display Name`(LDAP DN format)
- **Fixed Schema**: No custom field mapping; predefined column names
- **Encoding**: UTF-8 encoding required
- **Format**: Standard CSV with comma delimiters and quote escaping
- **LDAP DN Format**:`Entitlement Display Name`must contain valid LDAP Distinguished Names

#### C3: Security Constraints

- **No Plaintext Secrets**: Credentials never stored in code or logs
- **Certificate Validation**: SSL certificate verification enforced (except explicitly disabled for staging)
- **Credential Permissions**: Certificate and key files must have restrictive permissions (mode 600)
- **Audit Requirements**: All operations logged with sufficient detail for security audits
- **Secret Masking**: API tokens and passwords redacted from log output

#### C4: Operational Constraints

- **Single Tenant**: One tenant per execution; no multi-tenant batch operations
- **Batch Processing**: No real-time or streaming synchronization
- **Stateless Execution**: No persistent state between runs; CSV is always authoritative
- **Manual Scheduling**: Tool does not implement internal scheduling; relies on external schedulers
- **No GUI**: Command-line only; no graphical user interface

#### C5: Compatibility Constraints

- **Python Version**: Python 3.9 minimum (3.12 recommended for latest features)
- **OpenSSL Compatibility**: Must handle both OpenSSL 1.x and 3.x (legacy algorithm support)
- **Shell Compatibility**: Setup scripts require POSIX-compliant shell (bash, zsh)
- **CI/CD Platform**: Examples provided for GitHub Actions; adaptable to other platforms

#### C6: Data Volume Constraints

- **CSV Size**: Optimized for up to 100,000 rows (larger files may require performance tuning)
- **Group Membership**: No hard limit on users per group (practical limit ~10,000 users/group)
- **Concurrent Operations**: Sequential API operations (no parallel group creation)
- **Memory Usage**: In-memory CSV processing (full file loaded into memory)

### 2.6 Assumptions and Dependencies

#### Assumptions

**A1: Active Directory Export Quality**
- CSV exports from Active Directory are accurate and up-to-date
- LDAP Distinguished Names in CSV are properly formatted
- Email addresses in CSV are valid and unique
- Group memberships in CSV reflect intended access control

**A2: F5 XC Platform Availability**
- F5 Distributed Cloud API is accessible and operational
- API endpoints remain stable and backward-compatible
- Authentication mechanisms continue to be supported
- Rate limits are sufficient for batch synchronization operations

**A3: Network Connectivity**
- Reliable internet connectivity is available during execution
- Network latency is acceptable for API operations (<500ms typical)
- No corporate proxies block access to F5 XC endpoints
- TLS/SSL connections can be established successfully

**A4: Credential Management**
- Valid credentials (P12, PEM, or API tokens) are available
- Certificates have not expired and are trusted by F5 XC
- Credential rotation processes maintain tool functionality
- Secrets management in CI/CD platforms is properly configured

**A5: User Pre-existence**
- Users referenced in CSV groups exist in F5 XC or can be auto-created
- User email addresses are valid F5 XC user identifiers
- User creation during group sync is permitted by F5 XC policies

#### Dependencies

**D1: External Systems**
- **Active Directory**: Source system for user and group data
- **F5 Distributed Cloud**: Target platform for group synchronization
- **CSV Export Process**: Mechanism to generate AD exports in required format
- **CI/CD Platform**: GitHub Actions, Jenkins, or equivalent for automation

**D2: Third-Party Libraries**
- **requests**: HTTP client for API interactions
- **click**: Command-line interface framework
- **pydantic**: Data validation and parsing
- **python-dotenv**: Environment variable management
- **tenacity**: Retry and backoff logic
- **ldap3**: LDAP Distinguished Name parsing

**D3: System Utilities**
- **OpenSSL**: Certificate and key manipulation (P12 extraction)
- **bash/zsh**: Shell scripting for setup automation
- **GitHub CLI (optional)**: Automated secrets configuration

**D4: Runtime Environment**
- **Python 3.9+**: Interpreter with required packages installed
- **Operating System**: Linux, macOS, or WSL2 with POSIX compatibility
- **Network**: Outbound HTTPS connectivity to F5 XC endpoints
- **Filesystem**: Read/write permissions for configuration and log files

**D5: Organizational Dependencies**
- **IAM Policies**: Corporate policies defining group access control
- **Security Policies**: Certificate management and rotation procedures
- **Compliance Requirements**: Audit and logging standards
- **Support Processes**: Escalation procedures for API failures

---

## 3. System Features

This section details the six primary features of the XC Group Sync tool. Each feature includes functional requirements with unique identifiers, rationale, acceptance criteria, and testing guidance.

### 3.1 Feature 1: CSV-Driven Group Synchronization

**Feature Description**

Core synchronization functionality that parses Active Directory CSV exports, extracts group definitions from LDAP Distinguished Names, and performs idempotent create/update/delete operations against F5 Distributed Cloud user group API.

**Priority**: P0 (Critical - MVP Feature)

**Functional Requirements**

#### FR-SYNC-001: CSV Schema Validation

**Requirement**: The system MUST validate that CSV input contains required columns`Email`and`Entitlement Display Name`before processing.

**Rationale**: Early validation prevents processing errors and provides clear feedback on data quality issues.

**Acceptance Criteria**:
- AC-001.1: System detects missing`Email`column and fails with error message specifying missing column
- AC-001.2: System detects missing`Entitlement Display Name`column and fails with error message
- AC-001.3: CSV with both required columns passes validation
- AC-001.4: Error message includes example of expected CSV structure

**Testing**: Unit test with CSV files missing each required column individually and both columns together.

---

#### FR-SYNC-002: LDAP DN Parsing

**Requirement**: The system MUST extract the Common Name (CN) component from LDAP Distinguished Names in the`Entitlement Display Name`column to derive group names.

**Rationale**: Group names in F5 XC are derived from the CN component of AD group DNs, establishing traceability between systems.

**Acceptance Criteria**:
- AC-002.1: For DN`CN=Admins,OU=Groups,DC=example,DC=com`, system extracts`Admins`as group name
- AC-002.2: For DN with multiple CN components`CN=Users,CN=Admins,OU=Groups,DC=example,DC=com`, system extracts first CN (`Users`)
- AC-002.3: System handles escaped characters in CN per RFC 4514
- AC-002.4: System handles special characters in CN (spaces, parentheses, commas)
- AC-002.5: Malformed DNs (missing CN) are logged and skipped with clear error message

**Testing**: Unit tests with variety of DN formats including edge cases (escaped characters, special chars, multiple CNs).

---

#### FR-SYNC-003: Group Name Validation

**Requirement**: The system MUST validate extracted group names match pattern`^[A-Za-z0-9_-]+$`with maximum length of 128 characters.

**Rationale**: F5 XC API enforces group name constraints; validation prevents API errors and provides early feedback.

**Acceptance Criteria**:
- AC-003.1: Group names with only alphanumeric, hyphens, and underscores pass validation
- AC-003.2: Group names exceeding 128 characters are rejected with length error
- AC-003.3: Group names with spaces, special characters (#, @, etc.) are rejected with format error
- AC-003.4: Invalid group names are logged and skipped, not halting entire sync operation
- AC-003.5: Validation errors include the invalid group name and reason for rejection

**Testing**: Unit tests with valid and invalid group names; integration test verifying sync continues after skipping invalid group.

---

#### FR-SYNC-004: User Email Aggregation

**Requirement**: The system MUST aggregate user email addresses by group, creating one group membership list per unique group name extracted from CSV.

**Rationale**: Multiple CSV rows with same group DN represent multiple users in that group; aggregation produces correct group membership.

**Acceptance Criteria**:
- AC-004.1: Multiple CSV rows with same`Entitlement Display Name`are aggregated into single group
- AC-004.2: Duplicate email addresses within same group are deduplicated
- AC-004.3: Empty or malformed email addresses are logged and excluded from group membership
- AC-004.4: Groups with zero valid users after filtering are logged as warnings but not created

**Testing**: Unit test with CSV containing multiple users for same group, duplicate emails, and invalid emails.

---

#### FR-SYNC-005: Idempotent Group Creation

**Requirement**: The system MUST create groups in F5 XC that exist in CSV but not in F5 XC, using POST`/api/web/namespaces/system/user_groups`endpoint.

**Rationale**: New groups discovered in CSV must be provisioned in F5 XC to grant access to users.

**Acceptance Criteria**:
- AC-005.1: Groups present in CSV but absent in F5 XC are created with correct name and user list
- AC-005.2: Successful creation increments`created`counter in operation summary
- AC-005.3: Creation errors (API failures) are logged with group name and error detail
- AC-005.4: Dry-run mode logs "would create" messages without calling API
- AC-005.5: Creation failures increment`errors`counter in operation summary

**Testing**: Integration test with mock F5 XC API; verify POST called with correct payload for new groups.

---

#### FR-SYNC-006: Idempotent Group Updates

**Requirement**: The system MUST update groups in F5 XC when membership differs from CSV, replacing entire`usernames`array with CSV-derived list using PUT`/api/web/namespaces/system/user_groups/{name}`endpoint.

**Rationale**: Full membership replacement ensures CSV is authoritative source; removes users no longer in CSV, adds new users.

**Acceptance Criteria**:
- AC-006.1: Groups with differing membership between CSV and F5 XC trigger update operation
- AC-006.2: Update replaces entire`usernames`array (not incremental patch)
- AC-006.3: Users in F5 XC but not in CSV for that group are removed
- AC-006.4: Users in CSV but not in F5 XC for that group are added
- AC-006.5: Groups with identical membership in CSV and F5 XC do not trigger update (increment`unchanged`counter)
- AC-006.6: Successful updates increment`updated`counter in operation summary
- AC-006.7: Dry-run mode logs "would update" with before/after membership differences

**Testing**: Integration test with mock API; verify PUT called only when membership differs, with complete user list.

---

#### FR-SYNC-007: Dry-Run Mode

**Requirement**: The system MUST support`--dry-run`flag that displays all planned operations (create/update/delete) without executing API calls.

**Rationale**: Dry-run provides safe validation mechanism before applying changes, critical for production safety.

**Acceptance Criteria**:
- AC-007.1: With`--dry-run`flag, no API mutation calls (POST, PUT, DELETE) are executed
- AC-007.2: Dry-run displays planned creates with group names and user counts
- AC-007.3: Dry-run displays planned updates with membership differences (added/removed users)
- AC-007.4: Dry-run displays planned deletes (when used with`--prune`)
- AC-007.5: Dry-run mode displays prominent banner: "🔍 DRY RUN MODE - No changes will be made"
- AC-007.6: Operation summary shows counts for each operation type (created/updated/deleted/unchanged)
- AC-007.7: Dry-run execution completes in reasonable time (<5 seconds for typical CSV)

**Testing**: Integration test verifying no API mutations occur with --dry-run; verify banner display; verify planned operations accuracy.

---

#### FR-SYNC-008: Operation Summary Reporting

**Requirement**: The system MUST display operation summary after sync completion showing counts of created, updated, deleted, unchanged groups, and errors encountered.

**Rationale**: Summary provides at-a-glance understanding of sync impact and success rate.

**Acceptance Criteria**:
- AC-008.1: Summary displays in format:`Groups: created=N, updated=N, deleted=N, unchanged=N, errors=N`
- AC-008.2: Counters accurately reflect operations performed or planned (in dry-run)
- AC-008.3: Summary displayed regardless of success or failure
- AC-008.4: Execution time displayed in format:`Execution time: XX.XX seconds`
- AC-008.5: For user operations, separate summary:`Users: created=N, updated=N, deleted=N, unchanged=N, errors=N`

**Testing**: Integration tests for various scenarios (all creates, all updates, mixed operations, errors); verify counter accuracy.

---

#### FR-SYNC-009: User Auto-Creation

**Requirement**: The system MUST automatically create users in F5 XC when adding user to group membership if user does not exist, using POST`/api/web/namespaces/system/users`endpoint.

**Rationale**: Groups require pre-existing users; auto-creation ensures group membership operations succeed.

**Acceptance Criteria**:
- AC-009.1: Before adding user to group, system checks if user exists in F5 XC
- AC-009.2: Non-existent users are created with email as primary identifier
- AC-009.3: User creation errors (API failures) are logged and increment error counter
- AC-009.4: User creation failures cause group operation to be skipped and logged
- AC-009.5: Successfully created users are added to group membership
- AC-009.6: User auto-creation respects dry-run mode (logs "would create user" without API call)

**Testing**: Integration test with mock API; verify user creation attempted before group membership addition for new users.

---

### 3.2 Feature 2: Configuration and Environment Management

**Feature Description**

Flexible configuration system supporting hierarchical environment variable loading, multiple authentication methods, multi-environment deployments, and automatic environment detection.

**Priority**: P0 (Critical - Required for all deployments)

**Functional Requirements**

#### FR-ENV-001: Hierarchical Environment Loading

**Requirement**: The system MUST support hierarchical environment variable loading in the following order (highest to lowest priority):
1. Environment variables set in current shell
2.`secrets/.env`file (if exists)
3.`.env`file in project root (if exists)

**Rationale**: Prioritized loading enables local development overrides while supporting production secrets separation.

**Acceptance Criteria**:
- AC-ENV-001.1: Shell environment variables override any .env file values
- AC-ENV-001.2:`secrets/.env`values override`.env`file values
- AC-ENV-001.3:`.env`file values are used when not overridden by higher priority sources
- AC-ENV-001.4: Missing .env files do not cause errors; system continues with available configuration
- AC-ENV-001.5: System logs configuration source for debugging (e.g., "TENANT_ID loaded from secrets/.env")

**Testing**: Unit tests with various combinations of environment variables and .env files; verify precedence order.

---

#### FR-ENV-002: Custom Environment Path

**Requirement**: The system MUST support`DOTENV_PATH`environment variable to specify custom .env file location, overriding default paths.

**Rationale**: Enables CI/CD pipelines and custom deployments to specify credentials location without code changes.

**Acceptance Criteria**:
- AC-ENV-002.1: When`DOTENV_PATH`is set, system loads from specified path
- AC-ENV-002.2: Custom path takes precedence over`secrets/.env`and`.env`
- AC-ENV-002.3: Invalid or non-existent`DOTENV_PATH`logs warning and continues with remaining sources
- AC-ENV-002.4: Relative paths in`DOTENV_PATH`are resolved from current working directory
- AC-ENV-002.5: Absolute paths in`DOTENV_PATH`are used directly

**Testing**: Unit test with DOTENV_PATH pointing to custom location; verify loading from custom path.

---

#### FR-ENV-003: API URL Configuration

**Requirement**: The system MUST support`XC_API_URL`environment variable to override default F5 XC API endpoint, with automatic derivation from`TENANT_ID`when not set.

**Default Behavior**: If`XC_API_URL`not set, derive as`https://{TENANT_ID}.console.ves.volterra.io`

**Rationale**: Enables testing against staging/development environments without code changes.

**Acceptance Criteria**:
- AC-ENV-003.1: When`XC_API_URL`is set, system uses specified endpoint for all API calls
- AC-ENV-003.2: When`XC_API_URL`not set, system derives from`TENANT_ID`using production pattern
- AC-ENV-003.3: Custom URLs support staging pattern:`https://{TENANT_ID}.staging.volterra.us`
- AC-ENV-003.4: Invalid URL format (missing protocol, malformed) causes immediate error with clear message
- AC-ENV-003.5: URL is validated for HTTPS protocol (HTTP rejected for security)

**Testing**: Unit tests with custom XC_API_URL; integration test verifying API calls use custom endpoint.

---

#### FR-ENV-004: Multiple Authentication Methods

**Requirement**: The system MUST support three authentication methods with automatic selection:
1. P12 certificate file (`.p12`with password)
2. PEM certificate and key files (separate`.pem`files)
3. API token (string token)

**Priority Order**: P12 > PEM > Token (when multiple methods configured)

**Rationale**: Supports diverse enterprise authentication requirements; P12 preferred for organizational deployments.

**Acceptance Criteria**:
- AC-ENV-004.1: System detects and uses P12 when`VOLT_API_P12_FILE`and`VES_P12_PASSWORD`are set
- AC-ENV-004.2: System falls back to PEM when`VOLT_API_CERT_FILE`and`VOLT_API_CERT_KEY_FILE`are set (and P12 not available)
- AC-ENV-004.3: System falls back to token when`XC_API_TOKEN`is set (and certificates not available)
- AC-ENV-004.4: Missing authentication credentials cause immediate failure with clear error message listing required variables
- AC-ENV-004.5: P12 files are extracted to temporary PEM files for requests library compatibility
- AC-ENV-004.6: Temporary PEM files are cleaned up after use
- AC-ENV-004.7: System logs which authentication method is being used (for debugging)

**Testing**: Integration tests with each authentication method; verify correct auth headers in API calls.

---

#### FR-ENV-005: Environment Detection from Certificate Filenames

**Requirement**: Setup script MUST auto-detect environment type (production vs staging) from P12 filename patterns:
- **Production**:`{tenant}.console.ves.volterra.io.api-creds.p12`
- **Staging**:`{tenant}.staging.api-creds.p12`

**Rationale**: Automatic environment detection reduces configuration errors and simplifies multi-environment workflows.

**Acceptance Criteria**:
- AC-ENV-005.1: Production pattern filename extracts tenant ID and sets`XC_API_URL`to production endpoint
- AC-ENV-005.2: Staging pattern filename extracts tenant ID and sets`XC_API_URL`to staging endpoint
- AC-ENV-005.3: Fallback pattern (no environment indicators) assumes production with tenant from first DN component
- AC-ENV-005.4: Detected environment type logged during setup: "Using XC_API_URL=... (production)" or "(staging)"
- AC-ENV-005.5:`XC_API_URL`written to`secrets/.env`file for CLI consumption

**Testing**: Unit tests with various P12 filename patterns; verify correct environment detection and URL derivation.

---

#### FR-ENV-006: Staging Environment SSL Warnings

**Requirement**: Setup script MUST display warnings when staging environment is detected about potential SSL certificate verification issues.

**Rationale**: Staging F5 XC environments often use self-signed certificates that fail Python requests library SSL verification.

**Acceptance Criteria**:
- AC-ENV-006.1: When staging environment detected, prominent warning displayed:

  ```text
  ⚠️  WARNING: Staging environments use self-signed CAs
  Python requests library may fail SSL verification.
  See README 'SSL Certificate Verification Issues' for solutions.
  ```

- AC-ENV-006.2: Warning displayed during setup script execution
- AC-ENV-006.3: Warning does not block setup completion; informational only
- AC-ENV-006.4: Production environments do not display warning

**Testing**: Integration test of setup script with staging-pattern P12 file; verify warning display.

---

### 3.3 Feature 3: Advanced Retry and Backoff Mechanisms

**Feature Description**

Configurable retry logic with exponential backoff for transient API failures, intelligent error classification (retriable vs permanent), and layered retry architecture for robust operation in unreliable network conditions.

**Priority**: P1 (High - Production reliability feature)

**Functional Requirements**

#### FR-RETRY-001: Configurable Retry Attempts

**Requirement**: GroupSyncService MUST support configurable retry attempts for user auto-creation operations via constructor parameters.

**Default Values**:
-`retry_attempts`: 3 (total attempts including initial)
-`backoff_multiplier`: 1.0 (linear backoff)
-`backoff_min`: 1.0 second (minimum wait)
-`backoff_max`: 4.0 seconds (maximum wait)

**Rationale**: Enables tuning retry behavior based on API characteristics, network conditions, operational requirements without code changes.

**Acceptance Criteria**:
- AC-RETRY-001.1: GroupSyncService constructor accepts`retry_attempts`parameter
- AC-RETRY-001.2: GroupSyncService constructor accepts`backoff_multiplier`,`backoff_min`,`backoff_max`parameters
- AC-RETRY-001.3: Default values used when parameters not specified
- AC-RETRY-001.4: Invalid parameter values (negative, zero, min>max) cause immediate error
- AC-RETRY-001.5: Retry configuration logged at service initialization for debugging

**Testing**: Unit tests with various retry configurations; verify retry attempts match specified values.

---

#### FR-RETRY-002: Exponential Backoff

**Requirement**: System MUST apply exponential backoff with configurable multiplier for retry delays according to formula:

```python
wait_time = min(backoff_multiplier * (2 ** (attempt - 1)), backoff_max)
wait_time = max(wait_time, backoff_min)
```

**Rationale**: Exponential backoff reduces load on recovering systems while maintaining reasonable retry attempts for transient failures.

**Acceptance Criteria**:
- AC-RETRY-002.1: First retry attempt waits`backoff_multiplier * 1`seconds (2^0)
- AC-RETRY-002.2: Second retry attempt waits`backoff_multiplier * 2`seconds (2^1)
- AC-RETRY-002.3: Third retry attempt waits`backoff_multiplier * 4`seconds (2^2)
- AC-RETRY-002.4: Wait time never exceeds`backoff_max`
- AC-RETRY-002.5: Wait time never less than`backoff_min`
- AC-RETRY-002.6: Actual wait times logged for debugging

**Testing**: Unit test with mocked time.sleep(); verify wait durations match exponential backoff formula.

---

#### FR-RETRY-003: Intelligent Error Classification

**Requirement**: System MUST only retry transient network/API errors (connection failures, timeouts, HTTP 5xx, HTTP 429), not permanent failures (HTTP 4xx except 429, validation errors, programming errors).

**Retriable Errors**:
- Connection errors (network unreachable, connection refused)
- Timeout errors (request timeout, read timeout)
- HTTP 5xx server errors (500, 502, 503, 504)
- HTTP 429 rate limit errors

**Non-Retriable Errors (fail fast)**:
- HTTP 400 bad request (invalid data)
- HTTP 401/403 authentication/authorization failures
- HTTP 404 not found (endpoint doesn't exist)
- ValueError, TypeError (programming errors)

**Rationale**: Avoids wasting retry attempts on errors that won't succeed with repetition; preserves resources for genuinely transient failures.

**Acceptance Criteria**:
- AC-RETRY-003.1: Connection errors trigger retry with backoff
- AC-RETRY-003.2: HTTP 5xx errors trigger retry with backoff
- AC-RETRY-003.3: HTTP 429 rate limit triggers retry with backoff (honors Retry-After header if present)
- AC-RETRY-003.4: HTTP 400 errors fail immediately without retry
- AC-RETRY-003.5: HTTP 401/403 errors fail immediately with authentication error message
- AC-RETRY-003.6: HTTP 404 errors fail immediately with endpoint not found message
- AC-RETRY-003.7: Retry attempts and failure reasons logged for troubleshooting

**Testing**: Unit tests with mocked API responses for each error type; verify retry behavior matches classification.

---

#### FR-RETRY-004: Selective Retry Application

**Requirement**: Retry logic MUST apply specifically to user auto-creation within group operations, not to group create/update/delete operations.

**Rationale**: User auto-creation most likely to experience transient failures due to concurrent operations; group operations are idempotent and manual retry is acceptable.

**Acceptance Criteria**:
- AC-RETRY-004.1: User creation operations retry up to configured attempts on transient failures
- AC-RETRY-004.2: Group creation operations do not retry; immediate failure on error
- AC-RETRY-004.3: Group update operations do not retry; immediate failure on error
- AC-RETRY-004.4: Group deletion operations do not retry; immediate failure on error
- AC-RETRY-004.5: Retry vs non-retry behavior clearly documented in code comments

**Testing**: Integration tests with mocked API; verify retry only occurs for user creation, not group operations.

---

#### FR-RETRY-005: Layered Retry Architecture

**Requirement**: System MUST implement layered retry architecture:
1. **HTTP Transport Layer** (urllib3 Retry): Low-level retries for network/server errors
2. **Business Logic Layer** (tenacity): High-level retries for specific operations with custom backoff

**Interaction**: HTTP layer retries exhaust first (e.g., 3 attempts), then business logic layer retries (another 3 attempts), potentially resulting in 9 total HTTP requests in worst case.

**Rationale**: Defense in depth; HTTP layer handles transient network issues, business logic layer handles application-specific retry requirements.

**Acceptance Criteria**:
- AC-RETRY-005.1: HTTP transport layer configured with retry strategy (3 attempts, exponential backoff)
- AC-RETRY-005.2: Business logic layer wraps specific operations with @retry decorator
- AC-RETRY-005.3: Maximum total attempts documented and logged
- AC-RETRY-005.4: Layered retry behavior documented in architecture documentation
- AC-RETRY-005.5: Retry metrics (total attempts, layers triggered) available in logs

**Testing**: Integration test with network fault injection; verify both retry layers trigger appropriately.

---

### 3.4 Feature 4: User Experience and CLI Feedback

**Feature Description**

Comprehensive command-line feedback system providing execution timing, progress visibility, structured error reporting, user-friendly output formatting, and safety mechanisms for production operations.

**Priority**: P1 (High - Critical for operational safety)

**Functional Requirements**

#### FR-UX-001: Execution Time Tracking

**Requirement**: System MUST track and display total execution time for sync operations with 2 decimal precision.

**Rationale**: Provides users with performance visibility, helps identify slow operations, useful for optimizing large sync jobs.

**Acceptance Criteria**:
- AC-UX-001.1: Execution time displayed in format:`Execution time: XX.XX seconds`
- AC-UX-001.2: Timer starts before first API call, stops after last operation
- AC-UX-001.3: Execution time displayed for both dry-run and apply modes
- AC-UX-001.4: Execution time included in both group sync and user sync output
- AC-UX-001.5: Time tracking overhead negligible (<1ms)

**Testing**: Integration tests with timed operations; verify execution time accuracy within 100ms tolerance.

---

#### FR-UX-002: Pre-Operation Summary Display

**Requirement**: System MUST display planned operations summary before executing API calls, showing group counts and membership sizes.

**Rationale**: Gives users visibility into what will be changed before execution; critical for validation in production environments.

**Acceptance Criteria**:
- AC-UX-002.1: Summary displays total groups planned from CSV
- AC-UX-002.2: Summary lists each group with user count:`- {group_name}: {user_count} users`
- AC-UX-002.3: Summary displays existing resource counts from F5 XC:`Existing users in F5 XC: {count}`
- AC-UX-002.4: Summary displayed before any API mutation operations
- AC-UX-002.5: Summary format consistent between dry-run and apply modes

**Testing**: Integration test verifying summary displayed with correct counts before API calls.

---

#### FR-UX-003: Enhanced Error Reporting

**Requirement**: CLI MUST provide structured error summary with operation counts and detailed error list when failures occur.

**Rationale**: Consolidates error information for easy review; provides actionable details for remediation.

**Acceptance Criteria**:
- AC-UX-003.1: Error summary header:`Errors encountered:`
- AC-UX-003.2: Each error formatted:`- {email}: {operation} failed - {error_detail}`
- AC-UX-003.3: Error summary displayed after operation completion, before exit
- AC-UX-003.4: Exit code 1 returned when errors encountered
- AC-UX-003.5: Error details include enough context for troubleshooting (operation type, resource identifier, specific error)

**Testing**: Integration test with forced API failures; verify error summary accuracy and formatting.

---

#### FR-UX-004: Context-Aware Error Messages

**Requirement**: System MUST provide context-aware error messages for common failure scenarios categorized by error type.

**Error Categories**:
- **Usage errors** (`click.UsageError`): User input problems (missing files, invalid formats)
- **API errors** (`click.ClickException`with API context): Authentication failures, network issues
- **Sync errors** (`click.ClickException`with operation details): Individual operation failures

**Rationale**: Different error types require different user actions; clear categorization speeds troubleshooting.

**Acceptance Criteria**:
- AC-UX-004.1: CSV parse errors display:`Failed to parse CSV: {specific_error}`
- AC-UX-004.2: Authentication errors display:`API error: Authentication failed - check credentials`
- AC-UX-004.3: Network errors display:`API error: Network unreachable - check connectivity`
- AC-UX-004.4: Sync errors display operation context:`Failed to {operation} {resource}: {error}`
- AC-UX-004.5: Error messages include actionable guidance when possible

**Testing**: Unit tests with various error scenarios; verify error message format and actionable guidance.

---

#### FR-UX-005: Dry-Run Mode Indication

**Requirement**: System MUST clearly indicate dry-run mode with prominent visual banner to prevent confusion.

**Rationale**: Prominent dry-run indication prevents users from misinterpreting test runs as actual operations; critical for production safety.

**Acceptance Criteria**:
- AC-UX-005.1: Banner displayed:

  ```text
  ============================================================
  🔍 DRY RUN MODE - No changes will be made to F5 XC
  ============================================================
  ```

- AC-UX-005.2: Banner displayed before operation summary
- AC-UX-005.3: Banner uses visual separator lines (60 characters)
- AC-UX-005.4: Banner includes emoji indicator for visibility
- AC-UX-005.5: Banner displayed for all operations in dry-run mode

**Testing**: Integration test with --dry-run flag; verify banner presence and format.

---

#### FR-UX-006: Human-Readable Operation Summaries

**Requirement**: System MUST provide human-readable operation summaries with consistent formatting across commands.

**Format**:`Groups: created=N, updated=N, deleted=N, unchanged=N, errors=N`

**Rationale**: Standardized summary format improves consistency and readability across all operations.

**Acceptance Criteria**:
- AC-UX-006.1: Group sync summary uses format specified above
- AC-UX-006.2: User sync summary uses parallel format:`Users: created=N, updated=N, deleted=N, unchanged=N, errors=N`
- AC-UX-006.3: Counters accurate regardless of dry-run or apply mode
- AC-UX-006.4: Summary displayed after operation completion, before execution time
- AC-UX-006.5: Summary includes all counter categories even when zero

**Testing**: Integration tests for various scenarios; verify summary format consistency and counter accuracy.

---

#### FR-UX-007: Completion Confirmation

**Requirement**: System MUST provide clear completion messages indicating successful operation finish.

**Rationale**: Explicit completion messages confirm successful operation; distinguish from error exits.

**Acceptance Criteria**:
- AC-UX-007.1: Group sync displays:`Sync complete.`
- AC-UX-007.2: User sync displays:`User sync complete.`
- AC-UX-007.3: Completion message displayed after summary and execution time
- AC-UX-007.4: Completion message displayed only on successful completion (exit code 0)
- AC-UX-007.5: No completion message when errors cause early exit

**Testing**: Integration tests for successful operations; verify completion message presence.

---

#### FR-UX-008: Prune Operation Feedback

**Requirement**: System MUST display separate prune operation summaries when`--prune`flag is used.

**Rationale**: Separate prune feedback distinguishes prune operations from main sync operations; important for auditing destructive actions.

**Acceptance Criteria**:
- AC-UX-008.1: Prune summary header:`User prune: {deleted} deleted, {errors} errors`
- AC-UX-008.2: Prune summary displayed after main sync summary
- AC-UX-008.3: Prune summary shows deleted count for both users and groups separately
- AC-UX-008.4: Prune operations included in dry-run planning
- AC-UX-008.5: Prune summary format consistent with main summary format

**Testing**: Integration test with --prune flag; verify separate prune summary display.

---

#### FR-UX-009: Warning Messages for Configuration Issues

**Requirement**: System MUST display user-friendly warnings for configuration issues without blocking execution.

**Rationale**: Non-blocking warnings inform users of configuration issues while allowing operations to continue with fallback methods.

**Acceptance Criteria**:
- AC-UX-009.1: P12 file warning displays when P12 provided but Python requests cannot use directly
- AC-UX-009.2: Warning includes guidance: "Please run setup_xc_credentials.sh to extract cert/key files"
- AC-UX-009.3: Warning does not block execution; system falls back to alternative auth method if available
- AC-UX-009.4: Warnings logged at WARNING level, visible in default logging configuration
- AC-UX-009.5: Configuration warnings displayed before operation begins

**Testing**: Integration test with P12 file and no extracted PEM files; verify warning display and fallback behavior.

---

### 3.5 Feature 5: Credential Setup and CI/CD Integration

**Feature Description**

Automated credential extraction from P12 certificates, environment detection, secrets management, and CI/CD pipeline integration with atomic file operations and proper error handling.

**Priority**: P1 (High - Required for automated deployments)

**Functional Requirements**

#### FR-SETUP-001: Environment Detection from P12 Filenames

**Requirement**: Script MUST automatically detect environment type (production vs staging) from P12 filename patterns and derive appropriate API URL.

**Filename Patterns**:
- **Production**:`{tenant}.console.ves.volterra.io.api-creds.p12`→`https://{tenant}.console.ves.volterra.io`
- **Staging**:`{tenant}.staging.api-creds.p12`→`https://{tenant}.staging.volterra.us`
- **Fallback**:`{tenant}.api-creds.p12`→`https://{tenant}.console.ves.volterra.io`(assumed production)

**Rationale**: Eliminates manual environment configuration; reduces setup errors; enables correct API URL derivation for different F5 XC environments.

**Acceptance Criteria**:
- AC-SETUP-001.1: Production pattern filename correctly extracts tenant ID and sets production URL
- AC-SETUP-001.2: Staging pattern filename correctly extracts tenant ID and sets staging URL
- AC-SETUP-001.3: Fallback pattern assumes production with tenant from filename prefix
- AC-SETUP-001.4: Detected environment logged: "Using XC_API_URL=... (production)" or "(staging)" or "(production assumed)"
- AC-SETUP-001.5: Invalid P12 filenames (no tenant extractable) cause error with clear message

**Testing**: Unit tests with various P12 filename patterns; verify correct environment and URL derivation.

---

#### FR-SETUP-002: Automatic Environment File Generation

**Requirement**: Script MUST write detected`XC_API_URL`,`TENANT_ID`, and credential paths to`secrets/.env`file for CLI consumption.

**Rationale**: Automated .env generation eliminates manual configuration; ensures consistency between credentials and environment settings.

**Acceptance Criteria**:
- AC-SETUP-002.1:`secrets/.env`file created with variables:`TENANT_ID`,`XC_API_URL`,`VOLT_API_CERT_FILE`,`VOLT_API_CERT_KEY_FILE`,`VOLT_API_P12_FILE`,`VES_P12_PASSWORD`
- AC-SETUP-002.2: Certificate paths use absolute paths ($(pwd)/secrets/...)
- AC-SETUP-002.3: File created with mode 600 (owner read/write only)
- AC-SETUP-002.4: Existing`secrets/.env`file backed up before overwrite (timestamped backup)
- AC-SETUP-002.5: .env file format compatible with python-dotenv parser

**Testing**: Integration test of setup script; verify .env file contents and permissions.

---

#### FR-SETUP-003: OpenSSL 3.x Compatibility

**Requirement**: Script MUST support OpenSSL 3.x with automatic`-legacy`fallback for PKCS#12 operations.

**Rationale**: OpenSSL 3.0+ deprecated legacy algorithms used in many P12 files; automatic fallback ensures compatibility across OpenSSL versions.

**Acceptance Criteria**:
- AC-SETUP-003.1: Script attempts standard`openssl pkcs12`command first
- AC-SETUP-003.2: On failure, script retries with`openssl pkcs12 -legacy`flag
- AC-SETUP-003.3: Both OpenSSL 1.x and 3.x successfully extract certificates
- AC-SETUP-003.4: Legacy fallback behavior logged for debugging
- AC-SETUP-003.5: Failure of both methods produces clear error message with OpenSSL version info

**Testing**: Integration tests on systems with OpenSSL 1.x and 3.x; verify successful extraction on both.

---

#### FR-SETUP-004: Passwordless Private Key Extraction

**Requirement**: Script MUST ensure extracted private keys are decrypted (passwordless) for Python requests compatibility.

**Rationale**: Python requests library requires passwordless PEM keys for TLS client authentication; PKCS#12 extraction sometimes produces encrypted keys despite`-nodes`flag.

**Acceptance Criteria**:
- AC-SETUP-004.1: Script detects encrypted key by searching for "ENCRYPTED" marker in PEM file
- AC-SETUP-004.2: Encrypted keys automatically decrypted using`openssl rsa -in key -out key_nopass`
- AC-SETUP-004.3: Decrypted key replaces original encrypted key
- AC-SETUP-004.4: Final key file contains no "ENCRYPTED" marker
- AC-SETUP-004.5: Decryption process logged for debugging

**Testing**: Integration test with P12 that produces encrypted key; verify key is decrypted.

---

#### FR-SETUP-005: Atomic File Operations

**Requirement**: Script MUST use atomic file creation with temporary files and`install`command for secure credential handling.

**Rationale**: Prevents partial file writes, race conditions, and credential exposure during script execution.

**Acceptance Criteria**:
- AC-SETUP-005.1: Temporary files created with unique random suffixes (mktemp pattern)
- AC-SETUP-005.2: Extraction operations write to temporary files first
- AC-SETUP-005.3:`install`command atomically moves temporary files to final location with mode 600
- AC-SETUP-005.4: Cleanup trap ensures temporary files removed on script exit (success or failure)
- AC-SETUP-005.5: No partial credential files left in filesystem after any script termination scenario

**Testing**: Integration test with script interruption (SIGINT); verify no temporary files remain.

---

#### FR-SETUP-006: Optional GitHub Secrets Configuration

**Requirement**: Script MUST support`--no-secrets`flag to skip GitHub secrets creation, with automatic detection and configuration when gh CLI available.

**Rationale**: Local development and non-GitHub CI/CD environments don't require GitHub secrets; flag provides flexibility.

**Acceptance Criteria**:
- AC-SETUP-006.1: Without`--no-secrets`, script attempts GitHub secrets creation if gh CLI available
- AC-SETUP-006.2: With`--no-secrets`, GitHub secrets creation skipped
- AC-SETUP-006.3: Missing gh CLI logs warning and skips secrets creation (not fatal error)
- AC-SETUP-006.4: Secrets created:`TENANT_ID`,`XC_CERT`(base64),`XC_CERT_KEY`(base64),`XC_P12`(base64),`XC_P12_PASSWORD`
- AC-SETUP-006.5: Secret creation success/failure logged for each secret

**Testing**: Unit test with --no-secrets flag; verify secrets creation skipped.

---

#### FR-SETUP-007: P12 File Auto-Discovery

**Requirement**: Script MUST support automatic P12 file detection in`~/Downloads`when exactly one P12 file exists, with interactive selection for multiple files.

**Rationale**: Reduces friction for common workflow (download credentials → run setup); interactive selection maintains safety with ambiguous cases.

**Acceptance Criteria**:
- AC-SETUP-007.1: Zero P12 files in ~/Downloads causes error with message to provide --p12 flag
- AC-SETUP-007.2: One P12 file in ~/Downloads automatically used without prompting
- AC-SETUP-007.3: Multiple P12 files present interactive menu: "Select p12 file (enter number):"
- AC-SETUP-007.4: Interactive menu lists all P12 files with numbered options
- AC-SETUP-007.5: User selection validated; invalid selection prompts again

**Testing**: Integration tests with 0, 1, and multiple P12 files; verify auto-detection and interactive selection.

---

#### FR-SETUP-008: Multiple Password Input Methods

**Requirement**: Script MUST support multiple password input methods: environment variable (VES_P12_PASSWORD), interactive TTY prompt, and stdin pipe.

**Priority Order**: Environment variable > Interactive TTY > stdin pipe

**Rationale**: Supports diverse deployment scenarios from manual setup to fully automated CI/CD pipelines.

**Acceptance Criteria**:
- AC-SETUP-008.1: When VES_P12_PASSWORD set, script uses value without prompting
- AC-SETUP-008.2: When VES_P12_PASSWORD not set and stdin is TTY, script prompts: "Enter p12 passphrase:" (silent input)
- AC-SETUP-008.3: When VES_P12_PASSWORD not set and stdin is pipe, script reads password from stdin
- AC-SETUP-008.4: Silent input (no echo) for interactive TTY prompt
- AC-SETUP-008.5: Password never logged or displayed in output

**Testing**: Integration tests with each password input method; verify correct password acquisition.

---

### 3.6 Feature 6: Resource Pruning and Reconciliation

**Feature Description**

Optional deletion of F5 XC resources (groups and users) not present in CSV, with explicit opt-in controls, safety mechanisms, and comprehensive feedback for destructive operations.

**Priority**: P2 (Medium - Optional production feature)

**Functional Requirements**

#### FR-PRUNE-001: Explicit Opt-In Requirement

**Requirement**: System MUST require explicit`--prune`flag to enable deletion of resources not in CSV; default behavior is add/update only.

**Rationale**: Destructive operations require explicit user intent; prevents accidental data loss from omissions in CSV.

**Acceptance Criteria**:
- AC-PRUNE-001.1: Without`--prune`flag, orphaned groups and users are not deleted
- AC-PRUNE-001.2: With`--prune`flag, orphaned groups identified and deleted
- AC-PRUNE-001.3: With`--prune`flag, orphaned users identified and deleted
- AC-PRUNE-001.4: Prune operations respect dry-run mode (log "would delete" without API call)
- AC-PRUNE-001.5: Prune flag behavior documented in CLI help text

**Testing**: Integration tests with and without --prune flag; verify deletions only occur with flag present.

---

#### FR-PRUNE-002: Orphaned Group Detection

**Requirement**: System MUST identify groups present in F5 XC`system`namespace but absent from CSV as orphaned groups eligible for deletion.

**Rationale**: Authoritative synchronization requires removing groups no longer managed in AD.

**Acceptance Criteria**:
- AC-PRUNE-002.1: Groups in F5 XC but not in CSV identified as orphaned
- AC-PRUNE-002.2: Groups in CSV but not in F5 XC not considered orphaned (will be created)
- AC-PRUNE-002.3: Orphaned group list logged before deletion
- AC-PRUNE-002.4: Orphaned groups deleted via DELETE`/api/web/namespaces/system/user_groups/{name}`
- AC-PRUNE-002.5: Deletion count included in operation summary

**Testing**: Integration test with mock API; verify orphaned groups correctly identified and deleted.

---

#### FR-PRUNE-003: Orphaned User Detection

**Requirement**: System MUST identify users present in F5 XC but not referenced in any CSV group membership as orphaned users eligible for deletion.

**Rationale**: Complete reconciliation includes removing users no longer managed in AD.

**Acceptance Criteria**:
- AC-PRUNE-003.1: Users in F5 XC but not in any CSV group identified as orphaned
- AC-PRUNE-003.2: Users in CSV groups but not in F5 XC not considered orphaned (will be created)
- AC-PRUNE-003.3: Orphaned user list logged before deletion
- AC-PRUNE-003.4: Orphaned users deleted via DELETE`/api/web/namespaces/system/users/{email}`
- AC-PRUNE-003.5: Deletion count included in user prune summary

**Testing**: Integration test with mock API; verify orphaned users correctly identified and deleted.

---

#### FR-PRUNE-004: Separate Prune Reporting

**Requirement**: System MUST display separate prune operation summaries distinct from main sync summaries.

**Rationale**: Separate reporting clearly distinguishes destructive prune operations from standard sync operations; important for audit trails.

**Acceptance Criteria**:
- AC-PRUNE-004.1: Group prune summary:`Group prune: {deleted} deleted, {errors} errors`
- AC-PRUNE-004.2: User prune summary:`User prune: {deleted} deleted, {errors} errors`
- AC-PRUNE-004.3: Prune summaries displayed after main sync summary
- AC-PRUNE-004.4: Prune summaries included in dry-run output
- AC-PRUNE-004.5: Prune deletion counts separate from main sync deletion counts

**Testing**: Integration test with --prune flag; verify separate summary display and counter accuracy.

---

#### FR-PRUNE-005: Prune Operation Safety

**Requirement**: System MUST provide safety mechanisms for prune operations including dry-run validation, error handling, and rollback capabilities.

**Rationale**: Destructive operations require additional safety controls to prevent unintended data loss.

**Acceptance Criteria**:
- AC-PRUNE-005.1: Dry-run with --prune shows planned deletions without executing
- AC-PRUNE-005.2: Prune operations logged with sufficient detail for audit trail
- AC-PRUNE-005.3: Prune deletion failures logged with resource identifier and error detail
- AC-PRUNE-005.4: Partial prune failures do not halt entire operation; continue with remaining resources
- AC-PRUNE-005.5: Prune operations occur after main sync completes successfully

**Testing**: Integration tests with prune failures; verify error handling and partial completion behavior.

---

## 4. External Interface Requirements

### 4.1 User Interfaces

#### UI-001: Command-Line Interface

**Description**: The system provides a command-line interface implemented using the Click framework.

**Interface Type**: Text-based command-line (stdin/stdout/stderr)

**Primary Commands**:

1. **sync**: Synchronize groups and users from CSV to F5 XC

   ```bash
   xc_user_group_sync sync --csv <file> [options]
   ```

2. **sync_users**: Synchronize users only from CSV to F5 XC (DEPRECATED - use sync)

   ```bash
   xc_user_group_sync sync_users --csv <file> [options]
   ```

**Command Options**:
-`--csv <file>`: Path to CSV file (required)
-`--dry-run`: Log actions without calling API (optional, default: false)
-`--prune`: Delete XC users and groups missing from CSV (optional, default: false)
-`--log-level <level>`: Logging level (debug|info|warning|error, default: info)
-`--max-retries <n>`: Maximum retry attempts for transient errors (default: 3)
-`--timeout <seconds>`: HTTP timeout in seconds (default: 30)

**Output Format**:
- Structured text output to stdout
- Error messages to stderr
- Progress indicators and summaries to stdout
- Machine-readable exit codes (0=success, 1=error)

**Accessibility**:
- Plain text output compatible with screen readers
- No color dependencies (works on monochrome terminals)
- Clear, descriptive text messages
- Consistent formatting for parsing by scripts

---

### 4.2 Hardware Interfaces

**HW-001: No Direct Hardware Interfaces**

The system does not interface directly with hardware devices. All hardware interaction is mediated through the operating system:
- Filesystem access via OS file I/O APIs
- Network access via OS networking stack
- Console I/O via OS terminal interfaces

---

### 4.3 Software Interfaces

#### SI-001: F5 Distributed Cloud IAM API

**Interface Type**: RESTful HTTP API

**API Version**: Public API (version determined by endpoint URL)

**Base URL**: Configurable via`XC_API_URL`environment variable
- Production pattern:`https://{tenant}.console.ves.volterra.io`
- Staging pattern:`https://{tenant}.staging.volterra.us`

**Authentication**: TLS client certificate or API token in HTTP header

**Endpoints Used**:

1. **List User Groups**
   - Method: GET
   - Path:`/api/web/namespaces/system/user_groups`
   - Response: JSON array of user group objects

2. **Create User Group**
   - Method: POST
   - Path:`/api/web/namespaces/system/user_groups`
   - Request Body: JSON user group object
   - Response: HTTP 201 Created

3. **Update User Group**
   - Method: PUT
   - Path:`/api/web/namespaces/system/user_groups/{name}`
   - Request Body: JSON user group object
   - Response: HTTP 200 OK

4. **Delete User Group**
   - Method: DELETE
   - Path:`/api/web/namespaces/system/user_groups/{name}`
   - Response: HTTP 204 No Content

5. **Create User**
   - Method: POST
   - Path:`/api/web/namespaces/system/users`
   - Request Body: JSON user object
   - Response: HTTP 201 Created

6. **Delete User**
   - Method: DELETE
   - Path:`/api/web/namespaces/system/users/{email}`
   - Response: HTTP 204 No Content

**Data Format**: JSON (Content-Type: application/json)

**Error Handling**:
- HTTP 400: Bad Request (validation errors)
- HTTP 401: Unauthorized (authentication failure)
- HTTP 403: Forbidden (authorization failure)
- HTTP 404: Not Found (resource doesn't exist)
- HTTP 429: Rate Limit Exceeded (retry with backoff)
- HTTP 5xx: Server Error (retry with backoff)

**Rate Limiting**: Subject to F5 XC platform rate limits; tool implements retry with exponential backoff

**API Contract**: See Appendix A for detailed OpenAPI specification

---

#### SI-002: CSV File Input

**Interface Type**: File system read

**Format**: Comma-Separated Values (CSV)

**Encoding**: UTF-8

**Required Columns**:
-`Email`: User email address (primary user identifier)
-`Entitlement Display Name`: LDAP Distinguished Name containing group membership

**Optional Columns**: Additional columns may be present and are ignored

**Data Volume**: Optimized for up to 100,000 rows

**Validation**:
- Header row required with column names
- Each row must have values for required columns
- Email addresses must be valid format (RFC 5322)
- Entitlement Display Name must be valid LDAP DN (RFC 4514)

**Error Handling**:
- Malformed CSV rejected with parse error
- Missing required columns rejected with validation error
- Invalid data types logged and skipped
- Duplicate entries deduplicated automatically

---

#### SI-003: Environment Configuration Files

**Interface Type**: File system read

**File Locations** (in priority order):
1. Custom path specified by`DOTENV_PATH`environment variable
2.`secrets/.env`(preferred for credential separation)
3.`.env`(project root)

**Format**: KEY=VALUE pairs, one per line

**Required Variables**:
-`TENANT_ID`: F5 XC tenant identifier
- Authentication variables (one set required):
  -`VOLT_API_P12_FILE`+`VES_P12_PASSWORD`(P12 certificate)
  -`VOLT_API_CERT_FILE`+`VOLT_API_CERT_KEY_FILE`(PEM certificates)
  -`XC_API_TOKEN`(API token string)

**Optional Variables**:
-`XC_API_URL`: Custom API endpoint URL
-`DOTENV_PATH`: Custom .env file location
-`HTTP_PROXY`,`HTTPS_PROXY`: Proxy configuration
-`REQUESTS_CA_BUNDLE`: Custom CA bundle path

**Security**: .env files must not be committed to version control (.gitignore enforcement)

---

#### SI-004: Logging Output

**Interface Type**: File system write and console output

**Format**: Structured text log messages

**Log Levels**:
- DEBUG: Detailed diagnostic information
- INFO: General informational messages (default)
- WARNING: Warning messages (non-fatal issues)
- ERROR: Error messages (operation failures)

**Log Destinations**:
- Console (stdout/stderr) for user-facing messages
- Optional file logging (configurable)
- Structured format suitable for log aggregation tools

**Content Requirements**:
- Timestamps for all log entries
- Log level indicator
- Contextual information (operation, resource identifiers)
- No sensitive data (passwords, tokens, keys)
- Error stack traces for debugging

---

### 4.4 Communications Interfaces

#### CI-001: HTTPS/TLS Communication

**Protocol**: HTTPS (HTTP over TLS)

**TLS Version**: TLS 1.2 minimum, TLS 1.3 recommended

**Port**: TCP 443 (HTTPS)

**Directionality**: Outbound only (client to F5 XC API servers)

**Certificate Validation**: Enabled by default (can be disabled for staging with appropriate warnings)

**Client Authentication**: TLS client certificates (P12 or PEM format) or HTTP header API token

**Connection Pooling**: Enabled via urllib3 connection pool for performance

**Timeouts**:
- Connection timeout: 10 seconds (default)
- Read timeout: Configurable via`--timeout`flag (default 30 seconds)

**Retry Strategy**:
- Automatic retry on transient failures (connection errors, timeouts, HTTP 5xx/429)
- Exponential backoff with configurable parameters
- Maximum retry attempts: Configurable via`--max-retries`flag (default 3)

**Proxy Support**:
- HTTP_PROXY environment variable for HTTP proxy
- HTTPS_PROXY environment variable for HTTPS proxy
- Proxy authentication supported via URL-embedded credentials

---

## 5. Non-Functional Requirements

### 5.1 Performance Requirements

#### NFR-PERF-001: CSV Processing Performance

**Requirement**: System MUST process CSV files up to 100,000 rows in under 60 seconds (excluding network I/O).

**Rationale**: Large enterprise AD exports require efficient processing to maintain reasonable execution times.

**Measurement**: Time from CSV parse start to group aggregation completion.

**Testing**: Performance test with synthetic CSV of 100,000 rows; verify processing time <60s on reference hardware (2-core CPU, 4GB RAM).

---

#### NFR-PERF-002: API Operation Throughput

**Requirement**: System SHOULD achieve minimum throughput of 10 API operations per second under normal network conditions.

**Rationale**: Reasonable throughput ensures large synchronization jobs complete in acceptable timeframes.

**Measurement**: API operations per second measured over full sync operation.

**Testing**: Integration test with mock API; measure operations/second for 1000-group sync.

---

#### NFR-PERF-003: Memory Footprint

**Requirement**: System MUST operate within 512MB memory footprint for CSV files up to 10,000 rows.

**Rationale**: Enables execution in resource-constrained environments (containers, CI/CD runners).

**Measurement**: Peak resident memory (RSS) during sync operation.

**Testing**: Memory profiling during test execution; verify peak memory <512MB.

---

#### NFR-PERF-004: Dry-Run Response Time

**Requirement**: Dry-run validation MUST complete within 5 seconds for typical CSV files (<1000 rows).

**Rationale**: Fast dry-run feedback enables rapid validation cycles during CSV preparation.

**Measurement**: Time from command invocation to dry-run summary display.

**Testing**: Performance test with 1000-row CSV; verify dry-run time <5s.

---

### 5.2 Safety Requirements

#### NFR-SAFE-001: Data Loss Prevention

**Requirement**: System MUST implement safeguards against unintended data deletion:
- Prune operations require explicit`--prune`flag
- Dry-run mode available for pre-validation
- Deletion operations logged with sufficient detail for audit/recovery

**Rationale**: Prevents accidental deletion of resources due to CSV omissions or errors.

**Verification**: Manual test of prune operations; verify explicit flag requirement and logging detail.

---

#### NFR-SAFE-002: Credential Protection

**Requirement**: System MUST protect credentials from exposure:
- Private keys stored with mode 600 (owner read/write only)
- Passwords never logged or displayed
- API tokens redacted from log output
- Temporary credential files cleaned up on exit

**Rationale**: Prevents credential leakage through filesystem permissions, logs, or abandoned temp files.

**Verification**: Security audit of file permissions, log output, and temp file cleanup.

---

#### NFR-SAFE-003: Atomic Operations

**Requirement**: System SHOULD use atomic file operations where possible to prevent partial writes and race conditions.

**Rationale**: Ensures credential files are either fully written or not present; prevents corruption.

**Verification**: Integration test with interrupted file operations; verify no partial files.

---

#### NFR-SAFE-004: Fail-Safe Defaults

**Requirement**: System MUST use safe defaults for all operations:
- Dry-run mode does not require flag (operations default to dry-run)
- Prune requires explicit opt-in (default: no deletions)
- SSL verification enabled by default (disable only with explicit configuration)

**Rationale**: Safe defaults prevent unintended consequences from missing configuration.

**Verification**: Unit tests verifying default behavior; manual testing of default operations.

---

### 5.3 Security Requirements

#### NFR-SEC-001: Authentication Enforcement

**Requirement**: System MUST enforce authentication for all F5 XC API operations:
- Valid credentials required (P12, PEM, or token)
- Missing credentials cause immediate failure
- Invalid credentials detected with preflight API call
- Authentication errors logged without exposing credentials

**Rationale**: Prevents unauthorized access to F5 XC platform resources.

**Verification**: Integration tests with missing/invalid credentials; verify authentication enforcement.

---

#### NFR-SEC-002: Transport Security

**Requirement**: System MUST use TLS/SSL for all API communications:
- HTTPS protocol enforced (HTTP rejected)
- TLS 1.2 minimum version
- Certificate validation enabled by default
- Custom CA bundles supported for private CAs

**Rationale**: Protects data in transit from eavesdropping and tampering.

**Verification**: Network traffic inspection; verify TLS usage and version.

---

#### NFR-SEC-003: Credential Storage Security

**Requirement**: System MUST securely store credentials:
- Certificates and keys stored with mode 600 permissions
- .env files excluded from version control (.gitignore)
- No credentials in code or committed configuration
- CI/CD secrets stored in encrypted secret management systems

**Rationale**: Prevents credential exposure through code repositories or filesystem access.

**Verification**: Security audit of file permissions, .gitignore configuration, code review.

---

#### NFR-SEC-004: Audit Logging

**Requirement**: System MUST log all operations with sufficient detail for security audit:
- All API operations logged (create, update, delete)
- Resource identifiers included in logs
- Success/failure status recorded
- Timestamps in UTC

**Rationale**: Enables security incident investigation and compliance auditing.

**Verification**: Review log output for audit completeness; test log aggregation compatibility.

---

#### NFR-SEC-005: Input Validation

**Requirement**: System MUST validate all inputs to prevent injection attacks:
- CSV parsing with proper escaping
- LDAP DN parsing with RFC compliance
- Environment variables sanitized before use
- API inputs validated before transmission

**Rationale**: Prevents injection attacks (CSV injection, command injection, etc.).

**Verification**: Security testing with malicious inputs (CSV injection payloads, special characters).

---

#### NFR-SEC-006: Secrets Management

**Requirement**: System MUST prevent secrets from appearing in logs or output:
- Passwords redacted in logs
- API tokens masked in error messages
- Certificate contents not logged
- Environment variables with secrets (PASSWORD, TOKEN, KEY) automatically redacted

**Rationale**: Prevents credential leakage through log aggregation systems or console output.

**Verification**: Log review for secret patterns; automated secret scanning in CI/CD.

---

### 5.4 Software Quality Attributes

#### NFR-QUAL-001: Reliability (Availability)

**Requirement**: System SHOULD achieve 99.9% success rate for synchronization operations under normal conditions (excluding F5 XC API availability).

**Rationale**: High reliability ensures consistent identity synchronization for production use.

**Measurement**: (Successful syncs / Total sync attempts) × 100 over 30-day period.

**Testing**: Long-running stability test with periodic sync operations; measure success rate.

---

#### NFR-QUAL-002: Maintainability (Modifiability)

**Requirement**: System MUST be designed for maintainability:
- Modular architecture with clear separation of concerns
- Comprehensive inline documentation
- Type hints for all public functions
- Unit test coverage ≥90% for core modules

**Rationale**: Enables efficient bug fixes, feature additions, and long-term maintenance.

**Verification**: Code quality metrics (cyclomatic complexity, coupling, cohesion); coverage reports.

---

#### NFR-QUAL-003: Usability (Learnability)

**Requirement**: System SHOULD enable new users to perform successful dry-run sync within 15 minutes of initial setup.

**Rationale**: Low learning curve enables rapid adoption across diverse user skill levels.

**Measurement**: Time from clone repository to successful dry-run execution (user study).

**Testing**: Usability testing with representative users; measure time to first success.

---

#### NFR-QUAL-004: Portability

**Requirement**: System MUST operate on multiple platforms:
- Linux (Ubuntu 20.04+, RHEL 8+, Debian 11+)
- macOS (10.15+, Intel and Apple Silicon)
- Windows (via WSL2)

**Rationale**: Supports diverse enterprise infrastructure environments.

**Verification**: Integration testing on each supported platform; CI/CD pipeline validation.

---

#### NFR-QUAL-005: Testability

**Requirement**: System MUST be designed for testability:
- Dependency injection for external services (API client, filesystem)
- Mock-friendly interfaces
- Deterministic behavior for given inputs
- Test isolation (no shared state between tests)

**Rationale**: Enables comprehensive automated testing for reliability and regression prevention.

**Verification**: Unit test execution time <30 seconds; integration test mocking effectiveness.

---

#### NFR-QUAL-006: Observability

**Requirement**: System MUST provide comprehensive observability:
- Structured logging with contextual information
- Execution metrics (time, operation counts, error rates)
- Configurable log levels for debugging
- Integration with log aggregation systems (JSON output option)

**Rationale**: Enables operational monitoring, debugging, and performance analysis.

**Verification**: Log output review; integration with log aggregation tools (Splunk, ELK, CloudWatch).

---

#### NFR-QUAL-007: Recoverability

**Requirement**: System SHOULD support recovery from transient failures:
- Automatic retry with exponential backoff
- Stateless execution (re-running with same CSV produces same result)
- Clear error messages for manual intervention
- Idempotent operations (safe to retry)

**Rationale**: Reduces operational burden for transient failures; enables automated recovery.

**Verification**: Fault injection testing; verify automatic recovery from simulated failures.

---

#### NFR-QUAL-008: Scalability

**Requirement**: System SHOULD scale to handle growing data volumes:
- Linear time complexity O(n) for CSV processing
- Constant memory overhead (no memory leaks)
- Tested with up to 100,000 rows
- Performance degradation <10% from 1,000 to 100,000 rows (per row)

**Rationale**: Supports enterprise growth without tool replacement.

**Verification**: Performance testing with increasing data volumes; memory leak detection.

---

## 6. Data Requirements

### 6.1 Data Model

#### 6.1.1 Entities

##### Entity: Group

**Description**: Represents an F5 XC user group derived from Active Directory group membership.

**Attributes**:
-`name`(string, required): Group identifier, extracted from LDAP DN Common Name
- Pattern:`^[A-Za-z0-9_-]+$`
- Length: 1-128 characters
- Example:`Admins`,`Dev_Team`,`QA-Engineers`

-`description`(string, optional): Human-readable description
- Default: Empty string
- Future enhancement: Could map from AD group description

-`users`(array of strings, required): List of user email addresses who are members
- Format: Valid email addresses (RFC 5322)
- Derived from: Aggregation of CSV`Email`column for rows with matching group DN
- Example:`["alice@example.com", "bob@example.com"]`

-`namespace`(string, required): F5 XC namespace for group
- Fixed value:`system`
- Not configurable by user

-`roles`(array of strings, optional): RBAC role assignments
- Out of scope for current specification
- Reserved for future enhancement

**Constraints**:
- Group name must be unique within namespace
- Group must have at least one user (groups with zero users logged as warnings)
- Users in group must exist in F5 XC (auto-created if needed)

---

##### Entity: User

**Description**: Represents an F5 XC user, typically auto-created during group synchronization.

**Attributes**:
-`email`(string, required): User identifier and contact email
- Format: Valid email address (RFC 5322)
- Example:`alice.anderson@example.com`
- Serves as primary key

-`name`(string, optional): User's full name
- Source: Could be derived from CSV`User Display Name`column (future enhancement)
- Current behavior: Not set during auto-creation

-`status`(enum, optional): User account status
- Values:`active`,`inactive`,`pending`
- Current behavior: Not explicitly managed by tool

**Constraints**:
- Email address must be unique across F5 XC platform
- User auto-created when adding to group if not exists
- Users only deleted when`--prune`flag used and user not in any CSV group

---

##### Entity: CSVRow

**Description**: Represents a single row in the Active Directory CSV export.

**Attributes**:
-`User Name`(string): Active Directory username (not used in current implementation)
-`Email`(string, required): User email address
- Format: Valid email address
- Used as: User identifier in F5 XC

-`Entitlement Display Name`(string, required): LDAP Distinguished Name of group
- Format: LDAP DN per RFC 4514
- Example:`CN=Admins,OU=Groups,DC=example,DC=com`
- Processing: CN component extracted to derive group name

-`User Display Name`(string): User's full name (not currently used)
-`Application Name`(string): Application context (not currently used)
- Additional columns: Present in AD exports but not processed by tool

**Processing Logic**:
1. Parse CSV row by row
2. Extract`Email`and`Entitlement Display Name`columns
3. Parse`Entitlement Display Name`as LDAP DN
4. Extract CN component as group name
5. Aggregate:`group_name → [email1, email2, ...]`

---

##### Entity: Config

**Description**: Runtime configuration for tool execution.

**Attributes**:
-`tenant_id`(string, required): F5 XC tenant identifier
- Source:`TENANT_ID`environment variable
- Example:`acme-corp`

-`api_url`(string, optional): F5 XC API base URL
- Source:`XC_API_URL`environment variable or derived from`tenant_id`
- Default:`https://{tenant_id}.console.ves.volterra.io`
- Example:`https://acme-corp.staging.volterra.us`

-`auth`(object, required): Authentication credentials (exactly one method)
  -`p12_file`(string): Path to P12 certificate file
  -`p12_password`(string): P12 file password
  -`cert_file`(string): Path to PEM certificate file
  -`key_file`(string): Path to PEM private key file
  -`api_token`(string): API authentication token

-`dry_run`(boolean): Simulation mode flag
- Default: false
- Source:`--dry-run`CLI flag

-`prune`(boolean): Enable resource deletion
- Default: false
- Source:`--prune`CLI flag

-`log_level`(enum): Logging verbosity
- Values:`debug`,`info`,`warning`,`error`
- Default:`info`
- Source:`--log-level`CLI flag

-`max_retries`(integer): Maximum retry attempts
- Default: 3
- Range: 1-10
- Source:`--max-retries`CLI flag

-`timeout`(integer): HTTP timeout in seconds
- Default: 30
- Range: 5-300
- Source:`--timeout`CLI flag

---

#### 6.1.2 Relationships

**CSV to Groups** (1:N):
- One CSV file contains multiple group memberships
- Multiple CSV rows with same`Entitlement Display Name`represent multiple users in same group

**Groups to Users** (N:M):
- Each group contains multiple users
- Each user can be member of multiple groups
- Relationship derived from CSV aggregation

**Groups to Namespace** (N:1):
- All groups belong to`system`namespace
- Namespace is implicit, not derived from CSV

---

### 6.2 CSV Input Format

#### 6.2.1 Required CSV Structure

**File Format**: Comma-Separated Values (CSV)

**Encoding**: UTF-8

**Header Row**: Required (first row contains column names)

**Delimiter**: Comma (`,`)

**Quote Character**: Double quote (`"`)

**Escape**: Doubled quote (`""`) for embedded quotes

**Line Ending**: LF (`\n`) or CRLF (`\r\n`)

---

#### 6.2.2 Required Columns

| Column Name | Data Type | Required | Validation | Example |
|-------------|-----------|----------|------------|---------|
|`Email`| string | Yes | Valid email format (RFC 5322) |`alice.anderson@example.com`|
|`Entitlement Display Name`| string | Yes | Valid LDAP DN with CN component |`CN=Admins,OU=Groups,DC=example,DC=com`|

**Additional Columns**: Any additional columns present in CSV are ignored by the tool. Common additional columns include:
-`User Name`: Active Directory username
-`User Display Name`: User's full name
-`Application Name`: Application context
-`Sox`: SOX compliance flag
-`Job Title`,`Manager Email`, etc.: Organizational metadata

---

#### 6.2.3 CSV Example

```csv
"User Name","Login ID","User Display Name","Email","Entitlement Display Name","Application Name"
"USER001","CN=USER001,OU=Users,DC=example,DC=com","Alice Anderson","alice.anderson@example.com","CN=Admins,OU=Groups,DC=example,DC=com","Active Directory"
"USER002","CN=USER002,OU=Users,DC=example,DC=com","Bob Smith","bob.smith@example.com","CN=Admins,OU=Groups,DC=example,DC=com","Active Directory"
"USER003","CN=USER003,OU=Users,DC=example,DC=com","Carol White","carol.white@example.com","CN=Developers,OU=Groups,DC=example,DC=com","Active Directory"
```

**Result**: Two groups created:
-`Admins`with users:`alice.anderson@example.com`,`bob.smith@example.com`
-`Developers`with users:`carol.white@example.com`

---

### 6.3 Data Transformations

#### 6.3.1 LDAP DN to Group Name Extraction

**Input**: LDAP Distinguished Name from`Entitlement Display Name`column

**Process**:
1. Parse DN string according to RFC 4514 using`ldap3`library
2. Extract first Common Name (CN) component
3. Validate against group name pattern`^[A-Za-z0-9_-]+$`
4. Validate length ≤128 characters

**Examples**:

| Input DN | Extracted Group Name | Valid |
|----------|---------------------|-------|
|`CN=Admins,OU=Groups,DC=example,DC=com`|`Admins`| ✅ Yes |
|`CN=Dev_Team,OU=IT,OU=Groups,DC=example,DC=com`|`Dev_Team`| ✅ Yes |
|`CN=QA-Engineers,OU=Groups,DC=example,DC=com`|`QA-Engineers`| ✅ Yes |
|`CN=Group (Test),OU=Groups,DC=example,DC=com`|`Group (Test)`| ❌ No (invalid chars) |
|`CN=Users,CN=Admin,OU=Groups,DC=example,DC=com`|`Users`| ✅ Yes (first CN) |

**Error Handling**:
- Malformed DN: Log error, skip row
- Missing CN component: Log error, skip row
- Invalid characters: Log error, skip row
- Name too long (>128 chars): Log error, skip row

---

#### 6.3.2 Email Aggregation by Group

**Input**: CSV rows with`Email`and`Entitlement Display Name`columns

**Process**:
1. Parse all CSV rows
2. Extract group name from each`Entitlement Display Name`
3. Create mapping:`group_name → [email1, email2, ...]`
4. Deduplicate emails within each group
5. Validate email format (RFC 5322)
6. Filter out invalid/empty emails

**Example Transformation**:

**Input CSV**:

```csv
Email,Entitlement Display Name
alice@example.com,"CN=Admins,OU=Groups,DC=example,DC=com"
bob@example.com,"CN=Admins,OU=Groups,DC=example,DC=com"
alice@example.com,"CN=Admins,OU=Groups,DC=example,DC=com"
carol@example.com,"CN=Developers,OU=Groups,DC=example,DC=com"
```

**Output Mapping**:

```python
{
  "Admins": ["alice@example.com", "bob@example.com"],  # Deduplicated
  "Developers": ["carol@example.com"]
}
```

---

#### 6.3.3 Group Object Construction

**Input**: Aggregated group membership mapping

**Process**:
1. For each group name in mapping:
2. Create F5 XC group object:

   ```json
   {
     "name": "<group_name>",
     "description": "",
     "users": ["<email1>", "<email2>"],
     "namespace": "system"
   }
   ```

3. Validate group object against F5 XC API schema
4. Return list of group objects

**Validation**:
- Group name matches pattern and length constraints
- Users array not empty (warn if empty, don't create)
- All emails are valid format

---

### 6.4 Data Validation Rules

#### 6.4.1 CSV Validation

**Rule CSV-001**: CSV file MUST contain header row with required columns

**Validation**:
- First row parsed as header
- Column names checked for`Email`and`Entitlement Display Name`
- Case-insensitive column name matching
- Missing columns cause immediate error with clear message

---

#### 6.4.2 Email Validation

**Rule EMAIL-001**: Email addresses MUST conform to RFC 5322 format

**Validation Pattern**: Standard email regex pattern

```regex
^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
```

**Invalid Examples**:
- Missing @ symbol:`user.example.com`
- Multiple @ symbols:`user@@example.com`
- Invalid domain:`user@.com`
- Empty string:``

**Error Handling**: Invalid emails logged and excluded from group membership

---

#### 6.4.3 LDAP DN Validation

**Rule DN-001**: Entitlement Display Name MUST be valid LDAP Distinguished Name with CN component

**Validation**:
- Parse using`ldap3.utils.dn.parse_dn()`library function
- Extract CN component from parsed DN
- Verify CN component exists
- Handle special characters and escaping per RFC 4514

**Invalid Examples**:
- Missing CN:`OU=Groups,DC=example,DC=com`
- Malformed:`Admins`
- Empty:``

**Error Handling**: Invalid DNs logged and row skipped

---

#### 6.4.4 Group Name Validation

**Rule NAME-001**: Group names MUST match pattern`^[A-Za-z0-9_-]+$`

**Valid Characters**:
- Alphanumeric:`A-Z`,`a-z`,`0-9`
- Hyphen:`-`
- Underscore:`_`

**Invalid Characters**:
- Spaces:``
- Special characters:`@`,`#`,`$`,`%`,`(`,`)`, etc.

**Rule NAME-002**: Group names MUST be 1-128 characters in length

**Error Handling**: Invalid group names logged and group creation skipped

---

#### 6.4.5 Configuration Validation

**Rule CONFIG-001**: Tenant ID MUST be non-empty string

**Rule CONFIG-002**: Exactly ONE authentication method MUST be configured (P12, PEM, or Token)

**Rule CONFIG-003**: API URL MUST use HTTPS protocol

**Rule CONFIG-004**: Numeric parameters (timeout, max_retries) MUST be within valid ranges

**Error Handling**: Configuration validation occurs at startup; invalid configuration causes immediate failure with error message listing issues

---

## 7. Quality Attributes

### 7.1 Testability

#### 7.1.1 Unit Test Requirements

**Requirement**: All core modules MUST have ≥90% code coverage with unit tests.

**Scope**: Unit tests cover individual functions and classes in isolation.

**Key Modules**:
- CSV parsing and validation
- LDAP DN extraction
- Email validation and aggregation
- Group object construction
- Configuration loading
- Retry logic

**Testing Framework**: pytest with coverage plugin

**Mocking Strategy**: Use unittest.mock for external dependencies (filesystem, API client, environment variables)

**Test Organization**: Tests organized in`tests/unit/`directory mirroring`src/`structure

---

#### 7.1.2 Integration Test Requirements

**Requirement**: All external interfaces MUST have integration tests with mocked external services.

**Scope**: Integration tests verify interaction between components with mocked external dependencies.

**Key Integration Points**:
- F5 XC API client (mocked API responses)
- CSV file reading (temporary test files)
- Environment configuration loading
- Retry and backoff behavior
- End-to-end sync operations

**Testing Framework**: pytest with requests-mock for API mocking

**Test Organization**: Tests organized in`tests/integration/`directory

**Test Data**: Synthetic CSV files and API response fixtures in`tests/fixtures/`

---

#### 7.1.3 End-to-End Test Requirements

**Requirement**: Complete synchronization workflows MUST be tested end-to-end with representative data.

**Test Scenarios**:
1. **Happy Path**: Full sync with creates, updates, no errors
2. **Prune Operations**: Sync with --prune flag, verify deletions
3. **Error Handling**: Sync with API failures, verify error recovery
4. **Dry-Run**: Dry-run mode, verify no API calls
5. **Large Dataset**: Performance test with 10,000+ rows

**Testing Framework**: pytest with docker-compose for optional F5 XC mock server

**Test Organization**: Tests in`tests/e2e/`directory

---

### 7.2 Traceability

#### 7.2.1 Requirements Traceability Matrix

| Requirement ID | Test Coverage | Implementation | Documentation |
|---------------|---------------|----------------|---------------|
| FR-SYNC-001 | ✅ Unit |`cli.py:validate_csv()`| Section 3.1 |
| FR-SYNC-002 | ✅ Unit |`ldap_utils.py:extract_cn()`| Section 3.1 |
| FR-ENV-001 | ✅ Integration |`cli.py:_load_configuration()`| Section 3.2 |
| FR-RETRY-001 | ✅ Unit |`sync_service.py:__init__()`| Section 3.3 |
| FR-UX-001 | ✅ Integration |`cli.py:sync()`| Section 3.4 |
| FR-SETUP-001 | ✅ Integration |`setup_xc_credentials.sh`| Section 3.5 |
| FR-PRUNE-001 | ✅ Integration |`cli.py:sync()`| Section 3.6 |

**Full Traceability Matrix**: Complete matrix maintained in`docs/traceability-matrix.md`

---

#### 7.2.2 Change Traceability

**Requirement**: All specification changes MUST be documented with:
- Change description
- Rationale
- Impact assessment
- Affected requirements
- Implementation status

**Change Log Location**: Appendix D - Change History

**Version Control**: Specification versions tracked in git with semantic versioning (MAJOR.MINOR.PATCH)

---

### 7.3 Maintainability

#### 7.3.1 Code Quality Standards

**Requirement**: All code MUST meet quality standards enforced by automated tooling:

1. **Linting** (ruff): No violations at default strictness
2. **Formatting** (black): Consistent formatting throughout
3. **Type Checking** (mypy): Type hints for all public functions, strict mode enabled
4. **Complexity**: Cyclomatic complexity ≤10 per function
5. **Documentation**: Docstrings for all public functions, classes, modules

**Enforcement**: Pre-commit hooks run all quality checks before commit

**Measurement**: Quality metrics tracked in CI/CD pipeline

---

#### 7.3.2 Documentation Standards

**Requirement**: All code MUST be documented according to standards:

1. **Module Docstrings**: Purpose, key classes/functions, usage examples
2. **Class Docstrings**: Purpose, attributes, usage patterns
3. **Function Docstrings**: Purpose, parameters, return values, exceptions, examples (Google style)
4. **Inline Comments**: Explain complex logic, design decisions, workarounds

**Example Function Docstring**:

```python
def extract_cn(ldap_dn: str) -> str:
    """Extract Common Name from LDAP Distinguished Name.

    Args:
        ldap_dn: LDAP Distinguished Name string (RFC 4514 format)

    Returns:
        Common Name (CN) component extracted from DN

    Raises:
        ValueError: If DN is malformed or missing CN component

    Example:
        >>> extract_cn("CN=Admins,OU=Groups,DC=example,DC=com")
        'Admins'
    """
```

---

#### 7.3.2 Modularity Requirements

**Requirement**: System MUST be organized into logical modules with clear responsibilities:

1. **CLI Module** (`cli.py`): Command-line interface, argument parsing, main entry point
2. **Client Module** (`client.py`): F5 XC API client, HTTP communication, authentication
3. **Sync Service** (`sync_service.py`): Group synchronization business logic
4. **User Sync Service** (`user_sync_service.py`): User synchronization business logic
5. **CSV Parser** (`csv_parser.py`): CSV parsing, validation, LDAP DN extraction
6. **Config Module** (`config.py`): Configuration loading, validation
7. **Models** (`models.py`): Data models (Group, User, Config)

**Dependency Rules**:
- CLI depends on Sync Service and Client
- Sync Service depends on Client
- All modules depend on Models
- No circular dependencies
- External dependencies abstracted through interfaces

---

## 8. Implementation Guidance for Production Teams

This section provides comprehensive guidance for production teams implementing the XC Group Sync tool, including feature priorities, dependencies, operational workflows, and deployment scenarios.

### 8.1 Feature Implementation Roadmap

#### 8.1.1 Implementation Priority Classification

Features are classified by priority to guide implementation sequencing:

**P0 (Critical - MVP Requirements)**:
- Feature 1: CSV-Driven Group Synchronization (Section 3.1)
- Feature 2: Configuration and Environment Management (Section 3.2)

**P1 (High Priority - Production Essential)**:
- Feature 3: Advanced Retry and Backoff Mechanisms (Section 3.3)
- Feature 4: User Experience and CLI Feedback (Section 3.4)
- Feature 5: Credential Setup and CI/CD Integration (Section 3.5)

**P2 (Medium Priority - Operational Enhancements)**:
- Feature 6: Resource Pruning and Reconciliation (Section 3.6)

#### 8.1.2 Recommended Implementation Sequence

**Phase 1: Minimum Viable Product (MVP) - 2-3 weeks**

**Week 1: Foundation**
1. Implement data models (Section 6.1)
   - Group, User, CSVRow, Config entities
   - Validation rules

2. Implement CSV parsing (FR-SYNC-001, FR-SYNC-002)
   - CSV schema validation
   - LDAP DN parsing with ldap3 library
   - Group name extraction and validation (FR-SYNC-003)

3. Implement configuration loading (Feature 2)
   - Hierarchical .env file loading (FR-ENV-001, FR-ENV-002)
   - Environment variable parsing
   - Configuration validation

**Week 2: Core Synchronization**
4. Implement F5 XC API client (Section 4.3)
- Authentication methods (P12, PEM, Token) (FR-ENV-004)
- HTTP client with urllib3
- Basic error handling

5. Implement group synchronization service (Feature 1)
   - Email aggregation by group (FR-SYNC-004)
   - Group creation (FR-SYNC-005)
   - Group updates (FR-SYNC-006)
   - User auto-creation (FR-SYNC-009)

6. Implement CLI interface (Section 4.1)
   - Basic command structure with Click
   - --csv flag for input
   - Error handling and exit codes

**Week 3: MVP Completion & Testing**
7. Implement dry-run mode (FR-SYNC-007)
- Dry-run flag handling
- Operation planning without execution
- Dry-run banners and output

8. Implement operation summaries (FR-SYNC-008)
   - Counter tracking (created/updated/deleted/unchanged/errors)
   - Summary display formatting

9. Integration testing
   - End-to-end sync scenarios
   - Mock API testing
   - CSV validation testing

**Validation Criteria for MVP**:
- ✅ Parse CSV with required columns
- ✅ Extract group names from LDAP DNs
- ✅ Connect to F5 XC API with authentication
- ✅ Create groups that don't exist
- ✅ Update groups with membership changes
- ✅ Dry-run shows planned operations without executing
- ✅ Summary displays accurate operation counts

---

**Phase 2: Production Readiness - 2-3 weeks**

**Week 4: Reliability & User Experience**
10. Implement retry mechanisms (Feature 3)
- Configurable retry parameters (FR-RETRY-001)
- Exponential backoff (FR-RETRY-002)
- Intelligent error classification (FR-RETRY-003)
- Selective retry application (FR-RETRY-004)

11. Implement enhanced CLI feedback (Feature 4)

- Execution time tracking (FR-UX-001)
- Pre-operation summaries (FR-UX-002)
- Enhanced error reporting (FR-UX-003, FR-UX-004)
- Dry-run banners (FR-UX-005)
- Completion confirmations (FR-UX-007)

**Week 5: Operational Automation**
12. Implement credential setup script (Feature 5)
- Environment detection from P12 filenames (FR-SETUP-001)
- Automatic .env generation (FR-SETUP-002)
- OpenSSL 3.x compatibility (FR-SETUP-003)
- Passwordless key extraction (FR-SETUP-004)
- Atomic file operations (FR-SETUP-005)

13. Implement CI/CD integration (Feature 5 continued)

- GitHub Actions workflow templates
- GitHub secrets configuration (FR-SETUP-006)
- P12 file auto-discovery (FR-SETUP-007)
- Multiple password input methods (FR-SETUP-008)

14. Implement advanced configuration (Feature 2 continued)

- API URL configuration (FR-ENV-003)
- Multi-environment support (FR-ENV-005)
- Staging environment warnings (FR-ENV-006)

**Week 6: Testing & Documentation**
15. Comprehensive testing
- Unit tests (≥90% coverage)
- Integration tests for all features
- End-to-end scenarios
- Performance testing (NFR-PERF requirements)

16. Security hardening

- Credential protection verification (NFR-SEC requirements)
- Input validation (NFR-SEC-005)
- Audit logging (NFR-SEC-004)

17. Documentation completion

- README with examples
- API documentation
- Troubleshooting guides

**Validation Criteria for Production Readiness**:
- ✅ Transient failures automatically retried
- ✅ Execution time and operation counts displayed
- ✅ Setup script automates credential extraction
- ✅ GitHub Actions workflow deploys successfully
- ✅ All non-functional requirements verified
- ✅ Security audit passed

---

**Phase 3: Advanced Features - 1-2 weeks**

**Week 7-8: Resource Management**
18. Implement pruning operations (Feature 6)
- Explicit opt-in requirement (FR-PRUNE-001)
- Orphaned group detection (FR-PRUNE-002)
- Orphaned user detection (FR-PRUNE-003)
- Separate prune reporting (FR-PRUNE-004)
- Prune operation safety (FR-PRUNE-005)

19. Final integration & validation

- Full sync + prune workflows
- Large dataset testing (100K+ rows)
- Production deployment validation

**Validation Criteria for Complete Implementation**:
- ✅ Prune flag deletes orphaned resources
- ✅ Separate prune summaries displayed
- ✅ Large datasets processed efficiently
- ✅ All 64 requirements verified

---

### 8.2 Feature Dependency Matrix

Understanding feature dependencies helps teams parallelize work and identify critical paths.

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Feature Dependency Graph                      │
│                                                                   │
│  ┌──────────────────┐                                            │
│  │ Feature 2:       │ (Foundation - Required by all)             │
│  │ Configuration    │                                            │
│  │ & Environment    │                                            │
│  └────────┬─────────┘                                            │
│           │                                                       │
│           v                                                       │
│  ┌────────────────────────────────────────────────┐              │
│  │ Feature 1: CSV-Driven Group Synchronization   │ (Core MVP)   │
│  │ (Depends on: Feature 2)                        │              │
│  └────────┬──────────────┬────────────────────────┘              │
│           │              │                                        │
│           v              v                                        │
│  ┌────────────────┐  ┌──────────────────┐                       │
│  │ Feature 3:     │  │ Feature 4:       │ (Enhance core)        │
│  │ Retry/Backoff  │  │ UX & CLI         │                       │
│  │ (Depends on: 1)│  │ (Depends on: 1)  │                       │
│  └────────────────┘  └──────────────────┘                       │
│                                                                   │
│  ┌──────────────────┐                                            │
│  │ Feature 5:       │ (Independent - can parallel with 3,4)     │
│  │ Setup & CI/CD    │                                            │
│  │ (Depends on: 2)  │                                            │
│  └──────────────────┘                                            │
│                                                                   │
│  ┌──────────────────┐                                            │
│  │ Feature 6:       │ (Enhancement - requires 1,2,4)            │
│  │ Pruning          │                                            │
│  │ (Depends on:     │                                            │
│  │  1, 2, 4)        │                                            │
│  └──────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

**Dependency Details**:

| Feature | Depends On | Can Start After | Can Parallel With | Blocks |
|---------|-----------|-----------------|-------------------|--------|
| Feature 1 (CSV Sync) | Feature 2 | Week 1 complete | - | Features 3, 4, 6 |
| Feature 2 (Config) | None | Immediately | - | All features |
| Feature 3 (Retry) | Feature 1 | Week 2 complete | Features 4, 5 | None |
| Feature 4 (UX/CLI) | Feature 1 | Week 2 complete | Features 3, 5 | Feature 6 |
| Feature 5 (Setup) | Feature 2 | Week 1 complete | Features 3, 4 | None |
| Feature 6 (Pruning) | Features 1, 2, 4 | Week 5 complete | - | None |

**Critical Path**: Feature 2 → Feature 1 → Feature 4 → Feature 6

**Parallelization Opportunities**:
- Features 3 and 4 can be developed in parallel after Feature 1
- Feature 5 can be developed in parallel with Features 3 and 4
- Testing can occur in parallel with feature development

---

### 8.3 Operational Workflows

#### 8.3.1 Initial Setup Workflow

**Scenario**: DevOps engineer setting up tool for first time

**Prerequisites**:
- Python 3.9+ installed
- Access to F5 XC tenant with P12 certificate or API token
- CSV export from Active Directory

**Steps**:

1. **Clone Repository & Install**

   ```bash
   git clone https://github.com/organization/f5-xc-user-group-sync.git
   cd f5-xc-user-group-sync
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

2. **Run Credential Setup Script**

   ```bash
   # With P12 file in ~/Downloads
   ./scripts/setup_xc_credentials.sh

   # Or with explicit path
   ./scripts/setup_xc_credentials.sh --p12 /path/to/tenant.p12

   # Script will:
   # - Auto-detect environment (production/staging)
   # - Extract cert/key from P12
   # - Create secrets/.env with configuration
   # - Optionally configure GitHub secrets
   ```

3. **Verify Configuration**

   ```bash
   # Check secrets/.env was created
   cat secrets/.env

   # Should contain:
   # TENANT_ID=your-tenant
   # XC_API_URL=https://your-tenant.console.ves.volterra.io
   # VOLT_API_CERT_FILE=/path/to/cert.pem
   # VOLT_API_CERT_KEY_FILE=/path/to/key.pem
   ```

4. **Test with Dry-Run**

   ```bash
   xc_user_group_sync sync --csv User-Database.csv --dry-run

   # Should display:
   # - Dry-run banner
   # - Planned groups from CSV
   # - Existing groups in F5 XC
   # - Planned operations (create/update)
   # - Operation summary
   # - Execution time
   ```

5. **Execute First Sync**

   ```bash
   # After validating dry-run output
   xc_user_group_sync sync --csv User-Database.csv

   # Monitor output for errors
   # Verify success with operation summary
   ```

**Validation**:
- ✅ Configuration loaded successfully
- ✅ Dry-run shows expected operations
- ✅ Sync completes without errors
- ✅ Groups visible in F5 XC console

---

#### 8.3.2 Regular Synchronization Workflow

**Scenario**: IAM administrator performing periodic group sync

**Frequency**: Daily, weekly, or on-demand

**Steps**:

1. **Export Latest CSV from Active Directory**

   ```powershell
   # Active Directory export command (example)
   Get-ADGroupMember -Identity "All Groups" -Recursive |
     Export-Csv -Path "User-Database.csv" -NoTypeInformation
   ```

2. **Review CSV Changes**

   ```bash
   # Compare with previous export
   diff previous-export.csv User-Database.csv | head -20

   # Count groups and users
   csvcut -c "Entitlement Display Name" User-Database.csv | sort -u | wc -l
   csvcut -c "Email" User-Database.csv | sort -u | wc -l
   ```

3. **Perform Dry-Run Validation**

   ```bash
   xc_user_group_sync sync --csv User-Database.csv --dry-run

   # Review planned operations:
   # - New groups to create
   # - Groups with membership changes
   # - Expected user count changes
   ```

4. **Execute Synchronization**

   ```bash
   # Standard sync (create + update)
   xc_user_group_sync sync --csv User-Database.csv

   # Or with pruning (delete orphaned resources)
   xc_user_group_sync sync --csv User-Database.csv --prune
   ```

5. **Verify Results**

   ```bash
   # Check operation summary:
   # - created: New groups added
   # - updated: Groups with membership changes
   # - deleted: Orphaned groups removed (if --prune)
   # - unchanged: Groups matching CSV
   # - errors: Failed operations (investigate)

   # If errors > 0:
   # - Review error details in output
   # - Check F5 XC API logs
   # - Verify CSV data quality
   # - Retry failed operations if transient
   ```

6. **Validate in F5 XC Console** (Optional)
   - Log into F5 XC console
   - Navigate to IAM → User Groups
   - Spot-check random groups for correct membership
   - Verify new groups are present

**Validation**:
- ✅ CSV export contains latest AD data
- ✅ Dry-run shows expected changes
- ✅ Sync completes with errors=0
- ✅ Operation counts match expectations
- ✅ Spot-checks confirm accuracy

---

#### 8.3.3 Prune Operation Workflow

**Scenario**: Platform engineer performing full reconciliation to remove orphaned resources

**When to Prune**:
- After major organizational restructuring
- When cleaning up test/obsolete groups
- Quarterly reconciliation for audit compliance
- After decommissioning applications

**Steps**:

1. **Backup Current State** (Recommended)

   ```bash
   # Export current F5 XC groups for backup
   curl -X GET \
     "https://${TENANT_ID}.console.ves.volterra.io/api/web/namespaces/system/user_groups" \
     --cert ${VOLT_API_CERT_FILE} \
     --key ${VOLT_API_CERT_KEY_FILE} \
     > f5xc-groups-backup-$(date +%Y%m%d).json
   ```

2. **Dry-Run with Prune Flag**

   ```bash
   xc_user_group_sync sync --csv User-Database.csv --prune --dry-run

   # Carefully review prune section:
   # - Groups to be deleted (not in CSV)
   # - Users to be deleted (not in any CSV group)
   # - Verify these are truly orphaned/unwanted
   ```

3. **Validate Prune Targets**
   - Review list of resources to be deleted
   - Confirm with IAM team these are intended deletions
   - Check for production-critical groups
   - Verify no active users will lose access unintentionally

4. **Execute Prune Operation**

   ```bash
   # Only after validation!
   xc_user_group_sync sync --csv User-Database.csv --prune

   # Monitor both:
   # - Main sync summary (create/update)
   # - Prune summary (deleted counts)
   ```

5. **Post-Prune Verification**

   ```bash
   # Verify expected resources were deleted
   # Spot-check F5 XC console
   # Confirm no unintended deletions
   # Document deleted resources for audit trail
   ```

**Safety Considerations**:
- ⚠️ Prune is **DESTRUCTIVE** - deleted resources cannot be easily recovered
- ⚠️ Always dry-run first with --prune to preview deletions
- ⚠️ Coordinate with application owners before pruning
- ⚠️ Consider backup export before prune
- ⚠️ Start with small prune operations to build confidence

**Validation**:
- ✅ Dry-run prune list reviewed and approved
- ✅ Stakeholders notified of deletions
- ✅ Backup export completed
- ✅ Prune execution completed without unexpected deletions
- ✅ Audit log updated with prune operation

---

### 8.4 Deployment Scenarios

#### 8.4.1 Manual Execution (Development/Testing)

**Use Case**: Developers and IAM admins running tool manually for testing or one-off operations

**Setup**:

```bash
# Install locally
git clone <repo>
cd f5-xc-user-group-sync
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Configure credentials
./scripts/setup_xc_credentials.sh --p12 ~/Downloads/tenant.p12

# Run manually
xc_user_group_sync sync --csv User-Database.csv --dry-run
```

**Pros**:
- Simple setup
- Direct control
- Easy debugging
- Immediate feedback

**Cons**:
- Manual execution required
- No scheduling
- Requires local Python environment
- Credential management on individual machines

**Best For**: Development, testing, troubleshooting, one-off operations

---

#### 8.4.2 GitHub Actions (Recommended for GitHub Users)

**Use Case**: Automated synchronization triggered by CSV commits or scheduled runs

**Setup**:

1. **Configure GitHub Secrets**

   ```bash
   # Run setup script with GitHub secrets flag
   ./scripts/setup_xc_credentials.sh --p12 ~/Downloads/tenant.p12

   # Or manually create secrets in GitHub:
   # Settings → Secrets → Actions → New repository secret
   # - TENANT_ID: your-tenant
   # - XC_CERT: base64-encoded PEM certificate
   # - XC_CERT_KEY: base64-encoded PEM private key
   # Or:
   # - XC_P12: base64-encoded P12 file
   # - XC_P12_PASSWORD: P12 passphrase
   ```

2. **Create Workflow File** (`.github/workflows/xc-sync.yml`)

   ```yaml
   name: XC Group Sync

   on:
     schedule:
       - cron: '0 2 * * *'  # Daily at 2 AM UTC
     workflow_dispatch:      # Manual trigger
     push:
       paths:
         - 'User-Database.csv'

   jobs:
     sync:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3

         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.12'

         - name: Install dependencies
           run: |
             pip install -e .

         - name: Decode credentials
           run: |
             echo "${{ secrets.XC_CERT }}" | base64 -d > cert.pem
             echo "${{ secrets.XC_CERT_KEY }}" | base64 -d > key.pem

         - name: Sync groups (dry-run on PR)
           env:
             TENANT_ID: ${{ secrets.TENANT_ID }}
             VOLT_API_CERT_FILE: cert.pem
             VOLT_API_CERT_KEY_FILE: key.pem
           run: |
             if [ "${{ github.event_name }}" == "pull_request" ]; then
               xc_user_group_sync sync --csv User-Database.csv --dry-run
             else
               xc_user_group_sync sync --csv User-Database.csv
             fi
   ```

**Workflow Behavior**:
- **Scheduled**: Runs daily at 2 AM UTC automatically
- **On CSV Change**: Triggers when User-Database.csv committed to repository
- **Manual**: Can be triggered manually via GitHub Actions UI
- **Pull Request**: Runs dry-run for PR validation

**Pros**:
- Fully automated
- Integrated with GitHub workflow
- Scheduled execution
- No server maintenance
- Built-in secrets management
- Execution logs in GitHub Actions

**Cons**:
- Requires GitHub repository
- GitHub Actions minutes consumption
- CSV must be committed to repo (consider security)

**Best For**: Teams using GitHub, automated daily/weekly syncs, GitOps workflows

---

#### 8.4.3 Jenkins Pipeline

**Use Case**: Automated synchronization in Jenkins-based CI/CD environments

**Setup**:

1. **Configure Jenkins Credentials**
   - Navigate to: Manage Jenkins → Manage Credentials
   - Add credentials:
     -`TENANT_ID`: Secret text
     -`XC_CERT`: Secret file (PEM certificate)
     -`XC_CERT_KEY`: Secret file (PEM private key)
   - Or:`XC_P12`+`XC_P12_PASSWORD`

2. **Create Jenkins Pipeline** (`Jenkinsfile`)

   ```groovy
   pipeline {
     agent any

     triggers {
       cron('H 2 * * *')  // Daily at 2 AM
     }

     environment {
       TENANT_ID = credentials('xc-tenant-id')
       VOLT_API_CERT_FILE = credentials('xc-cert')
       VOLT_API_CERT_KEY_FILE = credentials('xc-cert-key')
     }

     stages {
       stage('Setup') {
         steps {
           sh '''
             python3 -m venv .venv
             . .venv/bin/activate
             pip install -e .
           '''
         }
       }

       stage('Dry-Run') {
         steps {
           sh '''
             . .venv/bin/activate
             xc_user_group_sync sync --csv User-Database.csv --dry-run
           '''
         }
       }

       stage('Sync') {
         when {
           branch 'main'
         }
         steps {
           sh '''
             . .venv/bin/activate
             xc_user_group_sync sync --csv User-Database.csv
           '''
         }
       }
     }

     post {
       always {
         archiveArtifacts artifacts: 'logs/*.log', allowEmptyArchive: true
       }
       failure {
         emailext (
           subject: "XC Group Sync Failed",
           body: "Sync operation failed. Check Jenkins logs.",
           to: "ops-team@example.com"
         )
       }
     }
   }
   ```

**Pipeline Behavior**:
- **Scheduled**: Runs daily at 2 AM
- **Dry-Run Stage**: Always validates before sync
- **Sync Stage**: Only runs on main branch
- **Post-Actions**: Archives logs, sends email on failure

**Pros**:
- Integrated with existing Jenkins infrastructure
- Flexible scheduling and triggers
- Built-in notification system
- Can integrate with other Jenkins jobs
- Supports complex pipeline logic

**Cons**:
- Requires Jenkins server
- More complex setup than GitHub Actions
- Need to manage Jenkins agent environment

**Best For**: Organizations with existing Jenkins infrastructure, complex CI/CD pipelines

---

#### 8.4.4 Cron Job (Linux Server)

**Use Case**: Scheduled execution on dedicated Linux server

**Setup**:

1. **Install on Server**

   ```bash
   # As service account
   cd /opt/xc-group-sync
   git clone <repo> .
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .

   # Configure credentials
   ./scripts/setup_xc_credentials.sh --p12 /secure/tenant.p12
   ```

2. **Create Wrapper Script** (`/opt/xc-group-sync/sync-wrapper.sh`)

   ```bash
   #!/bin/bash
   set -euo pipefail

   # Configuration
   SCRIPT_DIR="/opt/xc-group-sync"
   CSV_FILE="/data/exports/User-Database.csv"
   LOG_DIR="/var/log/xc-group-sync"
   LOG_FILE="${LOG_DIR}/sync-$(date +%Y%m%d-%H%M%S).log"

   # Create log directory
   mkdir -p "${LOG_DIR}"

   # Activate virtual environment
   cd "${SCRIPT_DIR}"
   source .venv/bin/activate

   # Run sync with logging
   {
     echo "=== XC Group Sync Started: $(date) ==="
     xc_user_group_sync sync --csv "${CSV_FILE}" \
       --log-level info 2>&1
     echo "=== XC Group Sync Completed: $(date) ==="
   } | tee -a "${LOG_FILE}"

   # Keep only last 30 days of logs
   find "${LOG_DIR}" -name "sync-*.log" -mtime +30 -delete

   # Send email on failure (optional)
   if [ ${PIPESTATUS[0]} -ne 0 ]; then
     echo "XC Group Sync failed. See ${LOG_FILE}" | \
       mail -s "XC Sync Failure" ops-team@example.com
   fi
   ```

3. **Configure Cron**

   ```bash
   # Edit crontab for service account
   sudo -u xc-sync-user crontab -e

   # Add cron entry (daily at 2 AM)
   0 2 * * * /opt/xc-group-sync/sync-wrapper.sh

   # Or weekly on Sunday at 2 AM
   0 2 * * 0 /opt/xc-group-sync/sync-wrapper.sh
   ```

**Pros**:
- Simple, reliable scheduling
- No external dependencies
- Full control over execution environment
- Suitable for isolated/air-gapped environments
- Low resource overhead

**Cons**:
- Manual server maintenance
- Need to manage log rotation
- Limited visibility/monitoring
- No built-in retry on server failures

**Best For**: On-premise deployments, air-gapped environments, simple scheduled execution

---

### 8.5 Testing and Validation Strategy

#### 8.5.1 Unit Testing Strategy

**Objective**: Verify individual components function correctly in isolation

**Scope**: All modules in`src/xc_user_group_sync/`

**Coverage Target**: ≥90% code coverage

**Key Test Areas**:

1. **CSV Parsing** (`test_csv_parser.py`)
   - Valid CSV with required columns
   - Missing required columns
   - Malformed CSV data
   - Empty CSV file
   - Large CSV files (performance)

2. **LDAP DN Extraction** (`test_ldap_utils.py`)
   - Valid LDAP DNs with single CN
   - DNs with multiple CNs (extract first)
   - DNs with special characters (escaped)
   - Malformed DNs (error handling)
   - DNs with Unicode characters

3. **Group Name Validation** (`test_validation.py`)
   - Valid group names (alphanumeric, hyphen, underscore)
   - Invalid characters (spaces, special chars)
   - Length validation (1-128 characters)
   - Empty strings
   - Unicode handling

4. **Configuration Loading** (`test_config.py`)
   - Hierarchical .env file loading
   - Environment variable precedence
   - Custom DOTENV_PATH
   - Missing configuration
   - Invalid configuration values

5. **Retry Logic** (`test_retry.py`)
   - Exponential backoff calculation
   - Retriable vs non-retriable errors
   - Max attempts enforcement
   - Backoff min/max bounds

**Testing Framework**: pytest with coverage plugin

**Example Test**:

```python
def test_extract_cn_valid_dn():
    """Test CN extraction from valid LDAP DN"""
    dn = "CN=Admins,OU=Groups,DC=example,DC=com"
    result = extract_cn(dn)
    assert result == "Admins"

def test_extract_cn_multiple_cns():
    """Test CN extraction when multiple CNs present"""
    dn = "CN=Users,CN=Admins,OU=Groups,DC=example,DC=com"
    result = extract_cn(dn)
    assert result == "Users"  # Should extract first CN

def test_extract_cn_malformed_dn():
    """Test error handling for malformed DN"""
    dn = "OU=Groups,DC=example,DC=com"  # Missing CN
    with pytest.raises(ValueError, match="No CN component"):
        extract_cn(dn)
```

**Running Unit Tests**:

```bash
# Run all unit tests with coverage
pytest tests/unit/ --cov=src/xc_user_group_sync --cov-report=html

# Run specific test file
pytest tests/unit/test_ldap_utils.py -v

# Run tests matching pattern
pytest -k "test_extract_cn" -v
```

---

#### 8.5.2 Integration Testing Strategy

**Objective**: Verify components work together correctly with mocked external services

**Scope**: End-to-end workflows with mocked F5 XC API

**Key Test Scenarios**:

1. **Complete Sync Workflow**
   - Parse CSV → Aggregate groups → Sync to mock API → Verify results
   - Test create, update, and unchanged operations
   - Verify operation counters accuracy

2. **Authentication Methods**
   - Test P12 authentication flow
   - Test PEM certificate authentication
   - Test API token authentication
   - Test authentication failure handling

3. **Retry Mechanism**
   - Mock transient failures (connection timeout, HTTP 503)
   - Verify retry attempts occur
   - Verify exponential backoff timing
   - Verify eventual success after retries

4. **Error Handling**
   - Mock permanent failures (HTTP 401, 404, 400)
   - Verify no retry occurs
   - Verify error reporting
   - Verify partial failure handling

5. **Dry-Run Mode**
   - Verify no API calls made
   - Verify planned operations displayed
   - Verify operation counts accurate

**Testing Framework**: pytest with requests-mock

**Example Integration Test**:

```python
@pytest.fixture
def mock_xc_api(requests_mock):
    """Mock F5 XC API responses"""
    requests_mock.get(
        "https://tenant.console.ves.volterra.io/api/web/namespaces/system/user_groups",
        json={"items": [{"name": "existing-group", "users": ["user1@example.com"]}]}
    )
    requests_mock.post(
        "https://tenant.console.ves.volterra.io/api/web/namespaces/system/user_groups",
        status_code=201
    )
    return requests_mock

def test_complete_sync_workflow(mock_xc_api, tmp_path):
    """Test complete sync workflow with mocked API"""
    # Create test CSV
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(
        "Email,Entitlement Display Name\n"
        "user1@example.com,\"CN=existing-group,OU=Groups,DC=example,DC=com\"\n"
        "user2@example.com,\"CN=new-group,OU=Groups,DC=example,DC=com\"\n"
    )

    # Run sync
    result = runner.invoke(cli, ['sync', '--csv', str(csv_file)])

    # Verify results
    assert result.exit_code == 0
    assert "created=1" in result.output  # new-group created
    assert "updated=1" in result.output  # existing-group updated

    # Verify API calls
    assert mock_xc_api.call_count == 3  # GET + POST + PUT
```

**Running Integration Tests**:

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run with API mock verification
pytest tests/integration/ --log-cli-level=DEBUG
```

---

#### 8.5.3 End-to-End Testing Strategy

**Objective**: Verify complete system functionality with real or near-real F5 XC environment

**Options**:

**Option 1: F5 XC Sandbox/Staging Environment** (Recommended)

```bash
# Configure for staging environment
export XC_API_URL="https://tenant.staging.volterra.us"
export TENANT_ID="test-tenant"
export VOLT_API_CERT_FILE="staging-cert.pem"
export VOLT_API_CERT_KEY_FILE="staging-key.pem"

# Run E2E test
pytest tests/e2e/ --e2e-env=staging
```

**Option 2: Mock F5 XC Server with Docker**

```bash
# Start mock F5 XC API server
docker-compose -f tests/e2e/docker-compose.yml up -d

# Run E2E tests against mock server
pytest tests/e2e/ --e2e-env=mock

# Cleanup
docker-compose -f tests/e2e/docker-compose.yml down
```

**Key E2E Test Scenarios**:

1. **First-Time Setup**
   - Run setup script with P12 file
   - Verify .env created correctly
   - Verify certificates extracted
   - Run first sync successfully

2. **Large Dataset Performance**
   - Generate synthetic CSV with 10,000+ rows
   - Measure execution time
   - Verify memory usage within limits
   - Validate all operations completed

3. **Prune Operation**
   - Create groups in F5 XC not in CSV
   - Run sync with --prune
   - Verify orphaned groups deleted
   - Verify CSV groups remain

4. **Error Recovery**
   - Simulate network interruptions
   - Verify retry mechanism works
   - Verify partial completion handling
   - Verify resumption succeeds

5. **Multi-Environment**
   - Test production configuration
   - Test staging configuration
   - Verify environment detection
   - Verify SSL warnings for staging

**Running E2E Tests**:

```bash
# Run all E2E tests (requires staging environment)
pytest tests/e2e/ --e2e-env=staging -v

# Run specific scenario
pytest tests/e2e/test_large_dataset.py -v

# Run with performance profiling
pytest tests/e2e/ --e2e-env=staging --profile
```

---

### 8.6 Troubleshooting Guide for Production Teams

#### 8.6.1 Common Issues and Resolutions

**Issue 1: Authentication Failures**

**Symptoms**:

```text
API error: Authentication failed - check credentials
HTTP 401 Unauthorized
```

**Possible Causes**:
1. Invalid or expired P12 certificate
2. Incorrect P12 password
3. Certificate not trusted by F5 XC
4. Incorrect API token

**Resolution Steps**:

```bash
# Verify certificate validity
openssl x509 -in secrets/cert.pem -noout -dates -subject

# Check certificate expiration
openssl x509 -in secrets/cert.pem -noout -checkend 0

# Re-extract certificate from P12 with correct password
./scripts/setup_xc_credentials.sh --p12 /path/to/new.p12

# Test connectivity
curl -X GET \
  "https://${TENANT_ID}.console.ves.volterra.io/api/web/namespaces/system/user_groups" \
  --cert ${VOLT_API_CERT_FILE} \
  --key ${VOLT_API_CERT_KEY_FILE}
```

---

**Issue 2: CSV Parsing Errors**

**Symptoms**:

```csv
Failed to parse CSV: Missing required column 'Email'
CSVParseError: Invalid format
```

**Possible Causes**:
1. Missing required columns
2. Incorrect CSV format (delimiter, encoding)
3. Malformed LDAP DNs
4. UTF-8 encoding issues

**Resolution Steps**:

```bash
# Verify CSV structure
head -5 User-Database.csv

# Check encoding
file -bi User-Database.csv  # Should show utf-8

# Verify required columns present
csvcut -n User-Database.csv | grep -E "Email|Entitlement Display Name"

# Validate LDAP DN format in sample rows
csvcut -c "Entitlement Display Name" User-Database.csv | head -10

# Convert encoding if needed
iconv -f ISO-8859-1 -t UTF-8 User-Database.csv > User-Database-utf8.csv
```

---

**Issue 3: Retry Exhausted / Persistent Failures**

**Symptoms**:

```text
Failed to create user user@example.com after 3 retries
RequestException: Connection timeout
```

**Possible Causes**:
1. Network connectivity issues
2. F5 XC API outage
3. Rate limiting (HTTP 429)
4. Firewall blocking HTTPS traffic

**Resolution Steps**:

```bash
# Test network connectivity
ping ${TENANT_ID}.console.ves.volterra.io
curl -I https://${TENANT_ID}.console.ves.volterra.io

# Check F5 XC status page
# https://status.f5.com/

# Increase timeout and retries
xc_user_group_sync sync --csv User-Database.csv \
  --timeout 60 \
  --max-retries 5

# Check for proxy/firewall issues
curl -v --proxy "" https://${TENANT_ID}.console.ves.volterra.io
```

---

**Issue 4: Staging SSL Certificate Verification Failures**

**Symptoms**:

```text
SSLError: certificate verify failed
Unable to establish SSL connection
```

**Possible Causes**:
1. Staging environment uses self-signed certificates
2. Custom CA not trusted by Python requests library

**Resolution Steps**:

```bash
# Option 1: Install staging CA certificate in system trust store (recommended)
# Linux:
sudo cp staging-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# macOS:
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain staging-ca.crt

# Option 2: Set custom CA bundle (temporary)
export REQUESTS_CA_BUNDLE=/path/to/staging-ca.crt
xc_user_group_sync sync --csv User-Database.csv

# Option 3: Use production environment for testing (if possible)
export XC_API_URL="https://${TENANT_ID}.console.ves.volterra.io"
```

---

#### 8.6.2 Diagnostic Commands

**Check Configuration**:

```bash
# Display loaded configuration (passwords masked)
env | grep -E "TENANT_ID|XC_API_URL|VOLT_API"

# Verify .env file exists and is readable
ls -la secrets/.env

# Test environment variable loading
python3 -c "from dotenv import load_dotenv; load_dotenv('secrets/.env'); import os; print(os.getenv('TENANT_ID'))"
```

**Test API Connectivity**:

```bash
# Test API endpoint reachability
curl -v https://${TENANT_ID}.console.ves.volterra.io/api/web/namespaces/system/user_groups \
  --cert ${VOLT_API_CERT_FILE} \
  --key ${VOLT_API_CERT_KEY_FILE}

# Expected: HTTP 200 with JSON response
# If 401: Authentication failure
# If connection timeout: Network/firewall issue
```

**Validate CSV**:

```bash
# Count rows
wc -l User-Database.csv

# List unique groups
csvcut -c "Entitlement Display Name" User-Database.csv | sort -u | wc -l

# List unique users
csvcut -c "Email" User-Database.csv | sort -u | wc -l

# Check for malformed DNs
csvcut -c "Entitlement Display Name" User-Database.csv | grep -v "^CN="
```

**Check Logs**:

```bash
# Run with debug logging
xc_user_group_sync sync --csv User-Database.csv --log-level debug

# Capture full output
xc_user_group_sync sync --csv User-Database.csv 2>&1 | tee sync-debug.log

# Search for specific errors
grep -i error sync-debug.log
grep -i "failed" sync-debug.log
```

---

## 9. Appendices

### 8.1 Appendix A: API Contract Specification

The F5 Distributed Cloud IAM API contract is defined in OpenAPI 3.0 format. The complete contract is maintained in a separate file for version control and reusability.

**Contract Location**: `api/contracts/xc-iam.yaml`

**Key Endpoints Summary**:

1. **GET /api/web/namespaces/{namespace}/user_groups**
   - Purpose: List all user groups in namespace
   - Response: Array of user group objects

2. **POST /api/web/namespaces/{namespace}/user_groups**
   - Purpose: Create new user group
   - Request Body: UserGroup object (name, users required)
   - Response: HTTP 201 Created

3. **PUT /api/web/namespaces/{namespace}/user_groups/{name}**
   - Purpose: Update existing user group (full replacement)
   - Request Body: UserGroup object with updated users array
   - Response: HTTP 200 OK

4. **DELETE /api/web/namespaces/{namespace}/user_groups/{name}**
   - Purpose: Delete user group
   - Response: HTTP 204 No Content

5. **POST /api/web/namespaces/{namespace}/users**
   - Purpose: Create new user
   - Request Body: User object (email required)
   - Response: HTTP 201 Created

6. **DELETE /api/web/namespaces/{namespace}/users/{email}**
   - Purpose: Delete user
   - Response: HTTP 204 No Content

**Authentication**: TLS client certificate or API token in Authorization header

**Content Type**: application/json

**Rate Limiting**: Subject to F5 XC platform limits; tool implements retry with exponential backoff

---

### 8.2 Appendix B: CSV Format Examples

#### Example 1: Minimal Valid CSV

```csv
Email,Entitlement Display Name
alice@example.com,"CN=Admins,OU=Groups,DC=example,DC=com"
bob@example.com,"CN=Developers,OU=Groups,DC=example,DC=com"
```

**Result**: Two groups created (Admins, Developers), each with one user.

---

#### Example 2: Multiple Users per Group

```csv
Email,Entitlement Display Name
alice@example.com,"CN=Admins,OU=Groups,DC=example,DC=com"
bob@example.com,"CN=Admins,OU=Groups,DC=example,DC=com"
carol@example.com,"CN=Admins,OU=Groups,DC=example,DC=com"
```

**Result**: One group (Admins) with three users.

---

#### Example 3: User in Multiple Groups

```csv
Email,Entitlement Display Name
alice@example.com,"CN=Admins,OU=Groups,DC=example,DC=com"
alice@example.com,"CN=Developers,OU=Groups,DC=example,DC=com"
alice@example.com,"CN=QA,OU=Groups,DC=example,DC=com"
```

**Result**: Three groups (Admins, Developers, QA), all containing alice@example.com.

---

#### Example 4: Full Active Directory Export Format

```csv
"User Name","Login ID","User Display Name","Cof Account Type","Application Name","Entitlement Attribute","Entitlement Display Name","Related Application","Sox","Job Level","Job Title","Created Date","Account Locker","Employee Status","Email","Cost Center","Finc Level 4","Manager EID","Manager Name","Manager Email"
"USER001","CN=USER001,OU=Developers,OU=All Users,DC=example,DC=com","Alice Anderson","User","Active Directory","memberOf","CN=Admins,OU=Groups,DC=example,DC=com","Example App","true","50","Lead Software Engineer","2025-09-23 00:00:00","0","A","alice.anderson@example.com","IT Infrastructure","Network Engineering","MGR001","David Wilson","David.Wilson@example.com"
"USER002","CN=USER002,OU=Developers,OU=All Users,DC=example,DC=com","Bob Smith","User","Active Directory","memberOf","CN=Developers,OU=Groups,DC=example,DC=com","Example App","true","40","Software Engineer","2025-09-24 00:00:00","0","A","bob.smith@example.com","IT Infrastructure","Application Development","MGR001","David Wilson","David.Wilson@example.com"
```

**Result**: Two groups (Admins, Developers), one user each. Additional columns ignored.

---

### 8.3 Appendix C: Glossary

**Active Directory (AD)**: Microsoft's directory service providing authentication, authorization, and centralized management for Windows domain networks.

**API Token**: Authentication credential in string format used in HTTP Authorization header for API access.

**Circuit Breaker**: Design pattern that detects failures and prevents cascading failures by temporarily disabling operations.

**Common Name (CN)**: Component of LDAP Distinguished Name typically representing entity's name (user, group, etc.).

**CSV (Comma-Separated Values)**: Plain text file format for tabular data with comma field delimiters.

**Distinguished Name (DN)**: Unique identifier in LDAP directory consisting of sequence of Relative Distinguished Names.

**Dry-Run**: Simulation mode that displays planned operations without executing them.

**Environment Variable**: Dynamic value affecting process behavior, stored outside code in shell or .env files.

**Exponential Backoff**: Retry strategy with exponentially increasing wait times between attempts.

**F5 Distributed Cloud (F5 XC)**: F5's cloud-native application delivery and security platform.

**Idempotent Operation**: Operation producing same result regardless of execution repetition.

**LDAP (Lightweight Directory Access Protocol)**: Protocol for accessing and maintaining distributed directory services.

**Namespace**: Logical isolation boundary in F5 XC for organizing resources; tool operates in`system`namespace.

**Orphaned Resource**: Resource present in F5 XC but absent from CSV, eligible for deletion with --prune flag.

**P12 (PKCS#12)**: File format for storing cryptographic objects (certificate and private key) protected by password.

**PEM (Privacy-Enhanced Mail)**: Base64-encoded file format for certificates and keys with header/footer markers.

**Prune**: Operation to delete resources not present in CSV, requires explicit --prune flag.

**Rate Limiting**: API restriction on number of requests per time period to prevent overload.

**Retry**: Automatic re-attempt of failed operation, typically with backoff delay.

**TLS (Transport Layer Security)**: Cryptographic protocol providing secure communication over networks.

**Transient Failure**: Temporary error condition that may succeed on retry (network timeout, server overload).

---

### 8.4 Appendix D: Change History

This appendix documents major changes to the specification since initial creation.

#### Version 1.0.0 - Initial Production Specification (2025-11-13)

**Type**: Consolidation and Standardization

**Description**: Consolidated all fragmented enhancement specifications and planning documents into single IEEE 29148:2018 compliant production specification.

**Changes**:
1. **Consolidated Documents**:
   -`enhancements-cli-feedback.md`→ Section 3.4 (FR-UX requirements)
   -`enhancements-config-environment.md`→ Section 3.2 (FR-ENV requirements)
   -`enhancements-retry-backoff.md`→ Section 3.3 (FR-RETRY requirements)
   -`enhancements-setup-script.md`→ Section 3.5 (FR-SETUP requirements)
   -`data-model.md`→ Section 6.1 (Data Model)
   -`CSV_MAPPING.md`→ Sections 6.2, 6.3 (CSV Format and Transformations)

2. **New Sections Added**:
   - Section 1: Introduction (Purpose, Scope, Definitions, References)
   - Section 2: Overall Description (Product Perspective, Functions, Users, Environment, Constraints)
   - Section 4: External Interface Requirements (UI, Hardware, Software, Communications)
   - Section 5: Non-Functional Requirements (Performance, Safety, Security, Quality)
   - Section 7: Quality Attributes (Testability, Traceability, Maintainability)
   - Section 8: Appendices (API Contract, Examples, Glossary, Change History)

3. **Requirements Organization**:
   - 32+ functional requirements organized into 6 feature areas
   - Each requirement includes: ID, statement, rationale, acceptance criteria, testing guidance
   - Traceability established between requirements, implementation, and tests

4. **IEEE 29148:2018 Compliance**:
   - Document structure follows IEEE standard sections
   - Requirements use modal verbs (MUST, SHALL, SHOULD, MAY)
   - Acceptance criteria defined for all functional requirements
   - Non-functional requirements separated by quality attribute
   - Verification methods specified for each requirement category

**Rationale**: Previous specification fragmented across 10+ files (enhancements, plan, tasks, research, quickstart, data-model, CSV mapping). Production teams require single authoritative document. IEEE 29148:2018 compliance ensures professional quality and industry best practice adherence.

**Impact**:
- **Positive**: Single source of truth for production teams, improved clarity, professional standard compliance
- **Removed**: Implementation artifacts (plan.md, tasks.md, research.md, quickstart.md, checklists/) - completed milestones no longer needed
- **Maintained**: API contract (contracts/xc-iam.yaml) as separate reusable artifact

**Migration Path**:
1. Production teams use`specification.md`as primary reference
2. Legacy enhancement documents archived/deleted (already implemented in codebase)
3. Implementation details verified against codebase for accuracy

**Verification**:
- All 32+ requirements traced to implementation
- All acceptance criteria verified against test suite
- API contract validated against F5 XC documentation
- Document reviewed for completeness and clarity

---

**End of Software Requirements Specification**

**Document Version**: 1.0.0
**Total Requirements**: 38 functional requirements (FR-*) + 19 non-functional requirements (NFR-*)
**Page Count**: Comprehensive (~150 pages equivalent)
**Compliance**: ISO/IEC/IEEE 29148:2018
**Status**: Production-Ready
