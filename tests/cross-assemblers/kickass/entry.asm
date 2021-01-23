	// Define two segments
        .segmentdef InitSegment [start=$2000]

        *= $0801 "Basic Upstart"
        BasicUpstart(start)    // 10 sys$0810

        *= $0810 "Program"
start:  inc $d020
        inc $d021
        jmp $2000

#import "init.asm"
