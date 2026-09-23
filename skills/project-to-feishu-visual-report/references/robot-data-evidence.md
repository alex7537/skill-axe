# Robot-data summary: lessons from MCAP/HDF5 playback

Read only for a similar robot-data visualization project. These are checks learned from a completed summary, not a promise about future repository versions.

| Evidence trap | Check that changes the conclusion |
|---|---|
| Both inputs end in `.hdf5` | Compare actual groups, arrays, joint names, poses and camera payloads before choosing a visualizer. |
| A dated note says camera/mimic support was added | Verify the current parser, defaults, reads and blueprint; those changes may have existed only as uncommitted work elsewhere. |
| A helper exists beside tracked files | Report whether it is untracked; the baseline commit alone may not reproduce the workflow. |
| A robot's hand meshes are vendored | Resolve the full robot URDF and transitive assets; the default may point into a sibling repository. |
| All columns are named `action` | Inspect preprocessing semantics; a vector may mix measured arm positions and commanded finger targets. |
| A shared `frame` timeline exists | Determine whether it represents collection frames, processed row numbers or inserted interpolation frames. Do not infer wall time or FPS. |
| Multiple ROS timestamp timelines are recorded | Describe timestamp fallbacks; do not infer hardware synchronization merely from logging timestamps. |
| Force arrows are next to TCP | Verify the source wrench frame and transform chain; end-effector link and TCP may differ. |
| RGB resolution is unchanged after video encoding | Re-encoding can still be lossy; do not equate unchanged resolution with lossless fidelity. |
| A five-episode contact sheet looks correct | Caption its selection/coverage; do not generalize to all episodes or claim measured success rate. |
| `rrd verify` succeeds | Establishes recording validity within that check, not Viewer rendering, motion correctness or a new conversion run. |

A useful diagram set separates input routes from state/action/pose/force semantics. Keep each figure focused. Preserve exact topic/path mappings in a nearby table rather than cramming full identifiers into every diagram node.

For a real sample image, explain camera ordering, selected timepoints and whether it is a contact sheet or Viewer screenshot. State which inspection was repeated now and which measurements came from historical notes. Retain source file/symbol and dated note references in the document without copying private dataset files into the skill.
