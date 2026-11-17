# Open-source voice options

Consult the official project documentation before installation because model licenses and hardware requirements can change.

## Selection guide

| Project | Best fit | Current documented capabilities | Important constraint |
|---|---|---|---|
| [CosyVoice](https://github.com/QwenAudio/CosyVoice) | Mandarin or cross-language dubbing from an authorized reference | Multilingual and cross-lingual zero-shot synthesis; Chinese and multiple Chinese dialects/accents; Apache-2.0 repository | Verify the selected checkpoint's model terms separately. Prefer this first for Chinese dubbing. |
| [OpenVoice](https://github.com/myshell-ai/OpenVoice) | Lightweight cross-language tone-color transfer | V2 documents native English, Spanish, French, Chinese, Japanese, and Korean support; MIT license | Quality and prosody still require clip-by-clip evaluation. |
| [RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) | Speech-to-speech timbre conversion while retaining an existing performance | Voice conversion with training/inference UI and short-data workflows | It does not translate the script. Training data and the target voice must be authorized. |
| [F5-TTS](https://github.com/SWivid/F5-TTS) | Experimental multi-speaker or style-controlled TTS | Reference-audio inference, multi-style and multi-speaker generation | Code is MIT, but the official pretrained models are documented as CC-BY-NC; do not assume commercial permission. |

## TTS versus voice conversion

- Choose multilingual TTS when the words change language, especially English-to-Chinese dubbing. It generates the translated script directly and is easier to align cue by cue.
- Choose voice conversion when a consented performer has already recorded the desired words and the goal is only to change timbre while preserving delivery.
- A practical Chinese dubbing baseline is: translated speech cues → CosyVoice with an authorized Mandarin reference or licensed preset → duration alignment → background mix → final mux.
- RVC can be an optional second stage only when the target model and its training material are authorized.

## Evaluation gates

Run a 20–30 second sample before processing a full video. Evaluate pronunciation, natural Mandarin prosody, cue-window fit, noise, metallic artifacts, clipped breaths, and speaker similarity only against the authorized reference.

Keep model checkpoints, reference-audio provenance, consent evidence, and generated audio out of Git unless the repository is explicitly designed and licensed to store them.
