# Documentation Structure

This directory contains comprehensive documentation for the F5 XC User and Group Sync tool, organized by audience and use case.

## Documentation Organization

### 📚 User Documentation

**For first-time users and operators**

| Document | Purpose | Audience |
|----------|---------|----------|
| **[index.md](index.md)** | Documentation home with persona-based navigation | All users |
| **[get-started.md](get-started.md)** | Installation and quick start guide | New users |
| **[configuration.md](configuration.md)** | Environment setup and CSV format | All users |
| **[cli-reference.md](cli-reference.md)** | Complete CLI command reference | Users, operators |
| **[operations-guide.md](operations-guide.md)** | Production operations and workflows | DevOps engineers, operators |
| **[troubleshooting.md](troubleshooting.md)** | Common issues and solutions | All users |

### 🔧 CI/CD Documentation

**For automation and deployment**

Located in `CICD/` directory:

| Document | Purpose |
|----------|---------|
| **[deployment-guide.md](CICD/deployment-guide.md)** | Overview of deployment scenarios |
| **[github-actions-guide.md](CICD/github-actions-guide.md)** | GitHub Actions automation |
| **[jenkins-guide.md](CICD/jenkins-guide.md)** | Jenkins pipeline integration |
| **[examples/](CICD/examples/)** | Reusable workflow and pipeline files |

### 💻 Developer Documentation

**For contributors and developers**

| Document | Purpose | Audience |
|----------|---------|----------|
| **[development.md](development.md)** | Development overview and setup | Contributors |
| **[contributing.md](contributing.md)** | Contribution workflow and guidelines | New contributors |
| **[quality-standards.md](quality-standards.md)** | Code quality requirements | Developers |
| **[testing.md](testing.md)** | Testing practices and requirements | Developers, QA |

### 📋 Specifications

**For technical specifications and requirements**

Located in `specifications/` directory:

| Document | Purpose |
|----------|---------|
| **[user-group-sync-srs.md](specifications/user-group-sync-srs.md)** | System requirements specification |
| **[user-lifecycle-management-srs.md](specifications/user-lifecycle-management-srs.md)** | User lifecycle specification |
| **[implementation/testing-strategy.md](specifications/implementation/testing-strategy.md)** | Comprehensive testing strategy |

## Quick Navigation

### By Role

**👤 First-Time User**

→ Start at [index.md](index.md) → [Getting Started](get-started.md)

**🔧 DevOps Engineer**

→ Start at [index.md](index.md) → [Operations Guide](operations-guide.md)

**💻 Contributor**

→ Start at [index.md](index.md) → [Contributing](contributing.md)

### By Task

| Task | Document | Section |
|------|----------|---------|
| Install | [get-started.md](get-started.md) | Installation |
| Configure | [configuration.md](configuration.md) | Environment Variables |
| Run sync | [get-started.md](get-started.md) | Quick Start |
| Automate | [CICD/deployment-guide.md](CICD/deployment-guide.md) | Scenarios |
| Troubleshoot | [troubleshooting.md](troubleshooting.md) | Common Issues |
| Contribute | [contributing.md](contributing.md) | Workflow |
| Write tests | [testing.md](testing.md) | Writing Tests |

## Documentation Principles

### DRY (Don't Repeat Yourself)

- Each concept documented once in canonical location
- Other documents reference via links
- Examples extracted to reusable files

### Progressive Disclosure

- Start simple (getting started)
- Progress to advanced (operations, deployment)
- Deep dive available (specifications)

### Persona-Based

- Clear audience identification
- Role-specific navigation paths
- Goal-oriented structure

### Maintainability

- Single source of truth per topic
- Clear cross-references
- Consistent formatting

## Contributing to Documentation

When updating documentation:

1. **Follow structure** - Place content in appropriate document
2. **Update cross-references** - Check all links remain valid
3. **Maintain DRY** - Reference existing content, don't duplicate
4. **Test examples** - Verify all code examples work
5. **Check formatting** - Run markdown linter (PyMarkdown)

See [Contributing Guide](contributing.md) for detailed process.

## Documentation Standards

### Markdown Formatting

- Headers: Use `#` notation
- Code blocks: Specify language (`` ```bash ``, `` ```python ``)
- Links: Use descriptive text, not "click here"
- Lists: Use `-` for unordered, `1.` for ordered

### File Naming

- Use kebab-case: `file-name.md`
- Be descriptive: `github-actions-guide.md`, not `guide.md`
- Match content purpose

### Document Structure

- Include metadata block at top (audience, date)
- Start with ## Overview section
- Use consistent heading hierarchy
- End with ## Related Documentation

## Getting Help

- **Questions**: Open GitHub issue with `documentation` label
- **Improvements**: Submit PR with documentation changes
- **Errors**: Report via GitHub issues
