`timescale 1ns / 1ps

module tt_um_rs2387_project_tb;

    reg [7:0] ui_in;
    reg [7:0] uio_in;

    wire [7:0] uo_out;
    wire [7:0] uio_out;
    wire [7:0] uio_oe;

    reg ena;
    reg rst_n;
    reg clk = 0; // initialises as 0 instead of x unknown

    integer input_file;
    integer result;
    integer sample_value;
    integer valid_value;
    integer sample_count;
    integer spike_count;

    // 40 MHz clock
    always #12.5 clk = ~clk;


    // Number of clock cycles between samples
    // 10 kHz = 4000, 20 kHz = 2000, 40 kHz = 1000
    integer clock_cycles_per_sample = 4000;

    // 15-bit signal for easier waveform viewing
    wire signed [14:0] sample = {uio_in[6:0], ui_in};

    // sample valid bit at pin 15 now
    wire sample_valid = uio_in[7];

    // raw spike for easier waveform viewing
    wire raw_spike = dut.raw_spike;

    // final spike for easier waveform viewing
    wire filtered_spike = uo_out[0];

    // spike flag for easier waveform viewing
    wire spike = filtered_spike;

    // Tiny Tapeout hardware
    tt_um_rs2387_project dut (
        .ui_in(ui_in),
        .uo_out(uo_out),
        .uio_in(uio_in),
        .uio_out(uio_out),
        .uio_oe(uio_oe),
        .ena(ena),
        .clk(clk),
        .rst_n(rst_n)
    );

    initial begin

        // records waveform for Vulkos
        $dumpfile("project.vcd");
        $dumpvars(0, tt_um_rs2387_project_tb);

        ena = 1'b1;
        rst_n = 1'b0;

        ui_in = 8'b0;
        uio_in = 8'b0;

        sample_count = 0;
        spike_count = 0;

        // read neural recording
        input_file = $fopen("tb/neural_samples.txt", "r");

        if (input_file == 0) begin
            $fatal(1, "Cannot open neural_samples.txt");
        end

        $display("Neural recording opened successfully.");

        // reset the detector
        repeat (2) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;

        // process every sample in txt
        while (!$feof(input_file)) begin

            result = $fscanf(
                input_file,
                "%d %d\n",
                sample_value,
                valid_value
            );

            if (result == 2) begin

                // Upload the sample ON the rising edge. Non-blocking (<=)
                // schedules the update for the end of this time step, so it
                // lands exactly on the edge while the DUT flops -- which read
                // their inputs first -- still see the previous sample.
                @(posedge clk);
                #1;
                ui_in  <= sample_value[7:0];
                uio_in <= {valid_value[0], sample_value[14:8]};

                // raw_spike is combinational off the new sample, and
                // filtered_spike compares it against the still-old
                // previous_raw_spike; #1 is just the read point, not a drive
                #1;
                if (filtered_spike)
                    spike_count = spike_count + 1;

                sample_count = sample_count + 1;

                // Next rising edge: EMA loads the sample and
                // previous_raw_spike catches up; deassert valid on that edge
                @(posedge clk);
                uio_in[7] <= 1'b0;

                // Wait for next neural sample
                repeat (clock_cycles_per_sample - 2)
                    @(posedge clk);

            end
        end

        $fclose(input_file);

        $display("Samples processed: %0d", sample_count);
        $display("Spike flags: %0d", spike_count);
        $display("Simulation completed.");

        $finish;
    end

endmodule