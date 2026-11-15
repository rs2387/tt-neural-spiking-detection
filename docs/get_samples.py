from pathlib import Path
from plot_hc1_data import get_channel

# ==========================================
# SETTINGS
# ==========================================

channel = 2
total_duration = 10
batch_duration = 0.5

output_folder = Path("neural_samples")
output_folder.mkdir(parents=True, exist_ok=True)

# ==========================================
# EXPORT BATCHES
# ==========================================

total_samples = 0

for batch in range(int(total_duration // batch_duration)):

    start_time = batch * batch_duration

    time, samples = get_channel(
        channel=channel,
        start_time=start_time,
        duration=batch_duration
    )

    filename = output_folder / f"neural_samples_{batch + 1:02d}.txt"

    with open(filename, "w") as file:
        for sample in samples:
            sample = int(sample)

            if sample < -16384 or sample > 16383:
                raise ValueError(
                    f"Sample {sample} exceeds 15-bit signed range"
                )

            file.write(f"{sample} 1\n")

    total_samples += len(samples)

    print(
        f"Batch {batch + 1:02d} | "
        f"{start_time}s - {start_time + batch_duration}s | "
        f"{len(samples)} samples | "
        f"{filename}"
    )

print(f"\nExported {total_samples} neural samples across 10 batches.")