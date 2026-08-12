# Large single-layer image incident

Use this generalized case as a diagnostic precedent, not as a hard-coded target.

## Situation

- The archive was roughly 18.5 GB.
- The image had been flattened into one very large layer.
- Direct upload from a desktop over the public network remained at `Waiting`, later produced `broken pipe`, and sometimes transferred bytes without committing a manifest.
- Registry upload tokens expired sooner than the direct upload could finish.
- An initially supplied service account had only `pull` scope.

## Successful procedure

1. Resume-upload `<image-archive>` to a Linux relay in the registry's region.
2. Compare local and remote SHA256 values without recording the real digest in the reusable skill.
3. Run `docker load` on the relay.
4. Authenticate through a hidden prompt and confirm effective `push` scope.
5. Tag and push `<local-image>` to `<registry>/<namespace>/<image>:<tag>`.
6. Query the resulting manifest and confirm the expected tag exists.

The same-region push completed in minutes rather than hours. Completion was accepted only after manifest readback.

## Lessons

- Prefer a same-region relay for very large layers.
- Preserve resumability during the desktop-to-relay transfer.
- Check effective scope, not account naming.
- Treat manifest commit and readback as the completion criterion.
- Rotate any credential ever pasted into chat or a command line.
