# LichtFeld 360 Plugin — RadiaSight fork

A plugin for [LichtFeld Studio](https://github.com/MrNeRF/LichtFeld-Studio) that turns 360 camera footage into datasets for Gaussian splatting. It extracts frames, optionally masks unwanted objects with SAM 3, reconstructs camera poses with COLMAP, and prepares the result for training.

Supports Insta360 `.insv`, DJI `.osv`, stitched equirectangular videos, and image-folder workflows.

## Changes from upstream

Forked from [alexmgee/lichtfeld-360-plugin](https://github.com/alexmgee/lichtfeld-360-plugin), version **0.5.0**. This fork tracks fixes and adjustments for our Kubuntu/Linux workflow:

- **Linux CUDA dependencies:** use `pycolmap-cuda12==4.1.0` and the CUDA 12.8 PyTorch index on Linux, avoiding the CPU-only PyCOLMAP build and conflicting CUDA 13 dependencies.
- **Linux worker launch:** use `.venv/bin/python` on Linux instead of the hard-coded Windows `Scripts/python.exe` path.
- **SAM 3 model browser:** use KDE's `kdialog` (or `zenity`) on Linux instead of silently failing through a Windows-only picker.
- **Progress display:** explicitly poll the panel every 100 ms, detect status-text changes, and recognize lowercase extraction/scoring messages. This addresses stale “Pipeline queued” and extraction labels.
- **Frame sampling:** raise the FPS control limit from 5 to 30. For dual-fisheye footage, each sampled frame pair produces two lens images.

These are local compatibility fixes, not a full cross-platform validation. The progress changes have targeted checks but still need live GUI verification.

## Quick start

1. Install this fork as a plugin in LichtFeld Studio.
2. With LichtFeld closed, run `uv sync` in the installed plugin directory to install its Python dependencies (Python 3.12).
3. Restart LichtFeld and open **360 Plugin**.
4. Select your input, a separate output folder, and a sampling rate; click **Process**.
5. Import the resulting dataset into LichtFeld and train.

SAM 3 masking is optional; its weights require accepting Meta's access terms. Black areas painted into footage are not equivalent to exclusion masks.

To verify the Linux CUDA dependency:

```bash
.venv/bin/python -c 'import pycolmap; print(pycolmap.__version__); print("CUDA:", pycolmap.has_cuda)'
```

The CUDA 12 wheels require a compatible NVIDIA driver; they do not change the system CUDA compiler.

For detailed features and original documentation, see the [upstream README](https://github.com/alexmgee/lichtfeld-360-plugin/blob/main/README.md).

## License

GPL-3.0-or-later. Original plugin by Alex Gee; see [LICENSE](LICENSE). Bundled tools, dependencies, and model weights retain their respective licenses.
