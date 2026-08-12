# Restore on a new computer

1. Configure SSH access to GitHub and clone the repository:

   ```bash
   git clone git@github.com:alex7537/skill-axe.git ~/.codex/skill-repos/skill-axe
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

4. Start a new Codex session so global `AGENTS.md` guidance and installed skill metadata are reloaded.

5. Recreate machine-local credentials separately. The repository intentionally excludes runtime credential files such as `tione/config.json`, Codex auth/session state, SSH private keys, Docker auth, and tokens.
