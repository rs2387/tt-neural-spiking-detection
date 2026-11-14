// make sure to raise an error for any undeclared wires
`default_nettype none


// makes a module to detect spikes in neural signal input

module spike_detector (

    input  wire signed [15:0] sample, // input sequence of 16 bit signed numbers 

    output wire spike         // output of 1 bit event spike 1 or 0
);

// spike is whether our sample exceeds our thresold |x-2000| > T which is 400
assign spike = (sample < 16'sd1600) ||
               (sample > 16'sd2400);

endmodule

// revert back to default 
`default_nettype wire
