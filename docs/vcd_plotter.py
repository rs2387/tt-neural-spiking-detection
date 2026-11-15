"""Visualise the NeuroDiff EMA detector from project.vcd.

No vcdvcd package is required: only NumPy and Matplotlib.
The VCD's own timescale and signal transition timestamps are used.

Run from the folder containing project.vcd:
    python plot_neurodiff_vcd.py

The script saves three PNG figures and opens them if SHOW_PLOTS is True.
"""

from pathlib import Path
import re

import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 1. SETTINGS
# ==========================================

folder = Path(__file__).resolve().parent
vcd_path = folder / "project.vcd"
text_path = folder / "neural_samples.txt"  # optional

THRESHOLD = 30
zoom_start = 0.002       # 2 ms (the uploaded VCD lasts only 10 ms)
zoom_end = 0.004         # 4 ms
edge_zoom_half_width_ns = 80
SHOW_PLOTS = True  # Set False to only save PNG files

# Exact paths present in the new VCD (aliases share their data).
SIGNALS = {
    "sample": "tt_um_rs2387_project_tb.sample",
    "ema": "tt_um_rs2387_project_tb.dut.ema",
    "abs_diff": "tt_um_rs2387_project_tb.dut.detector.abs_diff",
    "sample_valid": "tt_um_rs2387_project_tb.sample_valid",
    "ema_valid": "tt_um_rs2387_project_tb.dut.ema_valid",
    "raw_spike": "tt_um_rs2387_project_tb.raw_spike",
    "previous_raw_spike": "tt_um_rs2387_project_tb.dut.previous_raw_spike",
    "filtered_spike": "tt_um_rs2387_project_tb.filtered_spike",
    "ena": "tt_um_rs2387_project_tb.ena",
    "sample_count": "tt_um_rs2387_project_tb.sample_count",
    "spike_count": "tt_um_rs2387_project_tb.spike_count",
}


# ==========================================
# 2. LOAD ONLY THE SIGNALS WE NEED
# ==========================================

def load_selected_vcd(path, signal_paths):
    """Read a VCD without keeping millions of irrelevant clock transitions."""
    signals = {name: [] for name in signal_paths}
    target_by_path = {path: name for name, path in signal_paths.items()}
    target_by_id = {}
    scopes = []
    timescale_seconds = None
    last_tick = 0
    time_tick = 0
    definitions_done = False

    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            line = line.strip()
            if not line:
                continue

            if not definitions_done:
                if line.startswith("$timescale"):
                    match = re.search(r"\$timescale\s+(\d+)\s*(fs|ps|ns|us|ms|s)\s+\$end", line)
                    if not match:
                        raise ValueError("Unsupported VCD timescale: " + line)
                    multiplier = {
                        "fs": 1e-15, "ps": 1e-12, "ns": 1e-9,
                        "us": 1e-6, "ms": 1e-3, "s": 1.0,
                    }[match.group(2)]
                    timescale_seconds = int(match.group(1)) * multiplier
                elif line.startswith("$scope"):
                    scopes.append(line.split()[2])
                elif line.startswith("$upscope"):
                    scopes.pop()
                elif line.startswith("$var"):
                    parts = line.split()
                    identifier, base_name = parts[3], parts[4]
                    full_path = ".".join(scopes + [base_name])
                    name = target_by_path.get(full_path)
                    if name is not None:
                        target_by_id[identifier] = name
                elif line.startswith("$enddefinitions"):
                    definitions_done = True
                continue

            if line.startswith("#"):
                time_tick = int(line[1:])
                last_tick = time_tick
                continue

            if line[0] in "01xXzZ":
                value_text, identifier = line[0], line[1:]
            elif line[0] in "bB":
                pieces = line.split()
                if len(pieces) != 2:
                    continue
                value_text, identifier = pieces[0][1:], pieces[1]
            else:
                continue

            name = target_by_id.get(identifier)
            if name is None:
                continue

            value = None if any(c in value_text.lower() for c in "xz") else int(value_text, 2)
            signals[name].append((time_tick, value))

    if timescale_seconds is None:
        raise ValueError("Cannot find VCD timescale")

    missing = [name for name, changes in signals.items() if not changes]
    if missing:
        raise KeyError(f"Signals missing from VCD: {missing}")

    return signals, timescale_seconds, last_tick


signals, seconds_per_tick, last_tick = load_selected_vcd(vcd_path, SIGNALS)


def arrays(name):
    """Return exact change times (seconds) and values for a VCD signal."""
    changes = signals[name]
    times = np.array([tick * seconds_per_tick for tick, _ in changes], dtype=float)
    values = np.array([value if value is not None else np.nan for _, value in changes], dtype=float)
    return times, values


def values_at(name, times):
    """Sample a VCD signal at exact times, holding its last recorded value."""
    change_times, change_values = arrays(name)
    indices = np.searchsorted(change_times, times, side="right") - 1
    if np.any(indices < 0):
        raise ValueError(f"No initial value for {name}")
    return change_values[indices]


def rising_edges(name):
    times, values = arrays(name)
    previous = np.r_[0, values[:-1]]
    return times[(values == 1) & (previous == 0)]


# ==========================================
# 3. INSPECT AND VERIFY THE DETECTOR
# ==========================================

valid_sample_times = rising_edges("sample_valid")
raw_rise_times = rising_edges("raw_spike")
spike_times = rising_edges("filtered_spike")
recording_duration = last_tick * seconds_per_tick

# Compare the actual combinational outputs with the equations used in RTL.
all_change_times = np.unique(np.concatenate([
    arrays(name)[0] for name in (
        "sample", "ema", "abs_diff", "raw_spike", "previous_raw_spike",
        "filtered_spike", "ema_valid", "ena"
    )
]))

sample_at = values_at("sample", all_change_times)
ema_at = values_at("ema", all_change_times)
abs_diff_at = values_at("abs_diff", all_change_times)
raw_at = values_at("raw_spike", all_change_times)
previous_at = values_at("previous_raw_spike", all_change_times)
filtered_at = values_at("filtered_spike", all_change_times)
ema_valid_at = values_at("ema_valid", all_change_times)
enabled_at = values_at("ena", all_change_times)

expected_diff = np.abs(sample_at - ema_at)
expected_raw = (expected_diff > THRESHOLD).astype(int)
expected_filtered = (
    (raw_at == 1) & (previous_at == 0) &
    (ema_valid_at == 1) & (enabled_at == 1)
).astype(int)

print("\n========== NEURODIFF VCD RESULTS ==========")
print(f"VCD timescale: {seconds_per_tick:.0e} seconds per tick")
print(f"Simulation duration: {recording_duration * 1000:.6f} ms")
print(f"Valid sample pulses: {len(valid_sample_times)}")
print(f"Final sample_count in VCD: {int(arrays('sample_count')[1][-1])}")
print(f"Raw spike rising edges: {len(raw_rise_times)}")
print(f"Filtered spike rising edges: {len(spike_times)}")
print(f"Final spike_count in VCD: {int(arrays('spike_count')[1][-1])}")
print(f"Absolute-difference mismatches: {np.count_nonzero(abs_diff_at != expected_diff)}")
print(f"Raw comparator mismatches: {np.count_nonzero(raw_at != expected_raw)}")
print(f"Filtered comparator mismatches: {np.count_nonzero(filtered_at != expected_filtered)}")
print("Filtered spike times (ms):", np.round(spike_times * 1000, 6).tolist())

# The text file isn't needed for plotting the VCD; compare inputs if it's present.
if text_path.exists():
    source = np.loadtxt(text_path, dtype=np.int64, ndmin=2)
    source_samples = source[:, 0] & 0x7FFF  # Bits physically connected to 15-bit DUT
    if len(source_samples) == len(valid_sample_times):
        vcd_samples = values_at("sample", valid_sample_times).astype(int)
        input_errors = np.count_nonzero(source_samples != vcd_samples)
        print(f"Optional input comparison: {input_errors} mismatches / {len(source_samples)}")
    else:
        print("Optional input comparison skipped: text rows and valid pulses differ")


# ==========================================
# 4. PLOT THE VCD SIGNALS
# ==========================================

def step_signal(ax, name, label=None):
    times, vals = arrays(name)
    # Extend final state to the end of simulation.
    times = np.r_[times, recording_duration]
    vals = np.r_[vals, vals[-1]]
    ax.step(times * 1000, vals, where="post", label=label or name, linewidth=1.3)


def values_in_window(name, start_s, end_s):
    """Include the held starting value plus transitions within a plot window."""
    times, vals = arrays(name)
    start_value = values_at(name, np.array([start_s]))
    return np.r_[start_value, vals[(times >= start_s) & (times <= end_s)]]


def plot_waveform(start_s, end_s, title, output_file):
    figure, axes = plt.subplots(
        7, 1, figsize=(14, 11), sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1.5, 0.75, 0.75, 0.75, 0.75, 0.85]},
        layout="constrained",
    )

    step_signal(axes[0], "sample", "Input sample")
    step_signal(axes[0], "ema", "EMA")
    axes[0].set_ylabel("ADC counts")
    axes[0].legend(loc="upper right")

    # Ignore startup EMA=0 when choosing y-axis bounds for the full plot.
    ema_ready_times = rising_edges("ema_valid")
    settled_start = max(start_s, ema_ready_times[0]) if len(ema_ready_times) else start_s
    adc_values = np.r_[values_in_window("sample", settled_start, end_s),
                       values_in_window("ema", settled_start, end_s)]
    adc_margin = max(5, (np.max(adc_values) - np.min(adc_values)) * 0.12)
    axes[0].set_ylim(np.min(adc_values) - adc_margin,
                     np.max(adc_values) + adc_margin)

    step_signal(axes[1], "abs_diff", "|sample - EMA|")
    axes[1].axhline(THRESHOLD, linestyle="--", label=f"Threshold = {THRESHOLD}")
    axes[1].set_ylabel("Difference")
    axes[1].legend(loc="upper right")
    diff_values = values_in_window("abs_diff", settled_start, end_s)
    axes[1].set_ylim(-2, max(THRESHOLD + 5, np.max(diff_values) + 5))

    for ax, name, label in (
        (axes[2], "sample_valid", "Sample valid"),
        (axes[3], "ema_valid", "EMA valid"),
        (axes[4], "raw_spike", "Raw spike"),
        (axes[5], "previous_raw_spike", "Previous raw"),
        (axes[6], "filtered_spike", "Filtered spike"),
    ):
        step_signal(ax, name)
        ax.set_ylabel(label)
        ax.set_ylim(-0.15, 1.15)
        ax.set_yticks([0, 1])

    # Short 20 ns spikes are invisible at millisecond scale.
    # Mark their rising edges so they remain visible in the full plot.
    for event_time in spike_times:
        if start_s <= event_time <= end_s:
            axes[6].axvline(event_time * 1000, linewidth=1.2, linestyle=":")

    for ax in axes:
        ax.grid(alpha=0.25)
        ax.set_xlim(start_s * 1000, end_s * 1000)

    if end_s - start_s < 0.00001:
        # Show ns offsets for tiny clock-level windows rather than a confusing
        # Matplotlib '+2.1' milliseconds offset annotation.
        from matplotlib.ticker import FuncFormatter
        centre_ms = (start_s + end_s) * 500
        axes[-1].xaxis.set_major_formatter(
            FuncFormatter(lambda ms, pos: f"{(ms - centre_ms) * 1e6:.0f}")
        )
        axes[-1].set_xlabel(f"Time relative to {centre_ms:.6f} ms (ns)")
    else:
        axes[-1].set_xlabel("Simulation time (ms)")
    axes[0].set_title(title)
    figure.savefig(folder / output_file, dpi=180)
    if SHOW_PLOTS:
        plt.show()
    plt.close(figure)


# ==========================================
# 5. FULL, SAMPLE-LEVEL, AND CLOCK-LEVEL VIEWS
# ==========================================

plot_waveform(
    0, recording_duration,
    "NeuroDiff — Complete VCD recording",
    "neurodiff_full.png",
)

plot_waveform(
    max(0, zoom_start), min(zoom_end, recording_duration),
    "NeuroDiff — Zoom (2 to 4 ms)",
    "neurodiff_zoom.png",
)

if len(spike_times):
    centre = spike_times[0]
    margin = edge_zoom_half_width_ns * 1e-9
    plot_waveform(
        max(0, centre - margin), min(recording_duration, centre + margin),
        "NeuroDiff — Clock-edge view around the first filtered spike",
        "neurodiff_edge_zoom.png",
    )

print("Plots saved next to project.vcd.")
