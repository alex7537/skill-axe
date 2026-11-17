---
name: parabolic-yt-dlp-diagnose
description: Diagnose Windows Nickvision Parabolic and yt-dlp download failures across the frontend, extractor, HTTP/DNS/TLS/proxy path, cookies and login state, JavaScript runtime, FFmpeg merge, and output filesystem. Use when users mention Parabolic, yt-dlp, cookies.txt, HTTP 4xx/5xx, sign-in or bot challenges, missing formats, stalled downloads, or behavior that differs between Parabolic and a CLI/Python project. Read-only by default; do not use to bypass DRM, access controls, or media authorization.
---

# Parabolic and yt-dlp Diagnosis

Find the first failing layer and support it with evidence. Do not treat reinstalling, updating, replacing cookies, or changing the proxy as diagnosis.

## Safety and authorization

- Confirm that the user is authorized to access and download the media. Stop at DRM, paywall, account-access, geo-access-control, or other circumvention requests.
- Treat cookie files, browser profiles, URLs with signed query parameters, request headers, and verbose logs as secrets. Never print cookie values or copy a cookie file into chat, a report, a repository, or the skill.
- If cookie values have already appeared in a shared file or transcript, report exposure without repeating them and recommend revoking the affected sessions or rotating the cookies.
- Remain read-only unless the user explicitly asks for a particular repair. Do not delete caches, rewrite configuration, import browser cookies, log in, update executables, alter proxy settings, or change file associations during diagnosis.
- Respect rate limits. Do not loop retries after `429`, bot checks, CAPTCHA, or a temporary block.

## Known local context

Treat these as historical hints and verify that they still exist before relying on them:

- A project such as `youtube2bilibili` uses the Python `yt_dlp` API for authorized YouTube downloads.
- That project can reuse `ffmpeg.exe` and `deno.exe` under `C:\Program Files\Nickvision Parabolic\Release` when they are not on `PATH`.
- For a user-supplied Netscape-format cookie export, inspect only its metadata with the bundled diagnostic; never display its contents.

Do not assume the project copy, Parabolic, and a global `yt-dlp` command use the same yt-dlp version, configuration, executable, JavaScript runtime, proxy, cookies, or output directory.

## Evidence funnel

1. Capture the exact failing URL host, visible error, time, operation, expected output, and whether the failure occurs in Parabolic, the project, or both. Redact signed URL parameters and account data.
2. Run the bundled read-only inventory from this skill directory:

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/diagnose_parabolic.ps1
   ```

   Add `-ProjectPath`, `-CookieFile`, or `-Url` only for the target under investigation. `-CookieFile` reports format and expiry statistics without emitting cookie names or values. `-Url` performs DNS and TCP reachability checks for the URL host; it does not download media.
3. Build a layer map before suggesting a fix:

   ```text
   Parabolic UI/config
     -> yt-dlp executable or Python package
     -> site extractor and JavaScript/EJS runtime
     -> DNS/TCP/TLS/proxy/HTTP response
     -> authentication and cookie validity
     -> media fragment transfer
     -> FFmpeg merge/post-processing
     -> output path, permissions, and free space
   ```

4. Compare the smallest equivalent operation in the failing environments. Record the resolved executable/package versions and effective output location. Do not paste an unsanitized `--verbose` log; it can expose headers, cookies, proxy credentials, and signed URLs.
5. Read [references/failure-matrix.md](references/failure-matrix.md) for the matching symptom. Test one hypothesis at a time and repeat only the failed stage.
6. Lead the report with one classification: `frontend/config`, `yt-dlp/extractor`, `JavaScript runtime`, `network/HTTP`, `authentication/cookies`, `media transfer`, `FFmpeg/post-processing`, `filesystem`, or `unresolved`.

## Version and environment rules

- Identify every relevant yt-dlp instance: Parabolic-bundled, global command, and project Python environment. A successful CLI test with a different version does not clear Parabolic.
- Prefer a non-downloading extractor probe when it is sufficient. Keep any full download bounded to one authorized test item and a user-approved output directory.
- Distinguish HTTP status from cause. For example, `403` can mean stale cookies, missing challenge support, a signed media URL expiring, proxy reputation, or site-side blocking.
- Distinguish discovery from merge. Downloaded video/audio fragments plus a missing final file usually points to FFmpeg or output handling, not the extractor.
- Treat a Netscape cookie header as format evidence only. It does not prove that cookies are current, complete, valid for the requested domain, or accepted from the current network path.
- Compare timestamps and versions before reinstalling. Reinstallation is a repair attempt, not evidence of root cause.

## Repair gate

After identifying the failing layer, propose the smallest reversible repair and its verification. Obtain explicit user direction before any action that changes Parabolic configuration, replaces or exports cookies, installs or updates yt-dlp/Deno/FFmpeg, changes proxy/DNS settings, deletes cache, or writes outside a user-approved test directory.

Report what changed, which exact check now passes, and what remains unverified. Never claim success from process exit alone; require the expected metadata, media file, merged output, or other stage-specific artifact.
