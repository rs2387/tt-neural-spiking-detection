// make sure to raise an error for any undeclared wires
`default_nettype none


// makes a module to detect spikes in neural signal input
module spike_detector (
    input wire signed [14:0] ema, // input /sequence of 8 bit unsigned numbers 0-255
    input wire signed [14:0] sample,
    output wire raw_spike         // output of 1 bit event spike 1 or 0
);


    // same width as abs_diff so this is a clean 15-bit compare
    localparam [14:0] threshold = 15'd150;

    wire [14:0] abs_diff;
    assign abs_diff = (sample > ema) ? (sample - ema) : (ema - sample);
    assign raw_spike = (abs_diff > threshold);

endmodule

// revert back to default
`default_nettype wire
