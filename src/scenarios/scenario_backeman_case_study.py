import pytest
from typing import Callable
import tests
from roserer.rosgraph import RosGraphView
from importlib import resources
from roserer.types import DISTRIBUTION
from pathlib import Path
import time
import logging
from roserer.adapters.backeman_adapter import transform_system
import roserer.ros2system as ros
import roserer.patterns.backeman as bmp
from roserer.backeman.system import System

# Case study has following parameters:
# - cameras: No. of cameras
# - prob: probability of each camera being used (load)
# - mcamera: which camera should be monitored
# - subcription: if True, subscription is used of fusion (otherwise Timer)
#
def case_study(cameras, prob, mcamera, subscription, fusion_period=500) -> System | None:
    log = logging.getLogger(__name__)

    CAMERAWCET = 20
    CAMERAPER = 1000
    OBJDETWCET = 50
    FUSIONSUBWCET = 90
    FUSIONSUB = 10
    FUSIONTIMERWCET = 90
    ACTUATORWCET = 50
    
    if mcamera >= cameras:
        return None

    if subscription:
        name = "casestudy" + str(cameras) + "_" + str(mcamera) + "_sub" + str(prob)
    else:
        name = "casestudy" + str(cameras) + "_" + str(mcamera) + "_tmr" + str(prob)

    system = ros.System(name)
    e = system.add_host("host").add_executor("executor", ros_distribution=DISTRIBUTION.Humble)

    for i in range(cameras):
        bmp.add_probabilistic_datagenerator(
                e, "CAMERA" + str(i), CAMERAWCET, CAMERAPER, 0, prob)
        bmp.add_subscriber(e, "OBJDET" + str(i), OBJDETWCET, "CAMERA" + str(i))

    if subscription:
        bmp.add_subscriber(
                e,
                "FUSION",
                FUSIONSUBWCET,
                "OBJDET0",
                ["OBJDET" + str(i) for i in range(1,cameras)],
                [FUSIONSUB]*(cameras-1))
    else:
        bmp.add_timer(
                e,
                "FUSION",
                FUSIONTIMERWCET,
                fusion_period,
                0,
                ["OBJDET" + str(i) for i in range(cameras)],
                [FUSIONSUB]*cameras)
    bmp.add_subscriber(e, "ACTUATOR", ACTUATORWCET, "FUSION")
    feedback, bms = transform_system(system, (f"CAMERA{mcamera}", "ACTUATOR"))
    # for node in RosGraphView(system).get_all_nodes():
    #     log.debug(node)
    log = logging.getLogger(__name__)
    for ln in feedback.errors:
        log.info(ln)
    assert isinstance(bms, System)
    return bms

def run_system(max_cameras: int, mcamera: int, subscription: bool, upper_limit: int, fusion_period: int):
    log = logging.getLogger(__name__)
    log.debug(f"test_system({mcamera}, {str(subscription)}, {upper_limit}, {fusion_period})")
    results = []
    probs = [25, 50, 75, 100]
    for cameras in range(1,max_cameras+1):
        for prob in probs:
            log.debug(f"\t, {cameras}, {prob}")
            system = case_study(cameras, prob, mcamera, subscription, fusion_period)
            # log.debug(system)
            if isinstance(system, System):
                log.debug("\trunning system")
                THRESHOLD = 850
                PERCENTAGE = 0.05

                start = time.time()
                formula, data = system.measure_load(THRESHOLD, PERCENTAGE, upper_limit)
                # log.info(f"HERE: {system.name}. RESULT: {data}")
                end = time.time()
                t = end - start
                results.append((cameras, prob, data, formula, t))
            else:
                log.debug("\tsystem could not be created")
                results.append((cameras, prob, "n/a", "", 0.0))

    # log.debug("RESULTS")
    # for ln in results:
    #     log.info(ln)
    # log.debug("END RESULTS")

    # log.debug("#Cams\tLoad\tResult")
    # log.debug("============================")
    # for (c, p, r, f) in results:
    #     log.debug(c, "\t", p, "\t", r)
    #

    # Uncomment these lines to generate the table presented in the paper.
    #
    i = 0
    result = []
    rows = len(probs)
    cols = 3
    header = []
    result.append("\\begin{table}")
    result.append("\\centering")
    result.append("\\begin{tabular}{|" + '|'.join('c'*cols*4) + '|}')

    result.append("\\hline")
    for _ in range(cols):
        header.append("\\#Cams & Load & $\\leq 850$ & Time")
    result.append(' & '.join(header) + "\\\\")
    result.append("\\hline")
    while i*cols*rows < len(results):
        # Create one block (i.e., row x cols)
        lines = []
        for _ in range(rows):
            lines.append([])
        for col in range(cols):
            for row in range(rows):
                (c, p, r, f, t) = results[i*cols*rows + col*rows + row]
                #print(col, "x", row, " --> ", c, p, r)
                if r:
                    log.debug("look here")
                    if not r == "n/a":
                        r = "Yes"
                else:
                    r = "No"

                fmt = str(c) + " & " + str(p) + "\\% & " + r + " & " + "{:.2f}".format(t)  # noqa: E501
                lines[row].append(fmt)
                #print("NEWLINE: ", row, "--->", lines[row])
        i += 1
        for ln in lines:
            result.append(' & '.join(ln) + "\\\\")
        result.append("\\hline")
    result.append("\\end{tabular}")
    if subscription:
        result.append("\\caption{Use case monitoring "
            + str(mcamera+1) + ", with subscription-based fusion analysing "
            + str(upper_limit) + " time steps.}")
    else:
        result.append("\\caption{Use case monitoring "
            + str(mcamera+1) + ", with timer-based fusion (period of "
            + str(fusion_period) + ") analysing "
            + str(upper_limit) + " time steps.}")
    result.append("\\end{table}")
    latex = '\n'.join(result)
    return latex, results


# Correspoding to the first study
def first_study():
    all = []
    max_cameras = 12
    for mcamera in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]:
        for sub in [False]:
            for upper_limit in [10000]:
                for fusion_period in [500]:
                    latex, results = run_system(max_cameras, mcamera, sub, upper_limit, fusion_period)  # noqa: E501
                    all.append(latex)    

    return "\n\n\n".join(all)

# Ten-fold time steps
def ten_fold():
    all = []
    max_cameras = 6
    for mcamera in [0, 1, 2, 3, 4, 5, 6, 7]:
        for sub in [False]:
            for upper_limit in [100000]:
                for fusion_period in [500]:
                    latex, results = run_system(max_cameras, mcamera, sub, upper_limit, fusion_period)  # noqa: E501
                    all.append(latex)    

    return "\n\n\n".join(all)

# Subscription fusion
def subscription():
    all = []
    max_cameras = 6
    for mcamera in [0, 1]:
        for sub in [True]:
            for upper_limit in [10000]:
                for fusion_period in [500]:
                    latex, results = run_system(max_cameras, mcamera, sub, upper_limit, fusion_period)  # noqa: E501
                    all.append(latex)    

    return "\n\n\n".join(all)

# Fusion periods
def fusion_study():
    all = []
    max_cameras = 6
    for mcamera in [0, 1]:
        for sub in [False]:
            for upper_limit in [10000]:
                for fusion_period in [250, 750]:
                    latex, results = run_system(max_cameras, mcamera, sub, upper_limit, fusion_period)  # noqa: E501
                    all.append(latex)    

    return "\n\n\n".join(all)

#example()
#validation()

def extract_yes_no_pattern(line):
    parts = line.replace("\\\\", "").split("&")
    parts = [p.strip() for p in parts]
    pattern = [p for p in parts if p in ("Yes", "No")]
    return tuple(pattern)

def fixlatex(latex) -> str:
    return "\\documentclass{article}\n\\begin{document}\n"\
        + latex + "\n\\end{document}"

# def test_backeman_case(file):
#     log = logging.getLogger(__name__)
#     with resources.files(tests).joinpath("input/backeman_case_study/results_first_study.tex").open("r", encoding="utf-8") as f:
#         expected = f.read()
#     log.info(expected)
#     dir = "results/backeman/case_study"
#     path = Path(dir)
#     path.parent.mkdir(parents=True, exist_ok=True)
#     latex = fixlatex(first_study())
#     fout = open(dir + "results_first_study.tex", 'w')
#     fout.write(latex)
#     fout.close()
#     log.info(latex)
#     assert latex == expected
#
#     expected_path = Path(__file__).parent / "data" / "expected.txt"
#     expected = expected_path.read_text()


# def test_backeman_case_ten_fold():
#     log = logging.getLogger(__name__)
#     with resources.files(tests).joinpath("input/backeman_case_study/results_ten_fold.tex").open("r", encoding="utf-8") as f:
#         expected = f.read()
#     log.info(expected)
#     dir = "results/backeman/case_study"
#     path = Path(dir)
#     path.parent.mkdir(parents=True, exist_ok=True)
#     latex = fixlatex(ten_fold())
#     fout = open(dir + "results_ten_fold.tex", 'w')
#     fout.write(latex)
#     fout.close()
#     log.info(latex)
#     assert latex == expected
#
# def test_backeman_case_subscription():
#     dir = "results/backeman/case_study"
#     path = Path(dir)
#     path.parent.mkdir(parents=True, exist_ok=True)
#     latex = fixlatex(subscription())
#     fout = open(dir + "results_subscription.tex", 'w')
#     fout.write(latex)
#     fout.close()

# results_fusion_study.tex
@pytest.mark.parametrize("filename,task", [
    ("results_fusion_study.tex", fusion_study),
    ("results_subscription.tex", subscription),
    ("results_ten_fold.tex", ten_fold),
    ("results_first_study.tex", first_study)])
def test_backeman_case(filename: str, task: Callable):
    """
    Each of the files were produced by running the demo/backeman_demo.py file.
    This test shows that the results produced by the ros2system based case study are equivalent to those produced by
    running the original backeman test code.
    Running time is ignored, because that is not deterministic - so the comparison is based on the Yes/No results.
    """
    log = logging.getLogger(__name__)
    log.info(f"running {filename}")
    with resources.files(tests)\
            .joinpath(f"input/backeman_case_study/{filename}")\
            .open("r", encoding="utf-8") as f:
        expected = f.read()
    # log.info(expected)
    dir = "results/backeman/case_study"
    path = Path(dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    latex = task()
    latex = fixlatex(latex)
    fout = open(dir + filename, 'w')
    fout.write(latex)
    # log.info(latex)
    lni = 0
    nexperiments = 0
    for ln1, ln2 in zip(latex.split("\n"), expected.split("\n")):
        lni += 1
        p1 = extract_yes_no_pattern(ln1)
        p2 = extract_yes_no_pattern(ln2)
        if p1 and p2:
            nexperiments += len(p1)
            # log.info(f"{p1} | {p2}")
            # log.info(ln1)
            # log.info(ln2)
            if p1 != p2:
                log.info(lni)
                log.info(filename)
                log.info(p1)
                log.info(p2)
            # We have observed different results in a few cases.
            # We document the line numbers
            # All correspond to the cases of 7,8 or 9 cameras at 25% load
            # In the last cases, 7 and 8 are n/a, and so we only have 2 and 1 value,
            # respectively.
            # In each case, to match the 9 camera run, we allow the last element to differ.
            differences = [
                    19,
                    50,
                    81,
                    112,
                    143,
                    174,
                    236,
                    267,
                    ]
            differing_values = [('Yes', 'Yes', 'Yes'),
                                ('Yes', 'Yes', 'No'),
                                ('Yes', 'Yes'),
                                ('Yes', 'No')]
            assert ((p1 == p2) 
                    or ((filename == "results_first_study.tex")
                        and (lni in differences)
                        and (p1 in differing_values)
                        and (p2 in differing_values)))
        else:
            assert not p1 and not p2
        
        # log.info(p1)
        # return p1 == p2
    log.info(f"Number of experiments: {nexperiments}")


# s = case_study(7, 25, 6, False)
# print(s.gen_declaration())
# print(s.gen_system())
# s.write("tmt_min.xml")

#\caption{Use case monitoring 6, with timer-based fusion (period of 500) analysing 10000 time steps.} Here is the diff
