"""Create short, non-overlapping SRT cues from actual speech word timings."""

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Cue:
    start: float
    end: float
    text: str


def srt_time(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def group_words(words, max_duration: float, max_chars: int, pause: float) -> list[Cue]:
    cues: list[Cue] = []
    current = []

    def flush() -> None:
        nonlocal current
        if not current:
            return
        text = "".join(word.word for word in current).strip()
        normalized = text.lower().strip("[]().! ")
        if normalized not in {"music", "music playing"}:
            cues.append(Cue(max(0.0, current[0].start - 0.05), current[-1].end + 0.12, text))
        current = []

    for word in words:
        if word.start is None or word.end is None or not word.word.strip():
            continue
        gap = word.start - current[-1].end if current else 0
        proposed = "".join(item.word for item in current + [word]).strip()
        duration = word.end - current[0].start if current else word.end - word.start
        if current and (gap >= pause or duration > max_duration or len(proposed) > max_chars):
            flush()
        current.append(word)
        if word.word.strip().endswith((".", "?", "!")) and current[-1].end - current[0].start >= 1.0:
            flush()
    flush()

    for previous, following in zip(cues, cues[1:]):
        previous.end = min(previous.end, following.start - 0.03)
    return cues


def write_srt(cues: list[Cue], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8-sig", newline="\n") as handle:
        for index, cue in enumerate(cues, 1):
            handle.write(f"{index}\n{srt_time(cue.start)} --> {srt_time(cue.end)}\n{cue.text}\n\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--model", default="small")
    parser.add_argument("--language")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--max-duration", type=float, default=4.0)
    parser.add_argument("--max-chars", type=int, default=42)
    parser.add_argument("--pause", type=float, default=0.5)
    args = parser.parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise SystemExit("faster-whisper is required in the active project environment") from exc

    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)
    segments, info = model.transcribe(
        str(args.input),
        language=args.language,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 400},
    )
    words = [word for segment in segments for word in (segment.words or [])]
    cues = group_words(words, args.max_duration, args.max_chars, args.pause)
    if not cues:
        raise SystemExit("no speech cues were detected")
    write_srt(cues, args.output)
    print(f"language={info.language} words={len(words)} cues={len(cues)} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
