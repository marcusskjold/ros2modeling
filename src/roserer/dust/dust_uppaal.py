# # Copyright (c) 2024 Peter Backeman
# # All rights reserved.
# #
# # This software is provided "as is," without warranty of any kind, express or implied,
# # including but not limited to the warranties of merchantability, fitness for a particular purpose,
# # and noninfringement. In no event shall the authors or copyright holders be liable for any claim,
# # damages, or other liability, whether in an action of contract, tort, or otherwise, arising from,
# # out of, or in connection with the software or the use or other dealings in the software.

# ## Provides functions to perform various UPPAAL tasks.

import subprocess
import roserer.verifyta_resolver

# Class containing static functions for interacting with UPPAAL
class UPPAAL():
    def run_uppaal(
        modelfile: str, 
        queryfile: str,
        extra_args: list[str] | None = None
    ) -> str:
        if extra_args is None:
            extra_args = []
        try:
            output = subprocess.check_output(
                [roserer.verifyta_resolver.find_verifyta()] + extra_args + [modelfile, queryfile], text=True)
            return output
        except Exception:
            # We assume that any error is due to overflow in scheduling queue.
            print("Exception!")
            10/0
            return "Overflow"

    # query 2) from paper
    def buffer_overflow(modelfile : str, checkables : list[str]) -> dict:
        queryfile = modelfile + '.q'
        UPPAAL.write_buffer_overflow_query(queryfile, checkables)
        output = UPPAAL.run_uppaal(modelfile, queryfile)
        return UPPAAL.parse_buffer_overflow_query(output, checkables)

    def write_buffer_overflow_query(queryfile : str, checkables : list[str]) -> str:
        fout = open(queryfile, 'w')
        q = ""
        for checkable in checkables:
            q += f"A[] {checkable}.Overflow == false\n"
        fout.write(q)
        return q

    def parse_buffer_overflow_query(output : str, checkables : list[str]) -> dict:
        lines = output.split("\n")
        idx = 0
        results = {}
        for checkable in checkables:
            while "Verifying formula" not in lines[idx]:
                idx += 1
            verdict = lines[idx+1].strip() # Formula is/NOT satisfied
            if "Formula is NOT satisfied" in verdict:
                results[checkable] = False
            elif "Formula is satisfied" in verdict:
                results[checkable] = True
            idx += 1
        return results

    # query 3) from paper
    def max_buffer_size(modelfile : str, checkables : list[str]):
        queryfile = modelfile + '.q'
        UPPAAL.write_max_buffer_size_query(queryfile, checkables)
        output = UPPAAL.run_uppaal(modelfile, queryfile)
        return UPPAAL.parse_max_buffer_size_query(output, checkables)
        ## debug
        #return output

    def write_max_buffer_size_query(queryfile : str, checkables : list[str]):
        fout = open(queryfile, 'w')
        q = ""
        for checkable in checkables:
            q += f"sup:{checkable}.bufferUtil\n"
        fout.write(q)
        return q

    def parse_max_buffer_size_query(output : str, checkables : list[str]):
        return UPPAAL.parse_sup_query(output, checkables)

    # query 4) from paper
    def max_latency(modelfile : str, checkables : list[str]):
        queryfile = modelfile + '.q'
        UPPAAL.write_max_latency_query(queryfile, checkables)
        output = UPPAAL.run_uppaal(modelfile, queryfile)
        return UPPAAL.parse_max_latency_query(output, checkables)

    def write_max_latency_query(queryfile : str, checkables : list[str]):
        fout = open(queryfile, 'w')
        q = ""
        for checkable in checkables:
            q += f"sup {{{checkable}.ExecutionFinished}}: {checkable}.relTim[{checkable}.relcnt-1]\n"
        fout.write(q)
        return q

    def parse_max_latency_query(output : str, checkables : list[str]):
        return UPPAAL.parse_sup_query(output, checkables)
    
    # query 5) from paper
    def max_latency_trace(modelfile : str, checkables : list[str], max_latencies : dict = None):
        # get max latency for each checkable, if not provided
        if max_latencies is None:
            max_latencies = UPPAAL.max_latency(modelfile, checkables)
        queryfile = modelfile + '.q'
        UPPAAL.write_max_latency_trace_query(queryfile, max_latencies)
        ## returns raw trace -> needs to be parsed depending on use-case
        output = ""
        #output = UPPAAL.run_uppaal(modelfile, queryfile, ['-t', '1'])
        #return UPPAAL.parse_max_latency_trace_query(output, checkables)
        ##debug
        return output

    def write_max_latency_trace_query(queryfile : str, max_latencies : dict):
        fout = open(queryfile, 'w')
        q = ""
        for checkable, max_latency in max_latencies.items():
            q += f"E<> {checkable}.ExecutionFinished and {checkable}.relTim[{checkable}.relcnt-1]=={max_latency}\n"
        fout.write(q)
        return q

    # TODO: can be implemented depending on use-case
    def parse_max_latency_trace_query():
        return ""

    def parse_sup_query(output, checkables):
        lines = output.split("\n")
        results = {}
        idx = 0
        for checkable in checkables:
            while "sup:" not in lines[idx]:
                idx += 1
            results[checkable] = int(lines[idx][5:-1])
            idx += 1
        return results