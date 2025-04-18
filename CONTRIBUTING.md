Contributing Guidelines

Thank you for your interest in contributing to this project. To ensure consistency, security, and historical accuracy, please review the following guidelines before submitting any changes.

1. Branch Management

Contributors must target the appropriate branch that corresponds to the Toontown client year they are working with (e.g. 2001, 2003, 2004, 2005, etc).

Do not submit changes intended for one client version to another branch. This ensures fidelity to the original behavior and supports ongoing historical preservation.

If a change spans multiple client versions, submit separate pull requests to each relevant branch.


2. Secure Coding Standards

We prioritize security and stability across all components. All contributions must adhere to modern secure coding practices, including but not limited to:

Input Validation: Sanitize all input from users, clients, and external systems.
Example: Use whitelist-based validation for zone IDs or avatar names.

if not str(zone_id).isdigit():
    raise ValueError("Invalid zone ID.")

Avoid Hardcoded Secrets: Do not commit API keys, credentials, or session tokens. Use configuration files or environment variables instead.

Memory Safety: When working in lower-level modules or with performance-critical code, ensure proper bounds-checking and avoid buffer overflows.

Authentication & Authorization: Ensure that administrative and AI-level commands are not accessible by unauthorized clients.

Logging: Avoid logging sensitive information. Use structured logging and redact where appropriate.
Bad:

logger.info(f"User password: {password}")

Good:

logger.info("Password field received (value redacted)")

Exception Handling: Use structured exception handling and avoid exposing internal stack traces or server logic to clients.


3. Code Style & Quality

Write descriptive commit messages and include references to issues or documentation where applicable.

Pull requests must pass automated tests and be peer-reviewed before merge approval.


4. Licensing & Attribution

All contributions are subject to the repository's license.


---

If you have any questions about secure implementation, proper branching, or compatibility with specific client versions, please open an issue or contact a maintainer.
