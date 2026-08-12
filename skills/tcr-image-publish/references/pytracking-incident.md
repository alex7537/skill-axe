# PyTracking large-image incident

Use this case as a diagnostic precedent, not as a universal hard-coded target.

## Source and target

- Source archive: `pytracking.tar`
- Archive size: `18,531,639,296` bytes
- Archive SHA256: `cc99eb181713d28c7ae1652fed1b0efc2dd7df77427c409b05eb81d0154001d4`
- Loaded source image: `pytracking/cuda-squashed:11.6.2`
- Destination: `docker-registry.psibot.net/personal/zhangyurui:cuda11.6.2-py37-torch1.12.1`
- Platform: `linux/amd64`
- Published manifest digest: `sha256:e63c1b14a50013e803f7e2923765c9ced328fe5e1b8457af60d0e2818665f0c2`

## What failed

The image was flattened into one roughly 18.5 GB layer. Direct upload from Docker Desktop on a Mac remained at `Waiting`, later produced `broken pipe`, and on another attempt transferred almost the entire layer without committing a manifest. Registry Bearer tokens observed during diagnosis had about a 30-minute lifetime, while the public-network upload needed hours. The first service-account token also had only `pull` action even though the account name implied read/write.

## What succeeded

1. Resume-upload the archive to an `ap-shanghai` TI-ONE development machine.
2. Compare local and remote SHA256.
3. Run `docker load` on the relay.
4. Authenticate there with the service account through a hidden prompt.
5. Tag and push from the relay to TCR.
6. Independently query the resulting manifest.

The relay-to-TCR push completed in about 11 minutes. The result was trusted only after the registry returned the expected tag and manifest digest.

## Lessons

- Prefer a same-region relay for large layers.
- Preserve resumability during the Mac-to-relay transfer.
- Check effective scope, not account naming.
- Treat manifest commit and readback as the completion criterion.
- Rotate any credential ever pasted into a chat or command line.
