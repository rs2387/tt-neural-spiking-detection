
 // make sure to raise an error for any undeclared wires
`default_nettype none

module exponential_moving_average(
    input wire clk,
    input wire rst_n,
    input wire ena,
    input wire signed [14:0] sample,
    input wire sample_valid,
    output wire signed [14:0] ema,
    output wire ema_valid
   
);

    reg signed [18:0] ema_accumulator;
    reg initialised;

    wire signed [18:0] sample_extended = {{4{sample[14]}}, sample};

    always @(posedge clk)begin
        if(!rst_n)begin
            ema_accumulator <= 19'd0;
            initialised <= 1'b0;
        end else if (ena && sample_valid) begin
            if (!initialised)begin
                ema_accumulator <= {sample, 4'b0000};
                initialised <= 1'b1;
           
            end else begin
                // EMA_new = EMA - (EMA / 16) + (sample / 16)
                ema_accumulator <= ema_accumulator - (ema_accumulator >>> 4) + sample_extended;
            end
        end
    end

    assign ema = ema_accumulator[18:4];

    assign ema_valid = initialised;
endmodule

// revert back to default
`default_nettype wire
