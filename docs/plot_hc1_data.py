
from pathlib import Path
import xml.etree.ElementTree as xml_tree

import numpy as numpy
import matplotlib.pyplot as pyplot


# ==========================================
# SETTINGS
# ==========================================

data_folder = Path(__file__).resolve().parent / "d5331"
recording_name = "d533101"

extracellular_channels = [2, 3, 4, 5]
intracellular_channel = 6


# ==========================================
# LOAD RECORDING
# ==========================================

def load_recording():

    # Read recording information
    metadata_file = data_folder / f"{recording_name}.xml"
    recording_file = data_folder / f"{recording_name}.dat"

    metadata = xml_tree.parse(metadata_file).getroot()
    acquisition = metadata.find("acquisitionSystem")

    channel_count = int(acquisition.findtext("nChannels"))
    sampling_rate = float(acquisition.findtext("samplingRate"))

    # Read signed 16-bit samples
    recording = numpy.memmap(
        recording_file,
        dtype="<i2",
        mode="r"
    )

    # Separate the interleaved channels
    recording = recording.reshape(-1, channel_count)

    print(f"Recording: {recording_name}")
    print(f"Channels: {channel_count}")
    print(f"Sampling rate: {sampling_rate:,.0f} Hz")
    print(f"Duration: {len(recording) / sampling_rate:.2f} seconds")

    return recording, sampling_rate


recording, sampling_rate = load_recording()


# ==========================================
# GET CHANNEL DATA
# ==========================================

def get_channel(channel, start_time=0, duration=1):

    first_sample = int(start_time * sampling_rate)
    last_sample = int(
        (start_time + duration) * sampling_rate
    )

    # Channel 1 is column 0
    signal = recording[
        first_sample:last_sample,
        channel - 1
    ]

    time = numpy.arange(
        first_sample,
        first_sample + len(signal)
    ) / sampling_rate

    return time, signal

# ==========================================
# EXPORT CHANNEL DATA TO CSV
# ==========================================

def export_channel_csv(channel, filename):

    output_file = data_folder / filename

    # Process in chunks to support large recordings
    chunk_size = 100_000

    with open(output_file, "w", encoding="utf-8") as file:

        file.write("adc_count\n")

        for start in range(0, len(recording), chunk_size):

            signal = recording[
                start:start + chunk_size,
                channel - 1
            ]

            numpy.savetxt(
                file,
                signal,
                fmt="%d",
                delimiter=","
            )

    print(f"Saved channel {channel}: {output_file}")
# ==========================================
# PLOT ONE CHANNEL
# ==========================================

def plot_channel(channel=2, start_time=0, duration=1):

    time, signal = get_channel(
        channel,
        start_time,
        duration
    )

    pyplot.figure(figsize=(11, 4))

    pyplot.plot(
        time,
        signal,
        linewidth=0.7
    )

    pyplot.title(f"CRCNS — Channel {channel}")
    pyplot.xlabel("Time (seconds)")
    pyplot.ylabel("ADC counts")
    pyplot.grid(alpha=0.3)

    pyplot.tight_layout()
    pyplot.show()


# ==========================================
# PLOT MULTIPLE CHANNELS
# ==========================================

def plot_channels(channels, start_time=0, duration=1):

    figure, axes = pyplot.subplots(
        len(channels),
        1,
        figsize=(11, 2.5 * len(channels)),
        sharex=True
    )

    axes = numpy.atleast_1d(axes)

    for axis, channel in zip(axes, channels):

        time, signal = get_channel(
            channel,
            start_time,
            duration
        )

        axis.plot(
            time,
            signal,
            linewidth=0.7
        )

        axis.set_ylabel(f"Channel {channel}")
        axis.grid(alpha=0.3)

    axes[-1].set_xlabel("Time (seconds)")

    figure.suptitle("CRCNS — Neural Recordings")
    figure.tight_layout()

    pyplot.show()


# ==========================================
# COMPARE EXTRACELLULAR AND INTRACELLULAR
# ==========================================

def plot_extracellular_intracellular(
    extracellular_channel=2,
    start_time=0,
    duration=1
):

    time, extracellular_signal = get_channel(
        extracellular_channel,
        start_time,
        duration
    )

    _, intracellular_signal = get_channel(
        intracellular_channel,
        start_time,
        duration
    )

    figure, axes = pyplot.subplots(
        2,
        1,
        figsize=(11, 6),
        sharex=True
    )

    axes[0].plot(
        time,
        extracellular_signal,
        color="royalblue",
        linewidth=0.7
    )

    axes[0].set_title(
        f"Extracellular — Channel {extracellular_channel}"
    )

    axes[0].set_ylabel("ADC counts")
    axes[0].grid(alpha=0.3)

    axes[1].plot(
        time,
        intracellular_signal,
        color="darkorange",
        linewidth=0.7
    )

    axes[1].set_title(
        f"Intracellular — Channel {intracellular_channel}"
    )

    axes[1].set_ylabel("ADC counts")
    axes[1].set_xlabel("Time (seconds)")
    axes[1].grid(alpha=0.3)

    figure.tight_layout()
    pyplot.show()


# ==========================================
# COMPARE EXTRACELLULAR WITH CHANNEL 1
# ==========================================

def plot_extracellular_channel_one(
    extracellular_channel=2,
    start_time=0,
    duration=1
):

    time, extracellular_signal = get_channel(
        extracellular_channel,
        start_time,
        duration
    )

    _, channel_one_signal = get_channel(
        1,
        start_time,
        duration
    )

    figure, axes = pyplot.subplots(
        2,
        1,
        figsize=(11, 6),
        sharex=True
    )

    axes[0].plot(time, extracellular_signal, color="royalblue", linewidth=0.7)
    axes[0].set_title(f"Extracellular — Channel {extracellular_channel}")
    axes[0].set_ylabel("ADC counts")
    axes[0].grid(alpha=0.3)

    axes[1].plot(time, channel_one_signal, color="darkorange", linewidth=0.7)
    axes[1].set_title("Channel 1")
    axes[1].set_ylabel("ADC counts")
    axes[1].set_xlabel("Time (seconds)")
    axes[1].grid(alpha=0.3)

    figure.tight_layout()
    pyplot.show()




# ==========================================
# CHOOSE WHAT TO PLOT
# ==========================================
if __name__ == "__main__":
    # Plot one extracellular channel
    plot_channel(
        channel=2,
        start_time=1,
        duration=0.5
    )

    # Plot all eight channels
    # plot_channels(
    #     channels=list(range(1, 9)),
    #     start_time=1,
    #     duration=0.5
    # )

    # Plot extracellular channels only
    # plot_channels(
    #     channels=extracellular_channels,
    #     start_time=1,
    #     duration=0.5
    # )

    # Compare extracellular and intracellular
    # plot_extracellular_intracellular(
    #     extracellular_channel=2,
    #     start_time=1,
    #     duration=0.5
    # )

    # Compare extracellular channel with channel 1
    plot_extracellular_channel_one(
        extracellular_channel=2,
        start_time=0,
        duration=2
    )


    #     # Save extracellular channel 2
    # export_channel_csv(
    #     channel=2,
    #     filename="d533101_channel_2_extracellular.csv"
    # )

    # # Save unknown channel 1
    # export_channel_csv(
    #     channel=1,
    #     filename="d533101_channel_1_unknown.csv"
    # )