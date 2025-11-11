import os
import sys
import time
from absl import app, flags
import subprocess,glob
from utils.SolidityVersionAnalyzer import SolidityVersionAnalyzer

from slither import Slither
from AuditorAgent.Auditor import Auditor
from AttackerAgent.Attacker import Attacker
from InvariantChecker.Invariant import Invariant


FLAGS = flags.FLAGS

flags.DEFINE_string("input", None, "Input Solidity file path")
flags.DEFINE_string("containerid", None, "fuzzing engine container id")
flags.DEFINE_integer("enginetimeout", 300, "Timeout for fuzzing engine(in seconds)")

flags.mark_flag_as_required("input")
flags.mark_flag_as_required("containerid")

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def setup_environment(solc_version="0.8.0"):

    try:
        print(f"set solc {solc_version}...")
        solc_cmd = f"solc-select use {solc_version} --always-install"
        subprocess.run(solc_cmd, shell=True, check=True)
        print("success")
    except subprocess.CalledProcessError as e:
        print(f"Error:cmd - {e}")
    except Exception as e:
        print(f"Error:unkonwn: {e}")


def compile_contract(filepath,Mode):

    if Mode:
        sc_slither = Slither(filepath,solc_args="--via-ir --optimize")
    else:
        sc_slither = Slither(filepath,solc_args="--optimize --optimize-runs 200")


    return sc_slither


def read_solidity_lines(filepath, start_line, end_line):
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        return lines[start_line - 1:end_line]


def get_versioninfo(filepath):
    version_info = SolidityVersionAnalyzer().get_min_version_from_file(filepath)

    compile_mode = False
    if version_info[0] == None:
        print(version_info[1])
        exit()
    else:
        print(version_info[0])
        setup_environment(version_info[0])
        if SolidityVersionAnalyzer()._compare_versions(version_info[0],"0.8.13") != -1:
            compile_mode = True

    return compile_mode


def getpar2son():

    par2son = dict()
    son2par = dict()
    son2par["Wrong Implementation of Amount Lock"] = "Incorrect Control Mechanism"
    son2par["Vote Manipulation"] = "Incorrect Control Mechanism"
    son2par["Improper Handling of Deposit Fee"] = "Incorrect Control Mechanism"
    son2par["Wrong Checkpoint Order"] = "Insecure Calculating Logic"
    son2par["Wrong Interest Rate Order"] = "Insecure Calculating Logic"
    son2par["Risky First Deposit"] = "Insecure Calculating Logic"
    son2par["AMM Price Oracle Manipulation"] = "Price Oracle Manipulation"
    son2par["Non-AMM Price Oracle Manipulation"] = "Price Oracle Manipulation"
    son2par["Unauthorized Transfer"] = "Unauthorized Behavior"
    son2par["Approval Not Clear"] = "Unauthorized Behavior"


    par2son["Incorrect Control Mechanism"] = ["Wrong Implementation of Amount Lock","Vote Manipulation","Improper Handling of Deposit Fee"]
    par2son["Insecure Calculating Logic"] = ["Wrong Checkpoint Order","Wrong Interest Rate Order","Risky First Deposit"]
    par2son["Price Oracle Manipulation"] = ["AMM Price Oracle Manipulation","Non-AMM Price Oracle Manipulation"]
    par2son["Unauthorized Behavior"] = ["Unauthorized Transfer","Approval Not Clear"]

    return par2son,son2par


def fusion(auditor_res,attacker_res):

    par2son, son2par = getpar2son()

    fused_res = list()


    for attacker_item in attacker_res:
        sons = par2son[attacker_item]

        if attacker_item == "Incorrect Control Mechanism" or attacker_item == "Insecure Calculating Logic":
            for son in sons:
                if son in auditor_res:
                    fused_res.append(son)
        elif attacker_item == "Price Oracle Manipulation" or attacker_item == "Unauthorized Behavior":
            for son in sons:
                if son in auditor_res:
                    fused_res.extend(sons)
                    break

    return fused_res


def engine_ver():

    container_id = FLAGS.containerid

    start_cmd = subprocess.Popen(["docker","start",container_id],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    print("start")
    for line in iter(start_cmd.stdout.readline, b''):
        print(line.decode('utf-8').strip())
    start_cmd.wait()

    t0 = time.monotonic()
    ts = FLAGS.enginetimeout
    print(f"timeout set to {ts} seconds")
    detection_cmd = subprocess.Popen(["docker","exec",container_id,\
                                "./cli_offchain","evm","-t",\
                                "/bins/dataset/insertdir/*"],\
                                stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    
    print("detect......")
    running_flag = 1

    for line in iter(detection_cmd.stdout.readline, b''):
        log_info = line.decode('utf-8').strip()

        if running_flag == 1:
            if log_info.find("Found vulnerabilities!")!=-1:
                running_flag = 2
                break
        if time.monotonic() - t0 > ts:
            break
    
    try:
        detection_cmd.wait(timeout=ts)
    except subprocess.TimeoutExpired:
        print("detection timeout")



    stop_cmd = subprocess.Popen(["docker","stop",container_id],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    print("stop")
    for line in iter(stop_cmd.stdout.readline, b''):
        print(line.decode('utf-8').strip())
    stop_cmd.wait()

    

    if running_flag ==2:
        return True
    else:
        return False


def analysis_each_contract(sc_slither):

    analysis_res = list()

    for contract in sc_slither.contracts:
        if contract.is_interface:
            continue
        print(f"Contract: {contract.name}")

        for function in contract.functions:
            if len(function.nodes) == 0:
                continue

            if 'slither' in function.name:
                continue
            print(f"  Function: {function.name}")

            func_lines = function.source_mapping.lines
            func_code = ''.join(read_solidity_lines(FLAGS.input,func_lines[0],func_lines[-1]))

            auditor = Auditor(function.name,func_code)
            auditor_ans = auditor.query()
            attacker = Attacker(function.name,func_code)
            attacker_ans = attacker.query()
            fused_res = fusion(auditor_ans,attacker_ans)


            invariant = Invariant(function.name,FLAGS.input,func_code)


            for pitem in fused_res:
                path_wc = invariant.checker(pitem)
                if path_wc is None:
                    continue
                sol_files = glob.glob("insertdir/*.sol")
                subprocess.run(["solc", "--bin", "--abi", "-o", "insertdir/", "--overwrite", *sol_files],check=True)
                ver_flag = engine_ver()
                if ver_flag:
                    msg = f"[VULNERABILITY FOUND] \"{pitem}\" in \"{contract.name}.{function.name}\""
                    print(msg)
                    analysis_res.append(msg)
                    
    return analysis_res

def analysis(filepath):

    compile_mode = get_versioninfo(filepath)

    sc_slither = compile_contract(filepath,compile_mode)

    analysis_res = analysis_each_contract(sc_slither)

    return analysis_res

def printresults(analysis_res):

    output_path = "./promfuzz_result.txt"

    with open(output_path, "w", encoding="utf-8") as f:

        def writeandprint(text=""):
            print(text)
            f.write(text + "\n")
        writeandprint(FLAGS.input)
        writeandprint("================= Analysis Results =================")
        if len(analysis_res) == 0:
            writeandprint("No vulnerabilities found.")
        else:
            for res in analysis_res:
                writeandprint(str(res))
        writeandprint("====================================================")

    print(f"\nResults saved to {output_path}\n")


def main(argv):
    filepath = FLAGS.input

    if not filepath or not os.path.isfile(filepath):
        print("Please provide a valid Solidity file path using --input flag.")
        return
    
    analysis_res = analysis(filepath)

    printresults(analysis_res)

if __name__ == "__main__":
    app.run(main)
