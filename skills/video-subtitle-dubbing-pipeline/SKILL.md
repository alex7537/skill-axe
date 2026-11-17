---
name: video-subtitle-dubbing-pipeline
description: Process local videos into clips with speech-synchronized translated subtitles, validate hard or soft subtitle delivery, and create consented synthetic dubbing while preserving timing and background audio. Use for FFmpeg, faster-whisper, SRT, subtitle burn-in, subtitle-track, voice conversion, or multilingual dubbing tasks.
---

# Video Subtitle and Dubbing Pipeline

Produce a playable, verified media artifact. Keep source media unchanged and treat upload or publication as a separate action requiring explicit authorization.

## Inspect before processing

- Locate the exact source without printing unrelated media filenames.
- Use `ffprobe` to record duration, primary video/audio streams, resolution, frame rate, codecs, chapters, attachments, and existing subtitle streams.
- Confirm the requested time range. For an approximate opening clip, use an exact duration such as 600 seconds and report the actual muxed duration.
- Reuse machine-level FFmpeg and model caches, but use the repository's own Python environment. Test CPU inference before treating GPU acceleration as available.

## Build speech-synchronized subtitles

1. Extract or trim a working clip. Map the primary video and audio streams explicitly so attachments and data streams do not become accidental outputs.
2. Transcribe with word timestamps and voice-activity detection. Use `scripts/build_speech_timed_srt.py` when faster-whisper is available.
3. Group words into readable cues using real pauses. Target roughly 1–4 seconds per cue, end each cue close to the last spoken word, and ensure adjacent cues never overlap.
4. Remove non-dialogue hallucinations such as `Music` when the user wants captions only while a person speaks.
5. Translate cue text while preserving every cue number and timestamp. Review names, locations, units, and domain terms manually; ASR errors such as `pedal` versus `paddle` must be corrected before translation is accepted.
6. Check at least one speaking frame and one silent frame. A silent frame must contain no lingering caption.

## Choose exactly one subtitle delivery mode

- **Hard subtitles:** burn SRT/ASS into the video. Use when playback compatibility matters or the user asks for visible subtitles. The MP4 should contain video and audio only.
- **Soft subtitle track:** mux a selectable subtitle stream, normally `mov_text` for MP4. Do not also burn the same subtitles.
- **External SRT:** deliver the video unchanged with a sidecar SRT. Do not also burn the same subtitles unless the user explicitly asks for both.

Never place a same-basename SRT beside a hard-subtitled video in the delivery folder. Many players auto-load it and display two copies of the same subtitle.

For hard subtitles, prefer a common CJK font, a thin outline, safe bottom margin, H.264 video, AAC audio, and `+faststart`. If hardware encoding fails, fall back to CPU encoding and report why.

## Verify the artifact

- Confirm duration, dimensions, codecs, and stream count with `ffprobe`.
- Parse the SRT and assert: non-empty cues, valid increasing timestamps, no overlaps, and a reasonable maximum cue duration.
- Extract screenshots during speech and silence to visually confirm font rendering, placement, and disappearance.
- Keep intermediate media outside the final delivery directory. Deliver only the intended version so the user cannot confuse drafts or trigger automatic sidecar subtitles.

## Add dubbing only with an authorized voice

Use the user's own voice, a speaker who supplied explicit permission, a licensed stock/synthetic voice, or a fictional preset that does not imitate an identifiable person.

Do not clone or imitate a real actor, celebrity, creator, or other identifiable person without documented permission, including requests framed as “use a Captain America actor's voice” or “use Daniel Wu's voice.” Do not search for unauthorized voice models or scrape reference clips. Offer a licensed Mandarin male voice with comparable broad qualities instead, such as calm, cinematic, mature, or energetic. Preserve a consent/provenance note with the output and disclose synthetic dubbing when publishing.

For an authorized dubbing job:

1. Read [references/open-source-voice-options.md](references/open-source-voice-options.md) and choose TTS or voice conversion based on the desired output.
2. Generate one audio segment per speech cue from the reviewed source or Chinese translation.
3. Match each segment to its cue window. Prefer rewriting or regenerating over extreme time stretching; use small tempo corrections only when necessary.
4. Preserve ambience/music with source separation when available. Otherwise duck the original dialogue during synthetic speech rather than muting the entire soundtrack.
5. Assemble a continuous narration track, mix it with background audio, and mux it into a new output. Preserve the original version separately.
6. Check intelligibility, lip/timing mismatch, clipping, loudness consistency, and at least three transitions between speech and silence.

Do not upload or publish the result without explicit authorization for that specific action.
