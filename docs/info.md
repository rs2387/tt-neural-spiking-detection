## How it works

Takes digital input neural samples and applies an EMA threshold detection, if the magnitude is above the threshold it outputs 1. Then applies a rising edge filter onto the raw_spike output to only output a 1 at each independent neural spike, so only an event signal is sent rather than a continuous high. Can be used in neural closed loop feedback systems requiring ultra high latency, such as epileptic seizure feedback, or instant movement response. Achieves <50ns response after input sample on rising edge.

## How to test

Use python files to visualize data and generate "neural_samples.txt". Then upload "neural_samples.txt" file into "tb" folder and run to see how your system reacts to certain input waveforms. You can also use "vcd_plotter.py" to plot your vcd waveform in python and visualize with input reference data.

## External hardware

Will connect to an ADC take in digital continuous streams of data and then connect to a bigger processor/ feedback loop. The input streams can be up to a 15bit signed integer, and must have a one bit sample valid bit sending a high pulse every time a new sample is sent (at least 100ns pulse). The output is a high pulse for 25ns, representing a new independent spike event.
