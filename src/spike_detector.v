// make sure to raise an error for any undeclared wires
`default_nettype none


// makes a module to detect spikes in neural signal input

module spike_detector (
    input  wire [7:0] sample, // input sequence of 8 bit unsigned numbers 0-255 
    output wire spike         // output of 1 bit event spike 1 or 0
);

// spike is whether our sample exceeds our thresold |x-128| > T which is 30
assign spike = (sample < 98) || (sample > 158);

endmodule

// revert back to default 
`default_nettype wire
