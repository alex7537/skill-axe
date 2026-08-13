# Pseudo-label and distillation audit

- Interpret overlap as agreement with the teacher, not absolute segmentation accuracy.
- Record teacher model/version, preprocessing, prompts, propagation settings, and failure-handling behavior.
- Ask whether target identity entered through a point, box, object ID, prior mask, task state, or human selection. If the student sees only RGB, that information is absent from its input.
- Treat target-selection failures separately from boundary/segmentation failures.
- Prefer regenerating missing pseudo-labels with the original prompt contract when available; preserve original group and role.
- Check for segment-level zero filling, propagation loss, boundary overrun, and silent service failures.
- Do not use a student prediction alone to overwrite a teacher label.
