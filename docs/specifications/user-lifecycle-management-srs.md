# Software Requirements Specification

## User Lifecycle Management for F5 Distributed Cloud Synchronization Tool

**Document Version**: 1.0
**Date**: 2025-11-13
**Feature ID**: 059-user-lifecycle
**Status**: Production Ready
**IEEE Standard**: IEEE 29148:2018 Compliant

---

## Document Control

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2025-11-13 | Expert Panel Review | Initial production-ready specification |

**Distribution List**:

- Implementation Team Lead
- Quality Assurance Team
- DevOps/Operations Team
- Product Management
- Security Team

**Document Classification**: Internal - Production Implementation

---

## Table of Contents

1. [Introduction](#1-introduction)
   - 1.1 [Purpose and Scope](#11-purpose-and-scope)
   - 1.2 [Document Conventions](#12-document-conventions)
   - 1.3 [Intended Audience](#13-intended-audience)
   - 1.4 [Definitions, Acronyms, and Abbreviations](#14-definitions-acronyms-and-abbreviations)
   - 1.5 [References](#15-references)
   - 1.6 [Executive Summary](#16-executive-summary)

2. [Overall Description](#2-overall-description)
   - 2.1 [Product Perspective](#21-product-perspective)
   - 2.2 [Product Functions](#22-product-functions)
   - 2.3 [User Classes and Characteristics](#23-user-classes-and-characteristics)
   - 2.4 [Operating Environment](#24-operating-environment)
   - 2.5 [Design and Implementation Constraints](#25-design-and-implementation-constraints)
   - 2.6 [Assumptions and Dependencies](#26-assumptions-and-dependencies)

3. [System Features](#3-system-features)
   - 3.1 [User Creation from CSV](#31-user-creation-from-csv)
   - 3.2 [User Attribute Updates](#32-user-attribute-updates)
   - 3.3 [User Deletion](#33-user-deletion)
   - 3.4 [CSV Parsing and Validation](#34-csv-parsing-and-validation)
   - 3.5 [Dry-Run Preview Mode](#35-dry-run-preview-mode)
   - 3.6 [Synchronization Reporting](#36-synchronization-reporting)

4. [External Interface Requirements](#4-external-interface-requirements)
   - 4.1 [Command Line Interface](#41-command-line-interface)
   - 4.2 [F5 XC API Interface](#42-f5-xc-api-interface)
   - 4.3 [CSV File Format](#43-csv-file-format)
   - 4.4 [Logging Interface](#44-logging-interface)

5. [Non-Functional Requirements](#5-non-functional-requirements)
   - 5.1 [Performance Requirements](#51-performance-requirements)
   - 5.2 [Security Requirements](#52-security-requirements)
   - 5.3 [Reliability Requirements](#53-reliability-requirements)
   - 5.4 [Operational Requirements](#54-operational-requirements)
   - 5.5 [Maintainability Requirements](#55-maintainability-requirements)

6. [Data Model](#6-data-model)
   - 6.1 [Data Entities](#61-data-entities)
   - 6.2 [Data Relationships](#62-data-relationships)
   - 6.3 [Data Validation Rules](#63-data-validation-rules)
   - 6.4 [State Transitions](#64-state-transitions)
   - 6.5 [Data Flow](#65-data-flow)

7. [Quality Attributes](#7-quality-attributes)
   - 7.1 [Testability Requirements](#71-testability-requirements)
   - 7.2 [Requirements Traceability Matrix](#72-requirements-traceability-matrix)
   - 7.3 [Coverage Criteria](#73-coverage-criteria)
   - 7.4 [Success Metrics](#74-success-metrics)

8. [Failure Modes and Recovery](#8-failure-modes-and-recovery)
   - 8.1 [Failure Mode and Effects Analysis](#81-failure-mode-and-effects-analysis)
   - 8.2 [Error Handling Specifications](#82-error-handling-specifications)
   - 8.3 [Recovery Procedures](#83-recovery-procedures)
   - 8.4 [Rollback Mechanisms](#84-rollback-mechanisms)

9. [Testing Requirements](#9-testing-requirements)
   - 9.1 [Testing Strategy](#91-testing-strategy)
   - 9.2 [Test Environment Setup](#92-test-environment-setup)
   - 9.3 [Test Data Management](#93-test-data-management)
   - 9.4 [Acceptance Test Scenarios](#94-acceptance-test-scenarios)
   - 9.5 [Test Coverage Requirements](#95-test-coverage-requirements)

10. [Operational Requirements](#10-operational-requirements)
    - 10.1 [Deployment Specifications](#101-deployment-specifications)
    - 10.2 [Configuration Management](#102-configuration-management)
    - 10.3 [Monitoring and Alerting](#103-monitoring-and-alerting)
    - 10.4 [Logging Specifications](#104-logging-specifications)
    - 10.5 [Backup and Disaster Recovery](#105-backup-and-disaster-recovery)

11. [Appendices](#11-appendices)
    - A. [API Payload Examples](#appendix-a-api-payload-examples)
    - B. [CSV Format Examples](#appendix-b-csv-format-examples)
    - C. [Glossary](#appendix-c-glossary)
    - D. [Change History](#appendix-d-change-history)

---

## 1. Introduction

## 1.1 Purpose and Scope

### 1.1.1 Purpose

This Software Requirements Specification (SRS) document provides a comprehensive and complete specification for implementing user lifecycle management capabilities in the F5 Distributed Cloud (F5 XC) User and Group Synchronization Tool. This document is intended for production implementation teams and contains all necessary technical details, interface specifications, quality requirements, and operational procedures required for successful development, testing, deployment, and maintenance of this feature.

### 1.1.2 Scope

**In Scope:**

- User lifecycle management (create, update, delete) synchronized from Active Directory CSV exports
- Enhanced CSV parsing for user attributes (display name, active status)
- State-based reconciliation treating CSV as authoritative source of truth
- Configurable deletion flags with safety mechanisms
- Dry-run preview mode for change validation
- Detailed synchronization summary reporting
- Idempotent operations supporting repeated execution without side effects

**Out of Scope:**

- Active Directory integration or CSV generation (CSV must be provided by external process)
- Role assignments and permissions management (managed separately in F5 XC)
- User authentication or password management (handled by F5 XC SSO/SAML)
- Multi-tenancy or cross-namespace operations (operates in "system" namespace only)
- Backup or rollback of user changes (no automated recovery mechanism)
- Configuration file support (environment variables and CLI flags only)

### 1.1.3 Benefits

This enhancement provides the following business and technical benefits:

1. **Operational Efficiency**: Automates manual user management tasks, reducing administrative overhead
2. **Data Accuracy**: Ensures F5 XC user data matches Active Directory source of truth
3. **Security Compliance**: Enables timely user deactivation and removal aligned with termination processes
4. **Audit Trail**: Provides detailed logging of all user lifecycle operations
5. **Risk Mitigation**: Dry-run mode and explicit deletion flags prevent accidental data loss

## 1.2 Document Conventions

### 1.2.1 Requirement Priority Levels

Requirements are prioritized using the following classification:

- **P1 (Critical)**: Core functionality required for feature to work. Must be implemented.
- **P2 (Important)**: Significant functionality enhancing usability and safety. Should be implemented.
- **P3 (Nice-to-Have)**: Supportive functionality improving operational visibility. May be deferred.

### 1.2.2 Requirement Keywords

This specification uses RFC 2119 keywords to indicate requirement levels:

- **SHALL**: Mandatory requirement that must be implemented
- **SHOULD**: Recommended requirement with strong preference for implementation
- **MAY**: Optional requirement that can be implemented if resources permit

### 1.2.3 Naming Conventions

- **Functional Requirements**: Prefixed with FR-XXX (e.g., FR-001)
- **Non-Functional Requirements**: Prefixed with NFR-XXX (e.g., NFR-001)
- **Success Criteria**: Prefixed with SC-XXX (e.g., SC-001)
- **User Stories**: Prefixed with US-X (e.g., US-1)
- **Test Cases**: Prefixed with TC-XXX (e.g., TC-001)

### 1.2.4 Typographical Conventions

- `Code`, `commands`, and `file_names` appear in monospace font
- **Bold text** indicates key concepts or emphasis
- *Italic text* indicates referenced documents or variable names
- "Quoted text" indicates literal string values
- [Links] provide cross-references to related sections

## 1.3 Intended Audience

This document is intended for the following stakeholders:

### 1.3.1 Primary Audience (Must Read)

**Implementation Team**: Software engineers responsible for coding, unit testing, and integration of this feature. This audience should read all sections with particular attention to:

- Section 3: System Features (detailed functional requirements)
- Section 4: External Interface Requirements (API contracts)
- Section 6: Data Model (entity definitions)
- Section 9: Testing Requirements (test strategy)

**Quality Assurance Team**: Test engineers responsible for validation and verification. This audience should focus on:

- Section 3: System Features (acceptance criteria)
- Section 7: Quality Attributes (traceability matrix)
- Section 9: Testing Requirements (complete test strategy)
- Section 8: Failure Modes (negative test scenarios)

### 1.3.2 Secondary Audience (Selective Reading)

**DevOps/Operations Team**: Engineers responsible for deployment and operational monitoring. Focus areas:

- Section 5: Non-Functional Requirements (operational requirements)
- Section 10: Operational Requirements (deployment, monitoring)
- Section 8: Failure Modes (recovery procedures)

**Product Management**: Product owners and managers. Focus areas:

- Section 1.6: Executive Summary (business value)
- Section 3: System Features (feature descriptions)
- Section 7.4: Success Metrics (measurable outcomes)

**Security Team**: Security engineers responsible for security review and compliance. Focus areas:

- Section 5.2: Security Requirements (authentication, authorization, audit)
- Section 8: Failure Modes (security failure scenarios)

## 1.4 Definitions, Acronyms, and Abbreviations

### 1.4.1 Key Terms

**Active Directory (AD)**: Microsoft directory service providing centralized user and group management for Windows-based networks. Source system for CSV exports consumed by this tool.

**CSV (Comma-Separated Values)**: Text file format using commas to separate values, representing tabular data exported from Active Directory.

**Dry-Run Mode**: Execution mode where all synchronization logic runs but no API calls are made to F5 XC, allowing safe preview of planned operations.

**F5 Distributed Cloud (F5 XC)**: Target cloud platform where users and groups are synchronized.

**Idempotent Operation**: Operation that produces the same result regardless of how many times it is executed with the same input data.

**LDAP DN (Distinguished Name)**: Unique identifier for an entry in LDAP directory, formatted as comma-separated attribute-value pairs (e.g., "CN=User,OU=Department,DC=example,DC=com").

**Reconciliation**: Process of comparing desired state (CSV) with current state (F5 XC) and executing only necessary operations to achieve desired state.

**Source of Truth**: Authoritative data source that defines correct state. In this system, the CSV file is the source of truth for user data.

**State-Based Synchronization**: Synchronization approach where complete desired state is declared (CSV) and system calculates necessary changes to reach that state.

**User Lifecycle**: Complete set of operations affecting a user over time: creation, updates to attributes, and eventual deletion.

### 1.4.2 Acronyms

| Acronym | Full Form |
|---------|-----------|
| AD | Active Directory |
| API | Application Programming Interface |
| CLI | Command Line Interface |
| CN | Common Name (LDAP attribute) |
| CSV | Comma-Separated Values |
| DC | Domain Component (LDAP attribute) |
| DN | Distinguished Name (LDAP) |
| F5 XC | F5 Distributed Cloud |
| FMEA | Failure Mode and Effects Analysis |
| FR | Functional Requirement |
| HTTP | Hypertext Transfer Protocol |
| HTTPS | HTTP Secure |
| JSON | JavaScript Object Notation |
| LDAP | Lightweight Directory Access Protocol |
| NFR | Non-Functional Requirement |
| OU | Organizational Unit (LDAP attribute) |
| REST | Representational State Transfer |
| SC | Success Criteria |
| SCIM | System for Cross-domain Identity Management |
| SRS | Software Requirements Specification |
| SSL/TLS | Secure Sockets Layer / Transport Layer Security |
| US | User Story |
| UTC | Coordinated Universal Time |

### 1.4.3 Technical Terms

**Circuit Breaker**: Design pattern preventing cascading failures by temporarily blocking requests to failing external services.

**Email (as identifier)**: Unique string identifying a user in format `local-part@domain`, used as primary key in this system.

**Entity**: Data object with distinct identity and attributes (e.g., User, Group).

**Exponential Backoff**: Retry strategy where wait time between retries increases exponentially (1s, 2s, 4s, etc.).

**Protocol (Python)**: Structural subtyping mechanism defining interfaces for dependency injection without inheritance.

**Retry Logic**: Automatic re-attempt of failed operations with configurable conditions and limits.

**Tenant**: Isolated environment within F5 XC for a specific organization or business unit.

**User_Roles API**: F5 XC custom API endpoint for user management operations at `/api/web/custom/namespaces/system/user_roles`.

## 1.5 References

### 1.5.1 Standards and Specifications

| Reference | Title | Source |
|-----------|-------|--------|
| IEEE 29148:2018 | Systems and software engineering — Life cycle processes — Requirements engineering | IEEE Standards Association |
| RFC 2119 | Key words for use in RFCs to Indicate Requirement Levels | IETF |
| RFC 4180 | Common Format and MIME Type for CSV Files | IETF |
| ISO/IEC 25010:2011 | Systems and software quality models | ISO/IEC |

### 1.5.2 Related Documentation

| Document | Location | Description |
|----------|----------|-------------|
| System Requirements Specification | `user-group-sync-srs.md` | Complete system specification for F5 XC synchronization tool |
| API Contract | `api/contracts/xc-iam.yaml` | F5 Distributed Cloud IAM API OpenAPI specification |
| Project README | `README.md` | Project overview and setup instructions |
| Implementation Reference | `src/xc_user_group_sync/sync_service.py` | Current implementation patterns to follow |

### 1.5.3 External Resources

| Resource | URL | Purpose |
|----------|-----|---------|
| F5 XC API Documentation | F5 internal docs | API endpoint specifications |
| Python Pydantic Documentation | https://docs.pydantic.dev/ | Data validation framework |
| Tenacity Documentation | https://tenacity.readthedocs.io/ | Retry library documentation |
| Click Documentation | https://click.palletsprojects.com/ | CLI framework documentation |

## 1.6 Executive Summary

### 1.6.1 Problem Statement

Organizations using F5 Distributed Cloud currently lack automated user lifecycle management synchronized with their Active Directory infrastructure. This creates several operational challenges:

1. **Manual User Management**: Administrators must manually create, update, and delete users in F5 XC, leading to errors and inconsistencies
2. **Data Drift**: F5 XC user data becomes outdated as changes occur in Active Directory without corresponding updates
3. **Security Gaps**: Terminated employees may retain F5 XC access due to delayed manual deactivation
4. **Audit Compliance**: Lack of automated synchronization makes it difficult to maintain audit trails and demonstrate access governance
5. **Operational Overhead**: Manual user management tasks consume significant IT resources that could be applied to higher-value activities

### 1.6.2 Solution Overview

This feature enhances the existing F5 XC User and Group Synchronization Tool with comprehensive user lifecycle management capabilities. The solution:

**Automates User Synchronization**: Reads user data from Active Directory CSV exports and automatically creates, updates, or deletes users in F5 XC to match the CSV state.

**Ensures Data Accuracy**: Treats CSV as authoritative source of truth, reconciling F5 XC state to match exactly through idempotent operations.

**Provides Safety Mechanisms**: Includes dry-run preview mode and explicit deletion flags to prevent accidental data loss.

**Enables Audit Compliance**: Generates detailed logs and summary reports of all synchronization operations for audit trail purposes.

**Maintains Existing Functionality**: Preserves all existing group synchronization capabilities without disruption.

### 1.6.3 Key Features

| Feature | Priority | Description | Benefit |
|---------|----------|-------------|---------|
| User Creation | P1 | Automatically create new F5 XC users from CSV entries | Eliminates manual user provisioning |
| User Updates | P1 | Update existing user attributes when CSV data changes | Keeps user data synchronized with AD |
| User Deletion | P2 | Optionally delete F5 XC users not present in CSV | Removes terminated employees from system |
| CSV Parsing | P1 | Parse display names and employee status codes | Correctly interprets AD export format |
| Dry-Run Mode | P2 | Preview changes without executing API calls | Prevents accidental destructive changes |
| Summary Reports | P3 | Detailed statistics and error reporting | Provides operational visibility and troubleshooting |

### 1.6.4 Success Criteria Summary

This feature will be considered successful when:

1. **Performance**: 1,000 users can be synchronized in under 5 minutes
2. **Reliability**: 100% idempotent operation (re-running produces no unnecessary changes)
3. **Accuracy**: 100% correctness in parsing display names and active status codes
4. **Safety**: Zero users deleted without explicit `--prune` flag
5. **Observability**: Synchronization summary reports are 99%+ accurate compared to actual changes

### 1.6.5 Implementation Approach

**Architecture**: Extends existing protocol-based dependency injection architecture following established GroupSyncService patterns.

**Data Flow**: CSV → Parse → Reconcile → F5 XC API

- Enhanced CSV parser extracts user attributes and group memberships
- State reconciliation compares CSV (desired) with F5 XC (current)
- Only necessary operations (create/update/delete) are executed
- Comprehensive statistics and error tracking throughout

**Technology Stack**:

- Python 3.9+ (targeting Python 3.12)
- Pydantic for data validation
- Tenacity for retry logic with exponential backoff
- Click for CLI framework
- Requests for HTTP API communication

**Quality Standards**:

- 80%+ automated test coverage
- Test-Driven Development (TDD) approach
- Google-style docstrings with type hints
- Black formatting, Ruff linting, mypy type checking

### 1.6.6 Timeline and Effort Estimate

**Implementation Phases**:

1. **Phase 1**: Data models and utility functions (2-3 days)
2. **Phase 2**: API client extensions (2-3 days)
3. **Phase 3**: UserSyncService implementation (3-4 days)
4. **Phase 4**: CLI integration (1-2 days)
5. **Phase 5**: Integration testing and documentation (2-3 days)

**Total Estimated Effort**: 10-15 development days (2-3 weeks calendar time)

**Critical Path Dependencies**:

- F5 XC API access and credentials for testing
- Sample Active Directory CSV exports for validation
- Code review and security review approvals

---

## 2. Overall Description

## 2.1 Product Perspective

### 2.1.1 System Context

The User Lifecycle Management feature is an enhancement to the existing F5 XC User and Group Synchronization Tool. This tool serves as a bridge between an organization's Active Directory infrastructure and F5 Distributed Cloud platform, ensuring identity data remains synchronized.

**Current System Capabilities** (Preserved):

- Group synchronization from CSV to F5 XC
- LDAP Distinguished Name parsing for group extraction
- F5 XC API client with retry logic
- CLI framework with dry-run support
- P12 certificate authentication

**New Capabilities** (Added by this feature):

- User lifecycle management (create, update, delete)
- Enhanced CSV parsing for user-specific attributes
- Display name parsing into first/last name components
- Employee status code mapping to active boolean
- State-based reconciliation for users
- Optional user deletion with safety flags
- Comprehensive user synchronization reporting

### 2.1.2 System Architecture

```text
┌─────────────────────┐
│  Active Directory   │
│  (External System)  │
└──────────┬──────────┘
           │ CSV Export
           │ (Manual/Scheduled)
           ▼
┌─────────────────────────────────────────────────────────────┐
│          F5 XC User and Group Synchronization Tool          │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    CLI Layer                         │   │
│  │  (click framework - existing + user flags)           │   │
│  └───────────────────┬─────────────────────────────────┘   │
│                      │                                       │
│  ┌───────────────────┴─────────────────────────────────┐   │
│  │              Service Layer                           │   │
│  │  ┌──────────────────┐  ┌────────────────────────┐  │   │
│  │  │ GroupSyncService │  │ UserSyncService (NEW)  │  │   │
│  │  │   (existing)     │  │  - parse_csv_to_users  │  │   │
│  │  │                  │  │  - fetch_existing_users│  │   │
│  │  │                  │  │  - sync_users          │  │   │
│  │  └──────────────────┘  └────────────────────────┘  │   │
│  └───────────────────┬─────────────────────────────────┘   │
│                      │                                       │
│  ┌───────────────────┴─────────────────────────────────┐   │
│  │              API Client Layer                        │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │         XCClient (extended)                   │  │   │
│  │  │  - list_users / list_user_roles (existing)   │  │   │
│  │  │  - create_user (existing)                     │  │   │
│  │  │  - update_user (NEW)                          │  │   │
│  │  │  - delete_user (NEW)                          │  │   │
│  │  │  - get_user (NEW)                             │  │   │
│  │  │  + Retry logic with exponential backoff       │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └───────────────────┬─────────────────────────────────┘   │
│                      │ HTTPS/REST                           │
└──────────────────────┼──────────────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
     ┌─────▼─────┐         ┌───────▼──────┐
     │ F5 XC API │         │  F5 XC API   │
     │  Groups   │         │    Users     │
     │ (existing)│         │user_roles API│
     └───────────┘         │    (NEW)     │
                           └──────────────┘

```

### 2.1.3 Component Relationships

| Component | Type | Responsibility | Dependencies |
|-----------|------|----------------|--------------|
| CLI | Interface | Command-line interface, flag parsing, output formatting | Click, UserSyncService, GroupSyncService |
| UserSyncService | Business Logic | CSV parsing, state reconciliation, orchestration | UserRepository protocol, user_utils |
| GroupSyncService | Business Logic | Group synchronization (existing, unchanged) | GroupRepository protocol |
| XCClient | API Client | HTTP communication, retry logic, authentication | requests, tenacity |
| user_utils | Utilities | Name parsing, status mapping | None (pure functions) |
| ldap_utils | Utilities | LDAP DN parsing, CN extraction (existing) | ldap3 |
| models | Data | Pydantic models for validation | Pydantic |
| protocols | Interfaces | Protocol definitions for dependency injection | typing.Protocol |

## 2.2 Product Functions

### 2.2.1 Primary Functions

1. **User Creation** (P1)
   - Read user data from CSV Active Directory export
   - Parse display names into first/last name components
   - Map employee status codes to active boolean
   - Create new users in F5 XC via user_roles API
   - Log creation operations with results

2. **User Updates** (P1)
   - Fetch current user data from F5 XC
   - Compare CSV user attributes with existing F5 XC data
   - Update only users with attribute changes (idempotent)
   - Log update operations with changed attributes

3. **User Deletion** (P2)
   - Identify F5 XC users not present in CSV
   - Delete orphaned users when `--prune` flag provided
   - Default to NOT deleting users (safe behavior)
   - Log deletion operations with user identifiers

4. **CSV Parsing and Validation** (P1)
   - Validate presence of required CSV columns
   - Parse display names handling various formats (single name, multiple words)
   - Map employee status codes ("A" = active, others = inactive)
   - Extract group memberships from pipe-separated LDAP DNs
   - Skip invalid rows with warnings, continue processing

5. **Dry-Run Preview** (P2)
   - Execute full synchronization logic without API calls
   - Log all planned operations (create, update, delete)
   - Generate summary statistics without modifying F5 XC
   - Provide safe validation before actual execution

6. **Synchronization Reporting** (P3)
   - Track statistics: created, updated, deleted, unchanged, errors
   - Collect error details with user identifiers and error messages
   - Generate summary report with counts and execution time
   - Provide detailed error logs for troubleshooting

### 2.2.2 Function Hierarchy

```text
User Lifecycle Management
├── User Synchronization (Core)
│   ├── Create Users
│   ├── Update Users
│   └── Delete Users (Optional)
├── CSV Processing
│   ├── Validate CSV Structure
│   ├── Parse User Attributes
│   └── Handle Parse Errors
├── State Reconciliation
│   ├── Fetch Current State
│   ├── Calculate Differences
│   └── Execute Operations
├── Safety Mechanisms
│   ├── Dry-Run Mode
│   └── Explicit Deletion Flag
└── Observability
    ├── Operation Logging
    └── Summary Reporting

```

## 2.3 User Classes and Characteristics

### 2.3.1 Primary Users

**System Administrators** (Primary)

- **Role**: Responsible for user lifecycle management in F5 XC
- **Technical Expertise**: Intermediate to advanced command-line skills
- **Usage Frequency**: Daily to weekly synchronization runs
- **Key Tasks**:
  - Run synchronization with Active Directory exports
  - Troubleshoot synchronization errors
  - Manage user deletions during terminations
  - Review synchronization summaries for audit purposes
- **Success Factors**:
  - Clear error messages for troubleshooting
  - Safe defaults preventing accidental deletions
  - Dry-run mode for change validation
  - Comprehensive summary reports

### 2.3.2 Secondary Users

**Identity and Access Management (IAM) Engineers**

- **Role**: Design and maintain identity synchronization workflows
- **Technical Expertise**: Advanced scripting and automation skills
- **Usage Frequency**: Occasional (setup, troubleshooting, optimization)
- **Key Tasks**:
  - Integrate tool into automated synchronization pipelines
  - Configure scheduling and error alerting
  - Optimize synchronization performance
  - Validate compliance with security policies
- **Success Factors**:
  - Predictable behavior for automation
  - Detailed logging for monitoring integration
  - Performance suitable for automated scheduling
  - Clear documentation for integration patterns

**Security and Compliance Auditors**

- **Role**: Review access management practices and audit trails
- **Technical Expertise**: Basic command-line skills
- **Usage Frequency**: Quarterly or during audits
- **Key Tasks**:
  - Review synchronization logs for compliance
  - Validate timely user deactivation/deletion
  - Verify audit trail completeness
  - Ensure proper access governance
- **Success Factors**:
  - Comprehensive audit logs with timestamps
  - Clear summary reports showing all operations
  - Traceability from CSV source to F5 XC changes

## 2.4 Operating Environment

### 2.4.1 Software Environment

**Runtime Environment**:

- **Operating Systems**: Linux, macOS, Windows
- **Python Version**: Python 3.9 minimum, Python 3.12 recommended
- **Package Management**: pip or pipx for installation
- **Execution Context**: Command-line terminal or shell

**Dependencies**:

| Package | Version | Purpose |
|---------|---------|---------|
| click | 8.1.7+ | CLI framework |
| pydantic | 2.9.2+ | Data validation |
| requests | 2.32.3+ | HTTP client |
| tenacity | 9.0.0+ | Retry logic |
| ldap3 | 2.9.1+ | LDAP DN parsing |
| python-dotenv | 1.0.1+ | Environment configuration |

**Optional Dependencies** (Development):

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | 8.3.0+ | Testing framework |
| pytest-cov | 6.0.0+ | Code coverage |
| ruff | Latest | Linting |
| black | Latest | Code formatting |
| mypy | Latest | Type checking |

### 2.4.2 Hardware Environment

**Minimal Requirements**:

- **CPU**: Single core (1 GHz or faster)
- **Memory**: 256 MB RAM available for Python process
- **Disk**: 100 MB for installation and temporary files
- **Network**: Internet connectivity to F5 XC API endpoints

**Recommended Requirements** (for optimal performance):

- **CPU**: Dual core (2 GHz or faster)
- **Memory**: 512 MB RAM available
- **Disk**: 500 MB for installation, logs, and temporary files
- **Network**: Stable high-speed internet connection (>5 Mbps)

### 2.4.3 Network Environment

**Connectivity Requirements**:

- **Outbound HTTPS** (port 443) to F5 XC tenant API endpoints
- **DNS Resolution** for F5 XC domain names
- **No Inbound Ports Required**: Tool operates as client only

**Proxy Support**:

- Honors system proxy settings (HTTP_PROXY, HTTPS_PROXY environment variables)
- No additional proxy configuration required in tool

**Firewall Considerations**:

- Outbound HTTPS to `*.volterra.io` or `*.f5.com` domains must be permitted
- P12 authentication requires mutual TLS support

### 2.4.4 External System Dependencies

**F5 Distributed Cloud Platform**:

- **Version**: Any currently supported F5 XC version
- **API Endpoint**: `/api/web/custom/namespaces/system/user_roles`
- **Authentication**: P12 certificate
- **Rate Limits**: Must accommodate tool's request rate (configured with circuit breaker)

**Active Directory** (Indirect Dependency):

- **CSV Export Format**: Must match expected column structure
- **Character Encoding**: UTF-8 required
- **File Size**: Up to 10,000 user records supported (configurable)

## 2.5 Design and Implementation Constraints

### 2.5.1 Technical Constraints

**Programming Language**:

- **Constraint**: Must be implemented in Python 3.9+
- **Rationale**: Existing codebase is Python-based; maintains consistency
- **Impact**: Limits use of newer Python 3.12+ features in initial implementation

**API Limitations**:

- **Constraint**: F5 XC user_roles API does not support batch operations
- **Rationale**: API design limitation
- **Impact**: Each user requires individual create/update/delete API call, affecting performance

**Stateless Operation**:

- **Constraint**: No local state persistence between synchronization runs
- **Rationale**: Design decision for simplicity and reliability
- **Impact**: Cannot track historical changes or incremental synchronization

**No Transactions**:

- **Constraint**: F5 XC API does not support multi-operation transactions
- **Rationale**: API design limitation
- **Impact**: Cannot implement all-or-nothing synchronization; partial failures possible

### 2.5.2 Architectural Constraints

**Protocol-Based Dependency Injection**:

- **Constraint**: Must follow existing protocol-based architecture pattern
- **Rationale**: Consistency with established codebase patterns
- **Impact**: Requires UserRepository protocol matching GroupRepository pattern

**CLI Framework**:

- **Constraint**: Must use Click framework for CLI implementation
- **Rationale**: Existing tool uses Click; maintains consistency
- **Impact**: CLI design must conform to Click paradigms

**Single Namespace Operation**:

- **Constraint**: Operates in "system" namespace only
- **Rationale**: Simplifies implementation; matches existing group sync behavior
- **Impact**: Cannot manage users across multiple F5 XC namespaces

### 2.5.3 Operational Constraints

**Authentication Method**:

- **Constraint**: Must support P12 certificate authentication
- **Rationale**: Different deployment environments use different authentication methods
- **Impact**: Must handle both authentication approaches with same client code

**CSV Format Fixed**:

- **Constraint**: CSV column names and structure are fixed (must match Active Directory export format)
- **Rationale**: Integration with external system beyond our control
- **Impact**: Cannot modify CSV format; must handle variations through parsing logic

**No GUI**:

- **Constraint**: Command-line interface only, no graphical user interface
- **Rationale**: Target users are system administrators comfortable with CLI
- **Impact**: All interaction through terminal commands and flags

### 2.5.4 Regulatory and Compliance Constraints

**Data Privacy**:

- **Constraint**: User data (names, emails) must be handled according to organizational data privacy policies
- **Rationale**: Compliance with GDPR, CCPA, or other applicable regulations
- **Impact**: Must log user data appropriately; may require log sanitization in certain deployments

**Audit Requirements**:

- **Constraint**: All user lifecycle operations must be logged with sufficient detail for audit purposes
- **Rationale**: Compliance and security governance requirements
- **Impact**: Comprehensive logging required; cannot skip logging for performance

**Access Control**:

- **Constraint**: User executing tool must have appropriate F5 XC permissions for user management
- **Rationale**: Principle of least privilege
- **Impact**: Tool cannot bypass F5 XC authorization; failures expected if insufficient permissions

## 2.6 Assumptions and Dependencies

### 2.6.1 Assumptions

**CSV File Quality**:

- CSV files are UTF-8 encoded with proper header row
- Column names exactly match specification (case-sensitive)
- CSV is comma-delimited with double-quote text qualifiers
- Email addresses are valid and unique within the file
- Display names follow Western naming conventions (space-separated words)

**Environment Setup**:

- F5 XC API credentials are configured correctly before tool execution
- Network connectivity to F5 XC API is available during synchronization
- Python 3.9+ is installed and accessible in PATH
- Required Python dependencies are installed

**User Permissions**:

- User executing tool has administrative permissions in F5 XC
- API credentials provided have user management permissions
- No additional authorization or approval workflows required

**CSV Represents Complete State**:

- CSV is a complete snapshot of desired user state, not incremental changes
- All users that should exist in F5 XC are present in CSV
- Absent users can be safely deleted when `--prune` flag is used

**Active Directory Integration**:

- CSV export from Active Directory is performed by external process
- Export process maintains consistent format across runs
- Export timing aligns with synchronization schedule

### 2.6.2 Dependencies

**External Systems**:

1. **F5 Distributed Cloud Platform**
   - Availability: Must be accessible during synchronization
   - Stability: API must be operational and responsive
   - Version: Must support user_roles API endpoint
   - Impact if unavailable: Synchronization cannot proceed

2. **Active Directory** (Indirect)
   - Dependency: CSV export process must run successfully
   - Format: CSV must conform to expected structure
   - Impact if unavailable: Synchronization has no input data

**Internal Components**:

1. **Existing XCClient Implementation**
   - Dependency: Must have working authentication and retry logic
   - Impact: User sync builds upon existing API client patterns

2. **Existing LDAP Utilities**
   - Dependency: CN extraction from LDAP DNs must work correctly
   - Impact: Group membership parsing relies on these utilities

**Network Infrastructure**:

1. **DNS Resolution**
   - Dependency: F5 XC domain names must resolve correctly
   - Impact if unavailable: Cannot reach API endpoints

2. **TLS/SSL Infrastructure**
   - Dependency: Valid TLS certificates and trust chain
   - Impact if unavailable: HTTPS connections fail

3. **Proxy Infrastructure** (if applicable)
   - Dependency: Proxy must forward HTTPS traffic correctly
   - Impact if misconfigured: API calls fail or timeout

### 2.6.3 Dependency Risk Mitigation

| Dependency | Risk | Mitigation Strategy |
|------------|------|---------------------|
| F5 XC API Availability | Service outage prevents synchronization | Retry logic with exponential backoff, circuit breaker pattern |
| CSV Format Changes | Active Directory export format changes break parsing | CSV validation before processing, clear error messages for missing columns |
| Network Connectivity | Network issues cause API failures | Retry transient errors, timeout configuration, graceful degradation |
| Authentication Expiry | Credentials expire during sync | Token refresh logic, clear expiry error messages |
| API Rate Limits | Too many requests trigger rate limiting | Exponential backoff on 429 responses, configurable request pacing |

---

*[Continuing with Section 3: System Features...]*

## 3. System Features

## 3.1 User Creation from CSV

**Priority**: P1 (Critical)
**User Story**: US-1
**Requirement IDs**: FR-001, FR-002, FR-003, FR-004, FR-012, FR-016

### 3.1.1 Feature Description

When new users appear in the Active Directory CSV export, the system automatically creates those users in F5 Distributed Cloud with complete profile information including name (parsed into first/last components), email, active status, and group memberships.

This feature is foundational to user lifecycle management - without user creation capability, no synchronization can occur. Users are created with all necessary attributes to enable immediate access provisioning and group membership assignment.

### 3.1.2 Functional Requirements

**FR-001**: System SHALL parse CSV files containing columns: "Email", "Entitlement Display Name", "User Display Name", "Employee Status"

**FR-002**: System SHALL extract first name and last name from "User Display Name" column using the following algorithm:

- Trim leading and trailing whitespace
- Split display name on space characters
- Last space-separated word becomes last_name
- All remaining words (joined with spaces) become first_name
- If only one word exists, it becomes first_name with empty last_name

**FR-003**: System SHALL map "Employee Status" column value to active boolean:

- Value "A" (case-insensitive, whitespace-trimmed) maps to active=true
- All other values map to active=false

**FR-004**: System SHALL create users in F5 XC that exist in CSV but not in F5 XC, setting these attributes:

- email (from CSV "Email" column, lowercased)
- username (set to email value)
- display_name (from CSV "User Display Name")
- first_name (parsed from display_name per FR-002)
- last_name (parsed from display_name per FR-002)
- active (mapped from "Employee Status" per FR-003)

**FR-012**: System SHALL be idempotent - if user already exists in F5 XC, SHALL NOT create duplicate

**FR-016**: System SHALL trim whitespace from display names before parsing to handle formatting inconsistencies

### 3.1.3 Input Specifications

**CSV File**:

- Format: UTF-8 encoded, comma-delimited, double-quote text qualified
- Required Columns (case-sensitive, exact match):
  - "Email": User's email address
  - "User Display Name": Full name as shown in Active Directory
  - "Employee Status": Status code indicating active/inactive
  - "Entitlement Display Name": Pipe-separated LDAP DNs for groups (may be empty)

**Example CSV Row**:

```csv
Email,User Display Name,Employee Status,Entitlement Display Name
alice.anderson@example.com,Alice Anderson,A,CN=EADMIN_STD,OU=Groups,DC=example,DC=com|CN=DEVELOPERS,OU=Groups,DC=example,DC=com

```

### 3.1.4 Processing Logic

```text

1. Validate CSV structure (all required columns present)
2. FOR EACH row in CSV:

   a. Extract email, trim, lowercase
   b. Extract display_name, trim
   c. Parse display_name → (first_name, last_name) per FR-002
   d. Map employee_status → active per FR-003
   e. Parse groups from Entitlement Display Name (pipe-separated LDAP DNs)
   f. Create User object with validation
   g. IF validation fails:

      - Log warning with row details
      - SKIP row, CONTINUE with next
3. FOR EACH validated User:

   a. Check if user.email exists in F5 XC
   b. IF NOT exists:

      - Create user via F5 XC API
      - Log success or error
      - Update statistics (created or error count)

   c. IF exists:

      - SKIP creation (handled by update logic)
4. Return synchronization statistics

```

### 3.1.5 Output Specifications

**API Call** (F5 XC user_roles POST):

```json

POST /api/web/custom/namespaces/system/user_roles
Content-Type: application/json

{
  "email": "alice.anderson@example.com",
  "username": "alice.anderson@example.com",
  "display_name": "Alice Anderson",
  "first_name": "Alice",
  "last_name": "Anderson",
  "active": true
}

```

**Success Response** (201 Created):

```json

{
  "user_role": {
    "email": "alice.anderson@example.com",
    "username": "alice.anderson@example.com",
    "display_name": "Alice Anderson",
    "first_name": "Alice",
    "last_name": "Anderson",
    "active": true,
    "created_at": "2025-11-13T10:30:00Z"
  }
}

```

**Log Output**:

```text

INFO: Created user: alice.anderson@example.com (Alice Anderson, active=True)

```

### 3.1.6 Acceptance Criteria

**AC-1.1**: Given CSV contains user "Alice Anderson" with email "alice@example.com" and Employee Status "A", When synchronization runs, Then user is created in F5 XC with first_name="Alice", last_name="Anderson", email="alice@example.com", active=true

**AC-1.2**: Given CSV contains user "John Paul Smith" with Employee Status "I" (inactive), When synchronization runs, Then user is created with first_name="John Paul", last_name="Smith", active=false

**AC-1.3**: Given CSV contains user with single name "Madonna", When synchronization runs, Then user is created with first_name="Madonna", last_name="" (empty string)

**AC-1.4**: Given user already exists in F5 XC with same email, When synchronization runs again with same CSV, Then no duplicate user is created (operation is idempotent)

**AC-1.5**: Given CSV has display name with leading/trailing whitespace "  Alice  Anderson  ", When parsed, Then creates user with first_name="Alice", last_name="Anderson" (whitespace trimmed)

### 3.1.7 Edge Cases and Error Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| Display name empty or missing | Log warning, skip row, continue with remaining users |
| Email invalid format | Pydantic validation fails, log warning, skip row |
| Employee Status missing | Default to active=false (inactive), log warning, continue |
| API returns 409 Conflict (user exists) | Log info message, treat as unchanged (idempotent) |
| API returns 400 Bad Request | Log error with details, increment error count, continue with remaining users |
| CSV has duplicate emails | First occurrence processed, subsequent duplicates skipped with warning |

### 3.1.8 Performance Requirements

- SHALL parse 10,000 CSV rows in under 5 seconds (from FR-001, FR-002, FR-003)
- SHALL create 1,000 new users in under 5 minutes including API calls (from SC-001)
- SHALL handle individual user creation failures without aborting entire synchronization (from FR-019)

### 3.1.9 Security Considerations

- Email addresses SHALL be handled as case-insensitive identifiers (lowercase before comparison)
- User data SHALL be logged only when necessary for troubleshooting (minimize PII in logs)
- API authentication SHALL be validated before attempting any user creation operations

---

## 3.2 User Attribute Updates

**Priority**: P1 (Critical)
**User Story**: US-2
**Requirement IDs**: FR-005, FR-006, FR-016, FR-017

### 3.2.1 Feature Description

When existing user information changes in Active Directory (name changes due to marriage/legal reasons, status changes due to termination/leave), the system automatically updates that user's profile in F5 Distributed Cloud to match the current CSV data.

This feature is critical for maintaining data accuracy. Users frequently change names and active status changes occur during terminations and leaves of absence. The system must detect these changes and update only the necessary attributes, avoiding unnecessary API calls when data matches.

### 3.2.2 Functional Requirements

**FR-005**: System SHALL update existing F5 XC users when CSV attributes (first_name, last_name, active status) differ from current F5 XC values

**FR-006**: System SHALL compare current user attributes with desired CSV attributes before updating to ensure idempotency (SHALL NOT make unnecessary update API calls when attributes already match)

**FR-016**: System SHALL trim whitespace from display names before parsing to handle formatting inconsistencies

**FR-017**: System SHALL perform case-insensitive email matching when comparing CSV users with F5 XC users

### 3.2.3 Input Specifications

**Current State** (from F5 XC):

```json
{
  "email": "alice.anderson@example.com",
  "username": "alice.anderson@example.com",
  "display_name": "Alice Anderson",
  "first_name": "Alice",
  "last_name": "Anderson",
  "active": true
}

```

**Desired State** (from CSV after name change):

```csv

Email,User Display Name,Employee Status,Entitlement Display Name
alice.anderson@example.com,Alice Smith,A,CN=EADMIN_STD,OU=Groups,DC=example,DC=com

```

### 3.2.4 Processing Logic

```text

1. Fetch all existing users from F5 XC
2. Build map: lowercase_email → current_user_data
3. FOR EACH user in CSV:

   a. Parse user attributes (per User Creation logic)
   b. Lookup user in existing map by lowercase email
   c. IF user exists in F5 XC:
      i. Compare attributes: first_name, last_name, display_name, active
      ii. IF any attribute differs:

          - Build update payload with changed attributes
          - Call F5 XC update API
          - Log update with changed fields
          - Increment update count

      iii. ELSE (all attributes match):

          - SKIP update (idempotent)
          - Increment unchanged count

   d. ELSE (user not in F5 XC):

      - Handle via User Creation logic
4. Return synchronization statistics

```

### 3.2.5 Comparison Algorithm

```python

def user_needs_update(current: Dict, desired: User) -> bool:
    """Determine if user needs update by comparing attributes."""

    # Compare each relevant attribute
    fields_to_compare = [
        ('first_name', desired.first_name),
        ('last_name', desired.last_name),
        ('display_name', desired.display_name),
        ('active', desired.active)
    ]

    for field_name, desired_value in fields_to_compare:
        current_value = current.get(field_name)
        if current_value != desired_value:
            return True  # Attribute differs, update needed

    return False  # All attributes match, no update needed

```

### 3.2.6 Output Specifications

**API Call** (F5 XC user_roles PUT):

```json

PUT /api/web/custom/namespaces/system/user_roles/alice.anderson@example.com
Content-Type: application/json

{
  "email": "alice.anderson@example.com",
  "username": "alice.anderson@example.com",
  "display_name": "Alice Smith",
  "first_name": "Alice",
  "last_name": "Smith",
  "active": true
}

```

**Success Response** (200 OK):

```json

{
  "user_role": {
    "email": "alice.anderson@example.com",
    "username": "alice.anderson@example.com",
    "display_name": "Alice Smith",
    "first_name": "Alice",
    "last_name": "Smith",
    "active": true,
    "updated_at": "2025-11-13T10:35:00Z"
  }
}

```

**Log Output**:

```text

INFO: Updated user: alice.anderson@example.com (last_name changed: Anderson → Smith)

```

### 3.2.7 Acceptance Criteria

**AC-2.1**: Given user "Alice Anderson" exists in F5 XC, When CSV shows her name as "Alice Smith" (married name), Then user's first_name and last_name are updated to "Alice" and "Smith"

**AC-2.2**: Given user with active=true exists, When CSV shows Employee Status changed to "T" (terminated), Then user's active status is set to false

**AC-2.3**: Given user attributes match CSV exactly, When synchronization runs, Then no update API call is made (idempotent - no unnecessary updates)

**AC-2.4**: Given user exists with multiple attribute changes (name and status), When synchronization runs, Then all changed attributes are updated in a single operation

**AC-2.5**: Given user email in F5 XC is "Alice@example.com" and CSV has "alice@example.com", When comparing (case-insensitive), Then user is correctly identified as same person and attributes compared

### 3.2.8 Edge Cases and Error Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| API returns 404 Not Found | Log error, user may have been deleted externally; skip update |
| API returns 400 Bad Request | Log error with validation details, increment error count, continue |
| Display name changed but parsed first/last same | No update needed (idempotent), increment unchanged count |
| Only active status changed | Update only active field (don't touch other attributes) |
| CSV row has user email not in F5 XC | Handle via User Creation logic instead |
| Multiple simultaneous updates to same user | Last write wins (no conflict resolution) |

### 3.2.9 Performance Requirements

- SHALL compare 1,000 existing users in under 10 seconds (in-memory comparison)
- SHALL update 100 changed users in under 60 seconds including API calls
- SHALL minimize API calls by updating only when attributes differ (zero updates when data matches)

---

## 3.3 User Deletion

**Priority**: P2 (Important)
**User Story**: US-3
**Requirement IDs**: FR-007, FR-008, FR-009, FR-019

### 3.3.1 Feature Description

When users are removed from Active Directory (due to termination, transfer, or role changes), the system provides optional deletion of those users from F5 Distributed Cloud to maintain clean user lists and security compliance.

This feature is important for security and compliance but lower priority than create/update because:

1. It's optional (controlled by `--prune` flag)
2. Can be deferred until administrators are ready
3. Requires careful validation to prevent accidental data loss

### 3.3.2 Functional Requirements

**FR-007**: System SHALL support optional user and group deletion via `--prune` CLI flag, deleting F5 XC users and groups that do not exist in CSV

**FR-008**: System SHALL default to NOT deleting users or groups unless `--prune` flag is explicitly provided (safe default behavior)

**Note**: The `--prune` flag applies to **both users and groups simultaneously**. There is no option to prune only users or only groups independently. This unified behavior ensures referential integrity between users and groups during synchronization operations.

**FR-009**: System SHALL support dry-run mode via `--dry-run` CLI flag that logs planned deletions without executing API calls

**FR-019**: System SHALL continue processing remaining users if individual delete operations fail, collecting errors for summary report

### 3.3.3 Input Specifications

**Command Line Flags**:

```bash

# Without --prune flag (default, safe)

xc_user_group_sync --csv users.csv

# With --prune flag (explicit deletion enabled)

xc_user_group_sync --csv users.csv --prune

# With dry-run (preview deletions safely)

xc_user_group_sync --csv users.csv --prune --dry-run

```

**Current State** (F5 XC has user not in CSV):

```json

{
  "charlie@example.com": {
    "email": "charlie@example.com",
    "username": "charlie@example.com",
    "display_name": "Charlie Brown",
    "first_name": "Charlie",
    "last_name": "Brown",
    "active": true
  }
}

```

**Desired State** (CSV does not contain charlie@example.com)

### 3.3.4 Processing Logic

```text

1. Parse CSV to get desired users (set of email addresses)
2. Fetch existing users from F5 XC
3. Calculate orphaned users: existing_emails - desired_emails
4. IF --prune flag NOT provided:
   - Log info: "Skipping user deletions (--prune not specified)"
   - DO NOT delete any users
   - RETURN with zero deletions
5. IF --prune flag provided:

   FOR EACH orphaned user email:
      a. IF --dry-run:

         - Log: "[DRY-RUN] Would delete user: {email}"
         - Increment delete count (for dry-run summary)
         - DO NOT call API

      b. ELSE:

         - Call F5 XC delete API
         - Log success or error
         - Update statistics (deleted or error count)
6. Return synchronization statistics

```

### 3.3.5 Safety Mechanisms

**Default Safety**:

- Users are NEVER deleted unless `--prune` flag is explicitly provided
- Default behavior: create and update only, no deletions
- Prevents accidental mass deletion from incomplete or corrupted CSV files

**Dry-Run Preview**:

- `--dry-run` flag previews deletions without executing
- Allows administrators to validate deletion list before applying
- Recommended workflow: always dry-run before actual deletion

**Logging**:

- All deletion attempts logged with user email and result
- Dry-run mode clearly marked in logs: "[DRY-RUN]"
- Error handling: individual deletion failures don't abort sync

### 3.3.6 Output Specifications

**API Call** (F5 XC user_roles DELETE):

```http
DELETE /api/web/custom/namespaces/system/user_roles/charlie@example.com

```

**Success Response** (204 No Content or 200 OK):

```json

{}

```

**Log Output** (Normal Mode):

```text

INFO: Deleted user: charlie@example.com

```

**Log Output** (Dry-Run Mode):

```text

INFO: [DRY-RUN] Would delete user: charlie@example.com

```

**Log Output** (Flag Not Provided):

```text

INFO: Found 5 users in F5 XC not present in CSV (not deleted - use --prune to remove)

```

### 3.3.7 Acceptance Criteria

**AC-3.1**: Given user "charlie@example.com" exists in F5 XC but not in CSV, When sync runs with `--prune` flag, Then user is deleted from F5 XC

**AC-3.2**: Given user "charlie@example.com" exists in F5 XC but not in CSV, When sync runs WITHOUT `--prune` flag, Then user is NOT deleted (safe default)

**AC-3.3**: Given `--prune` flag is enabled, When `--dry-run` mode is active, Then deletion is logged but not executed

**AC-3.4**: Given user deletion fails due to API error, When sync completes, Then error is logged, error count incremented, and sync continues with other users

**AC-3.5**: Given 100 users to delete, When 5 deletions fail with errors, Then 95 users are successfully deleted and summary shows: deleted=95, errors=5

### 3.3.8 Edge Cases and Error Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| All F5 XC users missing from CSV | Dry-run recommended; without --prune, no deletions; with flag, all deleted |
| User deleted externally during sync | API returns 404, log as success (already deleted), increment delete count |
| API returns 403 Forbidden | Log error (insufficient permissions), increment error count, continue |
| API returns 409 Conflict | Log error (user may have dependencies), increment error count, continue |
| CSV file is empty | No users in desired state; with --prune ALL F5 XC users would be deleted (use dry-run!) |
| User has active sessions | F5 XC handles session termination; tool proceeds with deletion |

### 3.3.9 Performance Requirements

- SHALL delete 100 users in under 60 seconds including API calls
- SHALL handle deletion failures gracefully without aborting sync
- SHALL provide clear progress logging for large deletion batches (>100 users)

### 3.3.10 Security Considerations

**Authorization**:

- User executing tool must have delete permissions in F5 XC
- API returns 403 if insufficient permissions; tool logs error and continues

**Audit Trail**:

- All deletion attempts logged with timestamp and result
- Dry-run deletions logged with "[DRY-RUN]" prefix
- Error details logged for failed deletions

**Data Loss Prevention**:

- No automatic safeguards against bulk deletion (user responsibility)
- Dry-run mode strongly recommended before any deletion operation
- Clear documentation warning about deletion risks

---

## 3.4 CSV Parsing and Validation

**Priority**: P1 (Critical)
**User Story**: US-4
**Requirement IDs**: FR-001, FR-002, FR-003, FR-013, FR-015, FR-016

### 3.4.1 Feature Description

The system parses CSV files exported from Active Directory, extracting and transforming user data into structured format suitable for F5 XC synchronization. This includes validating CSV structure, parsing display names into name components, mapping status codes to boolean values, and extracting group memberships from LDAP Distinguished Names.

This feature is foundational - all other features depend on correct CSV parsing. Without accurate parsing, user data will be incomplete or incorrect in F5 XC.

### 3.4.2 Functional Requirements

**FR-001**: System SHALL parse CSV files containing required columns: "Email", "Entitlement Display Name", "User Display Name", "Employee Status"

**FR-002**: System SHALL extract first name and last name from "User Display Name" column (detailed algorithm in Section 3.1.2)

**FR-003**: System SHALL map "Employee Status" column value to active boolean: "A" (case-insensitive) → true, all others → false

**FR-013**: System SHALL handle CSV parsing errors gracefully, logging which rows failed and why, continuing with remaining valid rows

**FR-015**: System SHALL validate that required CSV columns exist before processing any rows

**FR-016**: System SHALL trim whitespace from display names before parsing to handle formatting inconsistencies

### 3.4.3 CSV File Structure

**Required Format**:

- **Encoding**: UTF-8
- **Delimiter**: Comma (`,`)
- **Text Qualifier**: Double-quote (`"`)
- **Header Row**: First row must contain column names (case-sensitive)
- **Line Endings**: CRLF (`\r\n`) or LF (`\n`) acceptable

**Required Columns** (exact names, case-sensitive):

| Column Name | Required | Data Type | Description |
|-------------|----------|-----------|-------------|
| Email | Yes | String | User's email address (unique identifier) |
| User Display Name | Yes | String | Full name from Active Directory |
| Employee Status | Yes | String | Status code ("A"=active, others=inactive) |
| Entitlement Display Name | Yes | String | Pipe-separated LDAP DNs for groups (may be empty) |

**Optional Columns** (ignored by tool):

- User Name, Login ID, Cof Account Type, Application Name, Job Title, Manager Name, etc.
- Any additional columns beyond required set are ignored without error

### 3.4.4 Validation Rules

**Pre-Processing Validation** (before parsing rows):

```text

1. Check file exists and is readable
2. Detect character encoding (expect UTF-8)
3. Parse header row
4. Validate required columns present (Email, User Display Name, Employee Status, Entitlement Display Name)
5. IF any required column missing:
   - Raise ValueError with list of missing columns
   - DO NOT process any rows

```

**Per-Row Validation** (during parsing):

```text

FOR EACH row:

  1. Validate email format (via Pydantic EmailStr)
  2. Validate display name is non-empty after trimming
  3. IF validation fails:

     - Log warning with row number and error details
     - SKIP row, CONTINUE with next

  4. ELSE:

     - Add validated User object to results

```

### 3.4.5 Parsing Algorithms

**Display Name Parsing** (FR-002):

```python

def parse_display_name(display_name: str) -> tuple[str, str]:
    """
    Parse display name into (first_name, last_name).

    Algorithm:

    1. Trim whitespace
    2. Split on space characters
    3. Last word → last_name
    4. Remaining words (joined) → first_name
    5. If only one word → (word, "")
    6. If empty → ("", "")

    Examples:
    "Alice Anderson" → ("Alice", "Anderson")
    "John Paul Smith" → ("John Paul", "Smith")
    "Madonna" → ("Madonna", "")
    "  Alice  Anderson  " → ("Alice", "Anderson")
    "" → ("", "")
    """
    trimmed = display_name.strip()
    if not trimmed:
        return ("", "")

    parts = trimmed.split()
    if len(parts) == 1:
        return (parts[0], "")

    first_name = " ".join(parts[:-1])
    last_name = parts[-1]
    return (first_name, last_name)

```

**Employee Status Mapping** (FR-003):

```python

def parse_active_status(employee_status: str) -> bool:
    """
    Map employee status code to active boolean.

    Rules:

    - "A" (case-insensitive, whitespace-trimmed) → True
    - All other values → False
    - Empty or missing → False (safe default)

    Examples:
    "A" → True
    "a" → True
    "  A  " → True
    "I" → False
    "T" → False
    "" → False
    None → False
    """
    if not employee_status:
        return False
    return employee_status.strip().upper() == "A"

```

**Group Extraction** (uses existing ldap_utils):

```python

def parse_groups(entitlement_display_name: str) -> List[str]:
    """
    Extract group names from pipe-separated LDAP DNs.

    Algorithm:

    1. Split on pipe character (|)
    2. For each DN:

       a. Trim whitespace
       b. Extract CN using ldap_utils.extract_cn()
       c. If CN found, add to groups list

    3. Return list of group names

    Example:
    "CN=EADMIN_STD,OU=Groups,DC=example,DC=com|CN=DEVELOPERS,OU=Groups,DC=example,DC=com"
    → ["EADMIN_STD", "DEVELOPERS"]

    "" → []
    "CN=GROUP1,OU=Groups,DC=example,DC=com" → ["GROUP1"]
    """
    if not entitlement_display_name:
        return []

    groups = []
    for dn in entitlement_display_name.split("|"):
        dn = dn.strip()
        if dn:
            cn = extract_cn(dn)  # from ldap_utils
            if cn:
                groups.append(cn)
    return groups

```

### 3.4.6 Error Handling

**Missing Required Columns**:

```text

ERROR: Missing required CSV columns: {'User Display Name', 'Employee Status'}
Expected columns: Email, User Display Name, Employee Status, Entitlement Display Name
Found columns: Email, Entitlement Display Name, User Name, Manager Email

```

**Invalid Row Data**:

```text

WARNING: Skipping invalid row 47 for user@example.com: invalid email format
WARNING: Skipping row 89: missing User Display Name (empty field)
WARNING: Skipping row 123 for baduser@.com: EmailStr validation failed

```

**Malformed CSV Structure**:

```text

ERROR: Failed to parse CSV: Unexpected number of fields in row 12
ERROR: Failed to decode CSV: File is not UTF-8 encoded

```

### 3.4.7 Output Specifications

**Parsed User Object** (Pydantic model):

```python

User(
    email="alice.anderson@example.com",
    username="alice.anderson@example.com",
    display_name="Alice Anderson",
    first_name="Alice",
    last_name="Anderson",
    active=True,
    groups=["EADMIN_STD", "DEVELOPERS"]
)

```

**Parsing Statistics**:

```text

INFO: CSV parsing complete
INFO: Total rows: 1,245
INFO: Valid users parsed: 1,238
INFO: Invalid rows skipped: 7
INFO: Users with groups: 1,150
INFO: Users without groups: 88

```

### 3.4.8 Acceptance Criteria

**AC-4.1**: Given CSV contains "User Display Name" column with "Alice Anderson", When CSV is parsed, Then first_name="Alice" and last_name="Anderson"

**AC-4.2**: Given CSV contains "User Display Name" with "John Paul Smith", When CSV is parsed, Then first_name="John Paul" and last_name="Smith"

**AC-4.3**: Given CSV contains "Employee Status" column with "A", When CSV is parsed, Then active=true

**AC-4.4**: Given CSV contains "Employee Status" with any value other than "A" (e.g., "I", "T", "L"), When CSV is parsed, Then active=false

**AC-4.5**: Given CSV missing required columns ("Email", "Entitlement Display Name", "User Display Name", "Employee Status"), When CSV is parsed, Then clear error message identifies missing columns and NO rows are processed

**AC-4.6**: Given CSV row has invalid email format, When row is parsed, Then warning is logged with row number, row is skipped, and processing continues with next row

**AC-4.7**: Given CSV has 1,000 valid rows and 10 invalid rows, When parsed, Then 1,000 User objects returned, 10 warnings logged, and summary shows: valid=1,000, invalid=10

### 3.4.9 Performance Requirements

- SHALL parse 10,000 CSV rows in under 5 seconds
- SHALL handle CSV files up to 50 MB in size
- SHALL use streaming parsing for memory efficiency (not load entire file into memory)

### 3.4.10 Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| CSV file is empty (no rows after header) | Return empty user list, log warning |
| CSV has only header row, no data rows | Return empty user list, log info message |
| Display name has multiple consecutive spaces | Spaces collapsed during split, parsed correctly |
| Display name is all whitespace | After trim, becomes empty string → ("", "") |
| Employee Status is null/empty | Defaults to False (inactive), log warning |
| Entitlement Display Name is empty | groups = [] (empty list), no warning (valid case) |
| CSV has BOM (Byte Order Mark) | UTF-8 BOM handled automatically by Python csv module |
| CSV has extra columns not in spec | Extra columns ignored without error |
| CSV has columns in different order | Order doesn't matter as long as required columns present |
| Email has mixed case (Alice@Example.COM) | Lowercased during parsing for consistent comparison |

---

## 3.5 Dry-Run Preview Mode

**Priority**: P2 (Important)
**User Story**: US-5
**Requirement IDs**: FR-009, FR-010

### 3.5.2 Functional Requirements

**FR-009**: System SHALL support dry-run mode via `--dry-run` CLI flag that logs planned actions without executing API calls

**FR-010**: System SHALL generate detailed logs for each user operation in dry-run mode: create, update, delete, skip (unchanged)

### 3.5.3 Behavior Specifications

**Normal Mode** (without --dry-run):

- Parse CSV
- Fetch existing users from F5 XC API
- Execute create/update/delete API calls
- Log actual operations with results
- Generate summary with real counts

**Dry-Run Mode** (with --dry-run):

- Parse CSV
- Fetch existing users from F5 XC API
- Calculate all planned operations
- Log operations with "[DRY-RUN]" prefix
- DO NOT execute create/update/delete API calls
- Generate summary with planned counts

### 3.5.4 Log Output Format

**Create Operation**:

```text
[DRY-RUN] Would create user: alice@example.com (Alice Anderson, active=True, groups=2)

```

**Update Operation**:

```text

[DRY-RUN] Would update user: bob@example.com (name changed: Bob Smith → Bob Jones)

```

**Delete Operation**:

```text

[DRY-RUN] Would delete user: charlie@example.com (not in CSV)

```

**Unchanged Operation**:

```text

[DRY-RUN] User unchanged: david@example.com (attributes match CSV)

```

### 3.5.5 Summary Report Format

```text

=== DRY-RUN SYNCHRONIZATION SUMMARY ===

CSV Users Analyzed: 1,067
F5 XC Users Found: 1,066

Planned Operations:
  Would create: 45 users
  Would update: 23 users
  Would delete: 2 users (--prune flag provided)
  Unchanged: 999 users

Parsing Errors: 1 row skipped

Execution Time: 3.42 seconds

NOTE: This was a dry-run. No changes were made to F5 XC.
Run without --dry-run to apply these changes.

```

### 3.5.6 Acceptance Criteria

**AC-5.1**: Given CSV contains new user "alice@example.com", When sync runs with `--dry-run`, Then log shows "[DRY-RUN] Would create user: alice@example.com" but user is NOT created in F5 XC

**AC-5.2**: Given user needs attribute update, When dry-run executes, Then log shows "[DRY-RUN] Would update user: bob@example.com (name changed)" but no update API call is made

**AC-5.3**: Given user should be deleted (with `--prune`), When dry-run executes, Then log shows "[DRY-RUN] Would delete user: charlie@example.com" but user remains in F5 XC

**AC-5.4**: Given dry-run completes, When reviewing output, Then summary report shows counts of planned creates/updates/deletes and execution time

**AC-5.5**: Given 1,000 users to process in dry-run, When execution completes, Then dry-run overhead is less than 10% compared to actual sync (fetch operations still occur)

### 3.5.7 Technical Implementation

**API Call Suppression**:

```python
def _create_user(self, user: User, dry_run: bool, stats: UserSyncStats):
    """Create user (or log planned creation in dry-run)."""
    try:
        if dry_run:
            logger.info(f"[DRY-RUN] Would create user: {user.email}")
            # DO NOT call self.repository.create_user()
        else:
            self.repository.create_user(user.dict())
            logger.info(f"Created user: {user.email}")
        stats.created += 1
    except Exception as e:
        logger.error(f"Failed to create user {user.email}: {e}")
        stats.errors += 1

```

**State Fetching** (still occurs in dry-run):

- Fetch existing users from F5 XC (needed for comparison)
- Parse CSV (needed to determine operations)
- Compare attributes (needed to identify changes)
- **DO NOT execute**: create/update/delete API calls

### 3.5.8 Use Cases

**Use Case 1: Validate New CSV Export**

```bash

# Before running sync on new CSV format

xc_user_group_sync --csv new_export.csv --dry-run

# Review output to ensure parsing works correctly

# Verify expected operations are planned

# Run actual sync once validated

```

**Use Case 2: Preview Deletions Before Applying**

```bash

# ALWAYS dry-run before deleting users

xc_user_group_sync --csv active_users.csv --prune --dry-run

# Review deletion list carefully

# Ensure only terminated users are listed

# Apply deletions after verification

xc_user_group_sync --csv active_users.csv --prune

```

**Use Case 3: Troubleshoot Synchronization Issues**

```bash

# Run dry-run to see what would happen

xc_user_group_sync --csv users.csv --dry-run --log-level DEBUG

# Review detailed logs to identify issues

# Fix CSV or configuration

# Re-run dry-run to validate fix

```

---

## 3.6 Synchronization Reporting

**Priority**: P3 (Nice-to-Have)
**User Story**: US-6
**Requirement IDs**: FR-011, FR-018, FR-019

### 3.6.1 Feature Description

After synchronization completes (or during dry-run), the system generates a comprehensive summary report showing statistics about operations performed, execution time, and any errors encountered. This provides operational visibility for administrators to verify success, troubleshoot issues, and maintain audit records.

### 3.6.2 Functional Requirements

**FR-011**: System SHALL generate detailed logs for each user operation: create, update, delete, skip (unchanged)

**FR-018**: System SHALL log execution duration in summary report

**FR-019**: System SHALL continue processing remaining users if individual user operations fail, collecting all errors for summary report

### 3.6.3 Summary Report Structure

**Standard Summary Output**:

```text
=== USER SYNCHRONIZATION SUMMARY ===

CSV Users Processed: 1,067

  - Active: 1,066
  - Inactive: 1

F5 XC Users (before sync): 1,066

Operations Executed:
  Created: 45 users
  Updated: 23 users
  Deleted: 2 users
  Unchanged: 997 users

Errors Encountered: 3

Execution Time: 00:04:36

User synchronization complete.

```

**Error Detail Section** (when errors > 0):

```text

=== ERROR DETAILS ===

1. Failed to create alice@example.com

   Error: 409 Conflict - User already exists
   Timestamp: 2025-11-13T10:30:15Z

2. Failed to update bob@example.com

   Error: 400 Bad Request - Invalid display name format
   Timestamp: 2025-11-13T10:31:22Z

3. Failed to delete charlie@example.com

   Error: 403 Forbidden - Insufficient permissions
   Timestamp: 2025-11-13T10:32:09Z

```

### 3.6.4 Detailed Operation Logs

**Create Operation Log**:

```text

INFO: [2025-11-13 10:30:12] Created user: alice@example.com (Alice Anderson, active=True)

```

**Update Operation Log**:

```text

INFO: [2025-11-13 10:30:15] Updated user: bob@example.com (last_name changed: Smith → Jones)

```

**Delete Operation Log**:

```text

INFO: [2025-11-13 10:30:18] Deleted user: charlie@example.com (not in CSV)

```

**Unchanged Operation Log**:

```text

DEBUG: [2025-11-13 10:30:20] User unchanged: david@example.com (attributes match)

```

**Error Log**:

```text

ERROR: [2025-11-13 10:30:22] Failed to create user eve@example.com: 409 Conflict - User already exists

```

### 3.6.5 Statistics Tracking

**UserSyncStats Data Structure**:

```python

@dataclass
class UserSyncStats:
    """Statistics from user synchronization operation."""
    created: int = 0          # Users created in F5 XC
    updated: int = 0          # Users updated in F5 XC
    deleted: int = 0          # Users deleted from F5 XC
    unchanged: int = 0        # Users that matched (no changes)
    errors: int = 0           # Total error count
    error_details: List[Dict[str, str]] = field(default_factory=list)

    # Error detail format: {"email": str, "operation": str, "error": str}

```

### 3.6.6 Acceptance Criteria

**AC-6.1**: Given sync creates 5 users, updates 3, deletes 2, When sync completes, Then summary shows "Users: Created: 5, Updated: 3, Deleted: 2"

**AC-6.2**: Given sync encounters 2 API errors, When sync completes, Then summary shows "Errors: 2" with details of which users failed and why

**AC-6.3**: Given sync processes large CSV, When sync completes, Then summary shows total execution time in HH:MM:SS format (e.g., "Duration: 00:05:23")

**AC-6.4**: Given sync has no changes (all users match), When sync completes, Then summary shows "Users: Unchanged: 1,245" with zero errors

**AC-6.5**: Given 100 operations with 5 errors, When summary is generated, Then error details include: email address, operation type (create/update/delete), error message, and timestamp for each error

### 3.6.7 Performance Metrics Reported

| Metric | Description | Format |
|--------|-------------|--------|
| Execution Time | Total time from start to finish | HH:MM:SS (00:04:36) |
| Operations Per Second | Total operations / execution time | Users/sec (3.6 users/sec) |
| Error Rate | Errors / total operations | Percentage (2.3% error rate) |
| API Call Count | Total API calls made | Integer (148 API calls) |
| CSV Parsing Time | Time to parse and validate CSV | Seconds (2.4s parsing) |

### 3.6.8 Logging Levels

**INFO Level** (default):

- Summary statistics
- Successful operations (create, update, delete)
- Important state changes

**DEBUG Level** (--log-level DEBUG):

- Unchanged users (attributes match)
- Detailed parsing information
- API request/response details
- State comparison logic

**WARNING Level**:

- Invalid CSV rows skipped
- Unexpected but handled conditions
- Performance degradation notices

**ERROR Level**:

- Failed operations with stack traces
- API errors with response details
- Critical failures preventing sync

### 3.6.9 Output Formats

**Console Output** (human-readable):

- Formatted tables with aligned columns
- Color-coded status indicators (if terminal supports)
- Progress indicators for large batches

**Structured Logging** (machine-readable):

```json
{
  "timestamp": "2025-11-13T10:30:15Z",
  "level": "INFO",
  "component": "user_sync_service",
  "operation": "create_user",
  "user_email": "alice@example.com",
  "result": "success",
  "duration_ms": 342
}

```

---

*[Continuing with Section 4: External Interface Requirements...]*

---

## 4. External Interface Requirements

## 4.1 Command Line Interface

### 4.1.1 CLI Framework

**Technology**: Click (Python CLI framework)
**Entry Point**: `xc_user_group_sync` command

### 4.1.2 Command Structure

```bash
xc_user_group_sync [OPTIONS]

```

### 4.1.3 Command Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--csv` | Path | Yes | None | Path to CSV file containing user and group data |
| `--dry-run` | Flag | No | False | Preview changes without executing API calls |
| `--prune` | Flag | No | False | Delete F5 XC users AND groups not present in CSV |
| `--log-level` | Choice | No | INFO | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `--timeout` | Integer | No | 120 | API request timeout in seconds |
| `--help` | Flag | No | False | Show help message and exit |

**Important Note on `--prune` Flag**:

The `--prune` flag applies to **both users and groups simultaneously**. When enabled, it will delete:

- All users in F5 XC that are not present in the CSV
- All groups in F5 XC that are not present in the CSV

There is no option to prune only users or only groups independently. This unified behavior ensures referential integrity - groups that reference non-existent users would become invalid, so the tool always synchronizes both resource types together.

### 4.1.4 Usage Examples

**Basic Synchronization** (create and update only):

```bash
xc_user_group_sync --csv /path/to/users.csv

```

**Dry-Run Preview**:

```bash

xc_user_group_sync --csv /path/to/users.csv --dry-run

```

**Synchronization with Deletion**:

```bash

xc_user_group_sync --csv /path/to/users.csv --prune

```

**Debug Mode with Custom Timeout**:

```bash

xc_user_group_sync --csv /path/to/users.csv --log-level DEBUG --timeout 180

```

**Combined Flags** (dry-run deletion preview):

```bash

xc_user_group_sync --csv /path/to/users.csv --prune --dry-run

```

### 4.1.5 Exit Codes

| Exit Code | Meaning | Description |
|-----------|---------|-------------|
| 0 | Success | Synchronization completed without errors |
| 1 | Partial Failure | Some operations failed but sync completed |
| 2 | Configuration Error | Invalid CLI arguments or missing configuration |
| 3 | CSV Error | CSV file missing, unreadable, or invalid format |
| 4 | Authentication Error | F5 XC API authentication failed |
| 5 | Network Error | Unable to reach F5 XC API |

### 4.1.6 Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `TENANT_ID` | Yes | F5 XC tenant identifier | `example-corp` |
| `XC_API_URL` | No | F5 XC API base URL (defaults to production) | `https://example-corp.console.ves.volterra.io` |
| `VOLT_API_P12_FILE` | Yes | Path to P12/PKCS12 certificate file | `/path/to/cert.p12` |
| `DOTENV_PATH` | No | Custom path to .env file (overrides default) | `/custom/path/.env` |
| `HTTP_PROXY` | No | HTTP proxy URL | `http://proxy.example.com:8080` |
| `HTTPS_PROXY` | No | HTTPS proxy URL | `https://proxy.example.com:8443` |

**P12 Certificate Authentication**:

The tool supports native P12 authentication. Certificate and private key are extracted at runtime into temporary files and automatically cleaned up on exit. P12 file path and password are required via `VOLT_API_P12_FILE` and `VES_P12_PASSWORD` environment variables.
