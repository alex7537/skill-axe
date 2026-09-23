---
name: anschreiben-masterarbeit
description: Create or adapt a concise German Masterarbeit motivations letter (Anschreiben) for Yurui Zhang when the user says “使用 anschreiben-masterarbeit skill 给这个岗位写动机信”, asks for an Anschreiben/Motivationsschreiben or an accompanying Word file for a thesis role, or wants a company-specific version. Use the confirmed Fraunhofer IGCV Word letter as the sole baseline; preserve its core research narrative and only customize the employer and role-specific fit.
---

# Anschreiben Masterarbeit

Use the confirmed reference [`assets/Yurui_Zhang_Motivationsschreiben_Fraunhofer_IGCV.docx`](assets/Yurui_Zhang_Motivationsschreiben_Fraunhofer_IGCV.docx) as the sole content and structural authority. Produce a natural German student-style letter of about 180–220 words. Keep it short, specific, and research-oriented; do not turn it into a CV summary or generic company praise.

## Required structure

1. Sender block, exactly:

   ```
   Yurui Zhang
   M.Sc. Mechatronik und Robotik
   Leibniz Universität Hannover
   ```

2. Recipient block: target institution, relevant department/team if known, and full postal address. Do not invent a department or address; omit unknown lines instead of guessing.
3. `Hannover, <date>`.
4. `Bewerbung um eine Masterarbeit: <role title>`.
5. `Sehr geehrte Damen und Herren,` unless a named contact is supplied.
6. Closing exactly:

   ```
   Mit freundlichen Grüßen

   Yurui Zhang
   ```

## Body contract

Write four compact paragraphs. Preserve paragraphs 2 and 3 materially unchanged unless the user explicitly asks to change them.

1. State in one sentence that the advertised Masterarbeit is very close to the questions Yurui is currently exploring independently. Adapt only the role/topic phrase.
2. Keep this core narrative:

   > In meinem derzeitigen Robot-Learning-Projekt untersuche ich verschiedene Ansätze zur Generierung kontinuierlicher Roboteraktionen. Dabei verwende ich weitgehend dieselben Daten und dieselbe Aufgabenstellung, um unterschiedliche Policy-Ansätze möglichst fair miteinander zu vergleichen. Konkret habe ich Conditional Flow Matching, Diffusion Policy und IMLE umgesetzt und untersucht. Die Modelle unterscheiden sich dabei vor allem darin, wie Aktionen generiert werden und welches Trainingsziel beziehungsweise welche Loss-Funktion zur Optimierung verwendet wird.

3. Keep this core narrative:

   > Darauf aufbauend habe ich begonnen, den Ansatz in Richtung World Models zu erweitern. Zusätzlich zur Aktionsvorhersage wird dabei Videoinformation über einen Video-Encoder verarbeitet und als weiteres Trainingssignal verwendet. Besonders interessiert mich dabei die Frage, ob und in welchem Umfang eine zusätzliche Video-Loss die Qualität und Generalisierungsfähigkeit der Policy tatsächlich verbessert.

4. Tailor only this paragraph to the position. Tie the role's concrete technical themes to the existing exploration, for example VLA, NVIDIA Isaac Sim, Domain Randomization, synthetic data, humanoid robotics, Sim-to-Real, real hardware, simulation, imitation learning, or policy evaluation. Do not make unsupported claims about tools, deployments, hardware access, or results.

## Style guardrails

- Aim for 180–220 German words in the body; prioritize the four paragraphs over padding.
- Sound like a technically strong German Master’s student: direct, calm, and natural.
- Keep the self-directed research thread central: comparable data/task, CFM/DP/IMLE, distinct action-generation and objective/loss mechanisms, then the Video-Encoder/Video-Loss World Model extension.
- Avoid empty praise, buzzword lists, broad claims of passion, repeated CV facts, and overly formal or AI-sounding transitions.
- Do not substantially rewrite the fixed second or third paragraph by default.
- Verify the role title, institution spelling, department, address, and job-specific terminology from material the user provides or reliable sources before finalizing.

## Word output rules

When the user requests a local `.docx` after confirming the letter text:

- Start by copying the confirmed IGCV Word document. Preserve its page setup, styles, fonts, sections, compatibility namespaces, and all untouched package parts. Change only the recipient, date or subject when requested, and the two position-specific body paragraphs. Do not rebuild the document from a blank file or broadly parse and reserialize `word/document.xml`.
- Delete source recipient lines that are no longer needed rather than leaving empty address paragraphs.
- Name the deliverable `Yurui_Zhang_Motivationsschreiben_<Organisation>.docx`. Derive `<Organisation>` from the recipient block in the letter, normally its first official company or institution line. Confirm that this name matches the recipient text before delivery.
- Use a filesystem-safe form of the organisation name: replace spaces and punctuation with single underscores; keep letters, digits, underscores, and German characters. If the official name is absent or cannot form a valid filename, use the closest unambiguous institution or brand name appearing in the recipient block. Do not invent a name.
- Render and inspect the final `.docx` before delivery. A successful archive check alone is insufficient.

## Gotcha

Editing every XML node through a generic XML serializer can discard Word compatibility namespace declarations and cause Word to repair or display the file incorrectly. In template-following mode, apply narrow text substitutions to a copied package and leave the remaining XML byte-for-byte intact.

## Trigger example

`使用 anschreiben-masterarbeit skill 给这个岗位写动机信`
