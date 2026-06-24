# OpenVoice Singing Scale: Issues & Alternatives

This document outlines the build and execution issues encountered with the setup in `tools/make-singing-scale` and presents the technical considerations and options for generating a singing scale.

---

## 1. Issues Identified & Resolved

We ran into several blocking errors during the build and run steps:

### A. Incorrect Package Index for PyTorch
* **Issue:** The script attempted to install PyTorch CPU with `--index-url https://pytorch.org`. This is a website, not a pip package index.
* **Fix:** Corrected the package index to PyTorch's official CPU wheel distribution index: `https://download.pytorch.org/whl/cpu`.

### B. Generic and Typo-ridden URLs
* **Issue 1:** The script ran `git clone https://github.com .`, which is not a valid clone URL.
  * **Fix:** Corrected to the official OpenVoice repository: `https://github.com/myshell-ai/OpenVoice.git`.
* **Issue 2:** The model checkpoints URL was written as `myshell-public-repo-host.s3.amazonaws.com` (missing the 'ing' suffix), returning 404 / 403 errors.
  * **Fix:** Corrected to a verified community Hugging Face resolve URL: `https://huggingface.co/kevinwang676/openvocie-v2/resolve/main/checkpoints_v2_0417.zip`.

### C. Missing Compilation Dependencies in base Image
* **Issue:** PyAV (`av==10.0.0`) compile steps require development headers.
* **Fix:** Added `build-essential`, `pkg-config`, and `libav*-dev` packages to the container's `apt-get` command.

### D. Cython 3 Compilation Failure with PyAV
* **Issue:** Cython 3 defaults C-function declarations to `noexcept`, causing a compilation mismatch with the older codebase of PyAV (`av==10.0.0`).
* **Fix:** Pre-installed `cython<3` inside the container and built PyAV using the `--no-build-isolation` flag.

### E. FFmpeg / Debian OS Version Incompatibility
* **Issue:** Under modern Debian base images (like Bookworm / Debian 12), the system FFmpeg package is version 5/6. PyAV `av==10.0.0` is incompatible with FFmpeg 5/6 and fails to compile due to deprecated symbols (`AV_OPT_TYPE_CHANNEL_LAYOUT`).
* **Fix:** Locked the base image to `python:3.10-slim-bullseye` (Debian 11), which ships with FFmpeg 4.x compatible with `av==10.0.0`.

### F. Hardcoded CUDA Device in OpenVoice
* **Issue:** The OpenVoice helper module `se_extractor.py` hardcodes `device="cuda"` inside `WhisperModel`, causing CPU execution crashes.
* **Fix:** Patched `openvoice/se_extractor.py` during build time to dynamically check for GPU availability:
  `device="cuda" if torch.cuda.is_available() else "cpu"`
  `compute_type="float16" if torch.cuda.is_available() else "float32"`

### G. Setuptools 82.0.0 Removal of `pkg_resources`
* **Issue:** In February 2026, `setuptools` version 82.0.0 was released, which completely removed the long-deprecated `pkg_resources` module. Modern Python packages like `librosa` failed at import with `ModuleNotFoundError: No module named 'pkg_resources'`.
* **Fix:** Pinned `setuptools<82` in all build steps to restore the module.

---

## 2. Alternatives & Design Considerations

When exploring alternatives for generating a singing scale ("do re mi fa so la ti do"), we prioritize **voice models that intrinsically understand the concept of pitch** rather than using generic models and applying a post-hoc digital signal processing (DSP) pitch shift (like WSOLA, PSOLA, or phase vocoder resampling).

### Preferred: Model-Level / Latent Pitch Control (OpenVoice/MeloTTS)
* **How it works:** OpenVoice V2's `ToneColorConverter.convert` takes a `pitch_scale` parameter directly. The neural network decoder uses this scale factor during generation to dictate the fundamental frequency (F0) contour of the synthesized phonemes.
* **Why we prefer this:**
  * **Intrinsically Pitch-Aware:** The model adjusts formant frequencies, breathing, and vocal tract length characteristics naturally in the latent space as the pitch changes, preserving natural-sounding voice quality.
  * **Vocal Quality:** Avoids the mechanical "chipmunk" or phasey artifacts associated with post-hoc time-domain or frequency-domain DSP shifting.

### Alternative A: MeloTTS Direct API (Simplified Deep Learning)
* **Description:** Bypasses OpenVoice's zero-shot voice cloning layers (whisper models, se-extractor) and interfaces directly with the underlying MeloTTS API.
* **Pitch Control:** MeloTTS also exposes pitch controls at the synthesis/morphing level.
* **Pros:** Bypasses heavy checkpoints downloading (saving ~120MB) and reduces model initialization times.

### Alternative B: Formant-based Rule Synthesizer (eSpeak)
* **Description:** Rule-based formant synthesis.
* **Pitch Control:** Formant synthesizers accept direct F0 frequency targets (in Hz) per phoneme.
* **Pros:** Extremely lightweight, fast, and gives exact mathematical frequency control.
* **Cons:** Sounds robotic, though it fits a synthetic, retro instrument aesthetic.

### Alternative C: Web Audio API (Browser Synthesizer)
* **Description:** Generate the singing scale directly in the web browser using FM synthesis or custom formant filters over oscillator sources.
* **Pros:** Zero backend overhead.
