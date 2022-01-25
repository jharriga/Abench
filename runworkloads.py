#
# Execute selected AutoBench2.0 workloads
# Reports key-metric values in benchmark-wrapper JSON format
# Tested with python 3.6.8

import os
import subprocess
import sys
import datetime
import distro
import re
import json
import io

################### 
# BEGIN:     >> USER EDITS
# Path to autobench2.0 executables - must be pre-built
workload_dir = "multibench_automotive_2.0.2653/builds/linux64/gcc64/bin"
# Specify workload names and number of iterations
workloads_list = [
    ("matrix-tblook-4M.exe", 50),
    ("rspeed-idctrn-canrdr-4M.exe", 50),
    ("ttsprk-a2time-pntrch-4M.exe", 5),
    ("ttsprk-a2time-pntrch-idctrn-4M.exe", 5)
    ]
num_ctx = "4"
num_samples = 3
# END:     << USER EDITS
#
##########################
# DICTIONARY STRUCTURE
#
# testrun_dict = {
#    ' date': curtime,
#     'test_config': {
#         testcfg_dict{}
#     } 
#     'test_results': {
#         '{run_num}':
#             run_dict{}
#         '{run_num}':
#             run_dict{}
#     }
#     'system_config': {
#         syscfg_dict{}
#     } 
# }
#

####################
# FUNCTIONS
def write_json(thedict):
    to_unicode = str
   # Write JSON file
    with io.open('workloads.json', 'w', encoding='utf8') as outfile:
        str_ = json.dumps(thedict,
                          indent=4, sort_keys=False,
                          separators=(',', ': '), ensure_ascii=False)
        outfile.write(to_unicode(str_))
        outfile.write(to_unicode("\n"))

    print("Wrote file: workloads.json")

def build_list(metrics_list):
    the_list = []              # new empty list

    # Build key-metric labels list, using km_list (trim)
    for label in metrics_list:
        no_semicolon = label.lstrip(':')
        no_equalsemi = no_semicolon.rstrip('=')
        the_list.append(no_equalsemi)

    return the_list

def init_dict(name, num1, num2):
    # Initialize new dict{} for the test config for this workload
    the_dict = {}             # new empty dict

    the_dict["workload"] = f"{name}"
    the_dict["num_ctx"] = f"{num1}"
    the_dict["num_iters"] = f"{num2}"

    return the_dict

def parse_lscpu(cmd_out, the_dict):
    # cpu model
    for line in cmd_out.split("\n"):
        if "Model name:" in line:
            model = re.search('Model name.*:(.*)', cmd_out).group(1)
    the_dict['model'] = verify_trim(model)

    # number of cores
    for line in cmd_out.split("\n"):
        if "CPU(s):" in line:
            numcores = re.search('CPU\(s\):(.*)', cmd_out).group(1)
    the_dict['numcores'] = verify_trim(numcores)

    # CPU max MHz
    for line in cmd_out.split("\n"):
        if "CPU max MHz:" in line:
            maxmhz = re.search('CPU max MHz:(.*)', cmd_out).group(1)
    the_dict['maxmhz'] = verify_trim(maxmhz)

    return the_dict

def verify_trim(value):
    # Check for value
    if not value:
        ret_val = str("")
    else:
        ret_val = str(value.strip())

    return ret_val

####################
def main():
    # Dictionaries
    wload_dict = {}          # complete run results (per workload)
    testcfg_dict = {}        # test configuration
    syscfg_dict = {}         # test configuration
    data_dict = {}           # test data/results (nested)

    # Vars
    km_list = [":time(secs)=", ":secs/workload=", ":workloads/sec="]
    to_unicode = str

    # Add current date timestamp to dict{}
    curtime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    wload_dict['curtime'] = str(curtime.strip())

    ##########################
    # Get 'system_config' values
    #
    # kernel version
    kversion_out = subprocess.run(['uname', '-r'], stdout=subprocess.PIPE)
    syscfg_dict['kernel'] =\
        str(verify_trim(kversion_out.stdout.decode('utf-8')))

    # Linux Distro
    syscfg_dict['distro'] = str(verify_trim(distro.name(pretty=True)))

    # cpu test config values
    lscpu_out = subprocess.run(['lscpu'], stdout=subprocess.PIPE)
    lscpu_out = lscpu_out.stdout.decode('utf-8')
    # Parse results from 'lscpu' command
    syscfg_dict = parse_lscpu(lscpu_out, syscfg_dict)

    ##########################
    # List of key-metric search strings
    kmlabels_list = build_list(km_list)

    # Execute the workloads  <-- each wload in separate TESTRUN_DICT ?
    for cnt, (wload, num_iters) in enumerate(workloads_list):
        cmdline = [f"./{wload}", "-v0", f"-c{num_ctx}", f"-i{num_iters}"]
        print(f"\nCMD: {cmdline}")

        # Initialize testcfg dict{} for this workload
        testcfg_dict = init_dict(wload, num_ctx, num_iters)
        wload_dict["test_config"] = testcfg_dict

        run_num = 1
        while run_num <= num_samples:
            cmd_out = subprocess.run(
                cmdline, cwd=workload_dir,
                universal_newlines=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT) 

            # Test/verify for clean run
            if cmd_out.check_returncode():
                print(f"{cmdline} FAILED to run")
                print(cmd_out.stdout)
                sys.exit(1)

            cmdout_lines = cmd_out.stdout.splitlines()

            # Initialize new dict_run for each run
            run_dict = {}          # per RUN key-metric values
            run_dict["RUN"] = f"{run_num}"
            # Find key-metrics and add to run_dict{}
            for line in (cmdout_lines):
                for key_metric in km_list:
                    if key_metric in line:
                        split1 = line.split(':')
                        split2 = split1[1].split('=')
                        # key = split2[0], value = split2[1]
                        key = split2[0].strip()
                        value = split2[1].strip()
                        run_dict[key] = float(value) 

            # Test for empty 'run_dict'
            # Append these run results to data_dict{}
            data_dict[f"{run_num}"] = run_dict 
            run_num += 1         # incr run number counter

        ######################
        # All RUNs for this workload completed
        # Insert all workload run results into 'test_results' section
        wload_dict["test_results"] = data_dict

        # Insert syscfg_dict{} into wload_dict{}
        wload_dict["system_config"] = syscfg_dict
        
        print(f"> wload_dict: {wload_dict}\n")    # DEBUG
        write_json(wload_dict)                    # DEBUG
        break                                     # DEBUG


##    # Insert data_dict{} into testrun_dict (final dictionary)
##    testrun_dict["test_results"] = data_dict
##
##    # Insert syscfg_dict{} into testrun_dict{}
##    testrun_dict["system_config"] = syscfg_dict

##    print(f"> testrun_dict: {testrun_dict}")

if __name__ == "__main__":
    main()
