
/*
 * Copyright (c) 2026 Ryan John Sabra
 * SPDX-License-Identifier: Apache-2.0
 *
 * Basic Neural Spike Detector
 */

`default_nettype none

// Tiny Tapeout top-level module
// gives 24 data I/O pins and 3 control signals 
module tt_um_rs2387_neural_spiking_detection (
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
    wire spike;

    // create an instance of the neural spike detector module
    spike_detector detector (
        .sample(ui_in),
        .spike(spike)
    );

    // bit 0 = spike event, bits 7:1 = unused, sets all to 0 
    assign uo_out = {7'b0000000, spike};

    // unused bidirectional pins, sets all to 0
    assign uio_out = 8'b00000000;
    assign uio_oe  = 8'b00000000;

    // prevents warnings for unused inputs
    wire _unused = &{uio_in, ena, clk, rst_n, 1'b0};

endmodule


`default_nettype wire
