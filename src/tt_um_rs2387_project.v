
/*
 * Copyright (c) 2026 Ryan John Sabra
 * SPDX-License-Identifier: Apache-2.0
 *
 * Basic Neural Spike Detector
 */

`default_nettype none

// Tiny Tapeout top-level module
// gives 24 data I/O pins and 3 control signals 
module tt_um_rs2387_project (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,  // bi-directional input mode
    output wire [7:0] uio_out, // bi-directional output mode
    output wire [7:0] uio_oe,  // controls whether each bi-directional pin is I/O
    input  wire       ena,     // enable, 1 when design is powered
    input  wire       clk,     // clock
    input  wire       rst_n    // reset, low to reset
);

    // one-bit spike signal
    wire raw_spike;

    // flip flop to store the previous raw spike
    reg previous_raw_spike;

    // combinational: current spike gated by the previous one
    wire filtered_spike;

    // combines 7-bit and 8-bit input buses into one 15-bit sample
    wire signed [14:0] sample = {uio_in[6:0], ui_in};

    // assign input pin 15 to sample_valid
    wire sample_valid = uio_in[7];

    // assign ema to a wire
    wire signed [14:0] ema;

    wire ema_valid;

    // create an instance of the neural spike detector module
    spike_detector detector (
        .sample(sample),
        .raw_spike(raw_spike),
        .ema(ema)
    );

    exponential_moving_average average (
        .sample(sample),
        .clk(clk),
        .ena(ena),
        .rst_n(rst_n),
        .ema(ema),
        .sample_valid(sample_valid),
        .ema_valid(ema_valid)
    );

    // keep a snapshot of raw_spike from the previous cycle
    always @(posedge clk) begin
        if (!rst_n)
            previous_raw_spike <= 1'b0;
        else if (ena && ema_valid)
            previous_raw_spike <= raw_spike;
    end

    // spike event = raw_spike rising 0->1: compared against the previous
    // value, which only updates on the NEXT edge, so the pulse is visible
    // combinationally during this cycle
    assign filtered_spike = raw_spike && !previous_raw_spike && ena && ema_valid;

    // bit 0 = spike event, bits 7:1 = unused, sets all to 0 
    assign uo_out = {7'b0000000, filtered_spike};

    
    // makes bidirectional pins inputs
    assign uio_oe = 8'b00000000;
    assign uio_out = 8'b00000000;


endmodule


`default_nettype wire
