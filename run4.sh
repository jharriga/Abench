#!/bin/bash

abench_bin="multibench_automotive_2.0.2653/builds/linux64/gcc64/bin"
# array of workloads
declare -a workloads=('matrix-tblook-4M.exe'
           'rspeed-idctrn-canrdr-4M.exe'
           'ttsprk-a2time-pntrch-4M.exe'
           'ttsprk-a2time-pntrch-idctrn-4M.exe')
# array of iterations, paired per workload
declare -a iters=(2000
                  2000
                  100
                  100)
# array of contents: first run with one context, then with four
declare -a contexts=(1 4)
##declare -a contexts=(4)                # DEBUG

# Move to req'd dir to execute workloads
cur_dir=$PWD
cd ${abench_bin}

# Execute the workloads
# First with one context and then with multple contexts
wload_cntr=0
for wload in "${workloads[@]}"; do
    for num_ctx in "${contexts[@]}"; do
        cur_iters="iters[wload_cntr]"
        num_iters=${!cur_iters}
        echo "> $wload : $num_ctx : $num_iters"
        ./"$wload" -v0 -c"$num_ctx" -i"$num_iters" > FILE.out
        grep -E "time\(secs\)" FILE.out
        grep "workloads\/sec" FILE.out
        rm -rf FILE.out
    done
    let "wload_cntr+=1"; echo     # insert newline w/new workload
done

# Return to original dir
cd $cur_dir
