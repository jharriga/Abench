#!/bin/bash
# Script to run Autobench 2.0 workloads
# Accepts variables to effect:
#   - number of samples (runs per workload condition)
#   - list of workloads
#   - list of number of iterations, per workload
#   - list of number of contexts, per workload
#   - number of samples, for all workloads
#
# Prints text results, per workload condition
#   - runtime (in seconds)
#   - throughput (iterations / sec)
#--------------

num_samples=3           # how many times to run each workload condition
# dir where autobench execs live - must be pre-built
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
        echo          # insert newline per workload condition
        cur_iters="iters[wload_cntr]"
	num_iters=${!cur_iters}
        echo "> $wload : CTX=$num_ctx : ITERS=$num_iters : SAMPLES=$num_samples"
	for (( i=1; i <= num_samples; i++ )); do
            ./"$wload" -v0 -c"$num_ctx" -i"$num_iters" > FILE.out
	    echo -n "  SAMPLE $i: time(secs)= "
            grep -E "time\(secs\)" FILE.out | awk -F '=' '{printf "%.2f",$2}'
	    echo -n " : workloads/sec= "
            grep "workloads\/sec" FILE.out | awk -F '=' '{printf "%.2f\n",$2}'
	    rm -rf FILE.out
        done
    done
    let "wload_cntr+=1"; echo     # insert newline w/new workload
done

# Return to original dir
cd $cur_dir
