# Restore on a new computer

1. Configure SSH access to GitHub and clone the repository:

   ```bash
   git clone <private-skill-repository> ~/.codex/skill-repos/skill-axe
   ```

2. Review the repository contents and copy only the managed skill folders:

   ```bash
   mkdir -p ~/.codex/skills
   rsync -a ~/.codex/skill-repos/skill-axe/skills/ ~/.codex/skills/
   ```

3. Restore the persistent completion reminder:

   ```bash
   python3 ~/.codex/skills/capture-session-to-skill/scripts/install_global_reminder.py
   python3 ~/.codex/skills/capture-session-to-skill/scripts/install_global_reminder.py --execute
   ```

   The managed block also records each personal skill at most once per session. Local usage counters bootstrap from the repository manifest and continue in `~/.codex/skill-usage.json`.

4. Start a new Codex session so global `AGENTS.md` guidance and installed skill metadata are reloaded.

5. Recreate machine-local configuration and credentials separately. The repository intentionally excludes every runtime `config.json`, Codex auth/session state, SSH private keys, Docker auth, tokens, private-only references, and the machine-local privacy blocklist. Use each `config.example.json` as the portable schema.
