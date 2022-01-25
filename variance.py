#
# Execute selected AutoBench2.0 workloads
# Reports key-metric values and calculates "Pass/Fail"
# Tested with python 3.6.8

import os
import subprocess
import sys
import statistics

# VARS
# list of key-metric search strings
km_list = [":time(secs)=", ":workloads/sec="]
##kmlabels_list = ["time(secs)", "workloads/sec"]  # build this automatically
# Specify workload names and number of iterations
workloads_list = [
    ("matrix-tblook-4M.exe", 500),
    ("rspeed-idctrn-canrdr-4M.exe", 500),
    ("ttsprk-a2time-pntrch-4M.exe", 5),
    ("ttsprk-a2time-pntrch-idctrn-4M.exe", 5)
    ]
num_ctx = "4"
num_samples = 10
max_variance = 10.0           # max allowable variance for {status} = PASS
workload_dir = "multibench_automotive_2.0.2653/builds/linux64/gcc64/bin"

# Build key-metric labels list, using km_list (trim)
kmlabels_list = []              # new empty list
for label in km_list:
    no_semicolon = label.lstrip(':')
    no_equalsemi = no_semicolon.rstrip('=')
    kmlabels_list.append(no_equalsemi)

##print(kmlabels_list)       # DEBUG

# Execute the workloads
for cnt, (wload, num_iters) in enumerate(workloads_list):
    cmdline = [f"./{wload}", "-v0", f"-c{num_ctx}", f"-i{num_iters}"]
    print(f"\nCMD: {cmdline}")
    # initialize new dict_wload for this workload
    dict_wload = {}           # per workload key:values
    dict_wload["WORKLOAD"] = f"{wload}"
    dict_wload["num_ctx"] = f"{num_ctx}"
    dict_wload["num_iters"] = f"{num_iters}"
    run_num = 1
    while run_num <= num_samples:
        cmd_out = subprocess.run(
            cmdline, cwd=workload_dir,
            universal_newlines=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT) 

        # test for clean run

        cmdout_lines = cmd_out.stdout.splitlines()
        # initialize new dict_run for this run
        dict_run = {}             # per RUN key-metric values
        dict_run["SAMPLE"] = f"{run_num}"
        # Find key-metrics and add to dict_run{}
        for line in (cmdout_lines):
            for key_metric in km_list:
                if key_metric in line:
                    split1 = line.split(':')
                    split2 = split1[1].split('=')
                    # key = split2[0], value = split2[1]
                    key = split2[0].strip()
                    value = split2[1].strip()
                    dict_run[key] = value    # limit to two decimal places?

        # test for empty 'dict_run', if so skip 'calc stats'
        dict_wload[f"{run_num}"] = dict_run 
        run_num+=1                     # incr run number counter

    # All RUNs for this workload completed
##    print(f"> dict_wload: {dict_wload}")

    # Calc and print statistics for this key metric - mean and stdev
    for kmlabel in kmlabels_list:
        # Extract values from dict and append to values_list
        values_list = []               # start with empty list
        sample_num = 1
        while sample_num <= num_samples:
            for key in dict_wload[str(sample_num)]:
                if (key == kmlabel):
                    values_list.append(float(dict_wload[str(sample_num)][key]))
            sample_num+=1                # incr counter
        # Simple stats
        min_value = min(values_list)
        max_value = max(values_list)
        average = ( sum(values_list) / len(values_list) )
        percent_diff = ( ((max_value - min_value) * 100) / min_value )
        if percent_diff >= max_variance:
            status = "FAIL"
        else:
            status = "PASS"

        # More elaborate
        mean = statistics.mean(values_list) 
        std_dev = statistics.stdev(values_list) 
        rsd = ((std_dev / mean) * 100)

        # Report out
        print(f"> key-metric: {kmlabel}"\
            f"  Number of samples: ",\
            len(values_list),\
            f"Status: {status}")
        print(f">> min_value: {min_value:.2f}"\
            f"  max_value: {max_value:.2f}"\
            f"  average: {average:.2f}"\
            f"  %DIFF: {percent_diff:.1f}%")
##        print(f">>\tmean: {mean:.2f}"\
##            f"\tstddev: {std_dev:.2f}"\
##            f"\tRSD: {rsd:.1f}%")
 

##    if result.check_returncode():                # test for clean run
##        print("stdout:", result.stdout)
##    else:
##        print(f"{cmdline} FAILED to run")
