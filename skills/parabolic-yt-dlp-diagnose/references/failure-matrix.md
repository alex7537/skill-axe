# Parabolic and yt-dlp Failure Matrix

Use the row matching the earliest observed failure. Commands are examples; choose the executable or Python environment actually used by the failing frontend.

| Symptom | Likely layer | Read-only checks | Repair direction after approval |
|---|---|---|---|
| `Unsupported URL`, no suitable extractor | yt-dlp/extractor | Confirm the real URL after redirects; compare yt-dlp versions; run a simulation without cookies first | Update only the failing yt-dlp instance if the current extractor is known to be obsolete |
| `HTTP Error 404/410` | HTTP/site state | Open only the public page; distinguish removed content from an expired media URL | Refresh metadata; do not retry a removed/private resource |
| `HTTP Error 403` | HTTP/auth/challenge | Compare public-page access, yt-dlp versions, cookie expiry metadata, JS runtime, proxy path, and whether the signed fragment URL expired | Refresh authorized session, runtime, or extractor only after identifying which evidence differs |
| `HTTP Error 429`, CAPTCHA, bot check | Rate limit/site defense | Stop retries; note IP/proxy path, request frequency, and whether the browser is also challenged | Wait or use the site's supported access path; do not automate CAPTCHA or evasion |
| `Sign in to confirm`, private/age-restricted item | Authentication | Confirm account authorization; inspect cookie file format/domains/expiry without values; compare requested host with cookie domains | Export a fresh authorized cookie file locally or use supported browser-cookie integration, without sharing it |
| Cookie file rejected | Authentication/cookie format | Check Netscape header, tab-separated seven fields, domain coverage, expiry, encoding, file permissions, and whether the browser session was revoked | Re-export locally; never hand-edit secret values in chat |
| `No video formats found` or only thumbnails | Extractor/JS/auth | Compare metadata with and without the expected JS runtime; check authentication requirement and yt-dlp version | Supply supported Deno/EJS runtime or update the failing extractor instance |
| Deno/EJS/player challenge error | JavaScript runtime | Resolve Deno used by Parabolic and the project; record version and executable path | Configure a verified runtime for the failing environment |
| DNS failure, timeout, TLS/certificate error | Network | Resolve the URL host; test TCP 443; compare system, WinHTTP, environment, VPN and application proxy paths without exposing credentials | Correct only the failing network layer; do not replace cookies for a DNS/TLS failure |
| Download starts then stalls | Media transfer/network | Observe whether bytes and fragment index advance; note one failing CDN host/status; stop duplicate downloads | Resume once after addressing network/rate-limit cause; avoid parallel retry storms |
| Audio/video downloaded but no final file | FFmpeg/post-processing | Resolve FFmpeg path/version; inspect the final post-processing error and output directory | Point the failing environment to a verified FFmpeg or correct the format/merge option |
| Exit code zero but expected file absent | Output selection/filesystem | Check resolved output template, filters, playlist mode, final extension, and directory listing | Correct output template or caller expectation; verify the actual file |
| Access denied, invalid filename, path too long, disk full | Filesystem | Check output directory, free space, Windows path length, reserved characters, antivirus quarantine, and write access | Choose an approved writable path or shorten/sanitize the template |
| CLI/project succeeds but Parabolic fails | Frontend/config/version | Compare bundled yt-dlp, Deno, FFmpeg, proxy, cookies, format selection, output template and working directory | Change the single differing Parabolic setting or bundled component |
| Parabolic succeeds but project fails | Project environment | Compare Python environment, `yt_dlp` package, config keys, runtime discovery, proxy variables and output handling | Repair the project dependency/configuration rather than Parabolic |

## Minimal comparison probes

Prefer simulation and metadata extraction before downloading media:

```powershell
yt-dlp --version
yt-dlp --simulate --no-playlist --print "%(extractor)s | %(id)s | %(availability)s" "AUTHORIZED_URL"
```

For the project Python environment, query package metadata without importing project modules:

```powershell
python -c "import importlib.metadata as m; print(m.version('yt-dlp'))"
```

Use `--verbose` only when the ordinary error is insufficient. Keep the raw log local, redact cookie/header/proxy values and signed query strings, and share only the minimal relevant lines.

## Stop conditions

Stop and report rather than escalating retries when:

- the media is DRM-protected or the requested action would bypass a paywall or access control;
- account ownership or download authorization is unclear;
- a CAPTCHA, bot challenge, or `429` persists;
- the cookie/session appears revoked or exposed;
- the next step would modify proxy, DNS, browser profile, credentials, application configuration, or installed software without approval.
