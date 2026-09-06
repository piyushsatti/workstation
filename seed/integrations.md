# Workstation integrations

| Component | What this machine has | What remains personal |
|---|---|---|
| Claude, Codex, OpenCode | Pinned command-line applications; Claude appearance seed; new OpenCode configuration denies actions except file inspection | Sign in locally. Existing configurations and credentials are preserved. No marketplace skills are imported |
| Continue | VS Code extension and Linux schema association | Existing model configuration is preserved. A fresh machine needs its own endpoint and credentials. Mercury currently uses localhost:4000; this installer does not host or assume that gateway |
| RAG | Workspace location and this pointer | LanceDB was selected for the separate RAG MCP server. Install that project for the appropriate personal or office workspace; do not copy indexes between them |
| Memory | Small workspace principles and directory structure seeds | No cross-project memory store is selected or copied by this installer |
| Foundry | See foundry.md | Marketplace content remains explicitly selected, not automatically imported |
| Network access | OpenSSH tools including ssh-copy-id | SSH identities, private keys and Tailscale membership stay machine-specific |

Projects belong in ~/Studio/Developer/projects/NAME/NAME. Sibling worktrees,
artifacts, notes, research and data belong under the outer NAME directory.
Keep personal and office project data, credentials, memories and retrieval indexes separate.
