# =============================================================================
# FILE:      irrigation/fft_analysis.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/fft_analysis.py
# PURPOSE:   FFT-based vibration fault classification. Preserved verbatim
#            from S_Backend.py so pump-fault behavior is identical.
# =============================================================================

from __future__ import annotations
import numpy as np
import scipy.fft

from . import config as cfg


def analyze_vibration_fft(vibration_samples, sampling_rate: int = cfg.FFT_SAMPLING_RATE):
    if len(vibration_samples) < cfg.FFT_SAMPLES:
        return "Normal", 0.0, {}

    yf = scipy.fft.fft(vibration_samples[: cfg.FFT_SAMPLES])
    xf = scipy.fft.fftfreq(cfg.FFT_SAMPLES, 1 / sampling_rate)
    mags = np.abs(yf[: cfg.FFT_SAMPLES // 2])
    freqs = xf[: cfg.FFT_SAMPLES // 2]

    dom_idx = int(np.argmax(mags))
    dom_freq = float(freqs[dom_idx])

    def peak_above(hz):
        mask = freqs > hz
        return float(mags[np.argmax(mags[mask])]) if mask.any() else 0.0

    p1 = peak_above(20)
    p2 = peak_above(40)
    p3 = peak_above(60)
    p4 = peak_above(80)

    fault = "Normal"
    if p2 > 50 or p3 > 40:
        fault = "Bearing Wear"
    elif p2 > 35 and p2 > p1 * 1.5:
        fault = "Misalignment"
    elif p1 > 30 and p1 > p2 * 2:
        fault = "Imbalance"
    elif p2 > 30 and p3 > 25 and p4 > 20:
        fault = "Looseness"
    elif float(np.mean(mags[20:100])) < 20:
        fault = "Cavitation"

    return fault, dom_freq, {"1x": p1, "2x": p2, "3x": p3, "4x": p4}
