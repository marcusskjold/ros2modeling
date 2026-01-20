###
## Class with statics functions to generate latex-graphs from UPPAAL traces.
#

class Grapher:

    # Finds upper bound on time for a trace
    def get_ul(trace: list[tuple[str, str, str, str]]) -> int:
       # print("UL")
       # print(trace)
       (time, act, idd, data) = trace[-1]
       return int(time)


    # Fills in missing data by traversing the trace backwards
    def fill_trace(trace: list[tuple[str, str, str, str]]) -> None:
        last_data = ""
        last_idd = ""
        for i in range(len(trace)-1, -1, -1):
            (time, act, idd, data) = trace[i]
            if act == "DONE":
                last_data = data
                last_idd = idd
            if act == "START":
                trace[i] = (time, act, last_idd, last_data)



    # Make sure trace is filled
    # Final part of trace should be a monitor:
    def find_mrt_path(trace: list[tuple[str, str, str, str]]
                      ) -> list[tuple[str, str, str, str]]:
        (ftime, fact, farg, fdata) = trace[-1]
        assert(fact == "MONITOR")
        final_data = farg

        path: list[tuple[str, str, str, str]] = []
        # Go through trace and only keep bits using final_data

        last_id = None
        fired = False
        for idx, (time, act, idd, data) in enumerate(trace):
            if act == "MONITOR":
                ()
            # we start our path from final_data, so lets skip ahead until it is FIRED
            elif not fired:
                if (act == "FIRE" and data == final_data):
                    path.append(trace[idx])
                    # print("++")
                    last_id = idd
                    fired = True

            # otherwise, we just track it ...
            else:
                if data == final_data:
                    path.append(trace[idx])
                    last_id = idd
            # If a process is executed again before, we should track new data (perhaps?)
                elif idd == last_id:
                    path.append(trace[idx])
                    final_data = data

        return path


    def gen_mrt(nodes: list[str], trace: list[tuple[str, str, str, str]]) -> list[str]:

        ul: int = Grapher.get_ul(trace)
        Grapher.fill_trace(trace)
        path = Grapher.find_mrt_path(trace)

        # We dont want the monitor states when drawing
        trace = list(filter(lambda x : not x[1] == "MONITOR", trace))
        strings: list[str] = []
        strings.append("\\documentclass{article}")
        strings.append("\\usepackage{tikz}")
        strings.append("\\begin{document}")
        strings.append("\\begin{figure}")

        strings.append("\\begin{tikzpicture}[scale=0.5,shift={(current page.center)}]")
        strings.append("\\draw[step=0.5cm,gray!50,very thin] (0,0) grid (" \
            + str(ul/10) + ", " + str(len(nodes)) + ");")

        for i in range(int(ul/10)+1):
            strings.append("\\draw (" \
                + str(i) + " cm,2pt) -- (" \
                + str(i) + " cm,-2pt) node[anchor=north] {\\tiny$" \
                + str(i*10) + "$};")

        # Thicker lines for each node
        for i, n in enumerate(nodes):
            strings.append("\\draw[-] (0," \
                + str(i) + ") -- (" \
                + str(ul/10) + "," \
                + str(i) + ") node[right] {};")
            strings.append(
                "\\node[minimum width=4cm, anchor=east, text width=4cm] at (0," \
                + str(i+0.5) + ") {\small " \
                + n + "};")


        time, act, arg, data = "", "", "", ""
        prev_start = ""
        for time, act, arg, data in trace:
            t = str(int(time)/10)
            if act == "START":
                prev_start = t
            elif act == "DONE":
                i = int(arg)
                # print("ARG: ", arg)
                strings.append("\\draw[->] (" \
                    + prev_start + "," \
                    + str(i) + ".1) -- (" \
                    + prev_start + "," \
                    + str(i) + ".8);")
                strings.append("\\draw[<-] (" \
                    + t + "," \
                    + str(i) + ".1) -- (" \
                    + t + "," \
                    + str(i) + ".8);")
            elif act == "FIRE":
                # print("FIRE____")
                strings.append("\\draw[->,thick, orange] (" \
                    + t + "," \
                    + arg + ".1) -- (" \
                    + t + "," \
                    + arg + ".8);")

            elif act == "WINDOW":
                strings.append("\\draw[red, dashed] (" \
                    + t + ",0) -- (" \
                    + t + "," \
                    + str(len(nodes))  + ");")

            elif act == "MONITOR":
                ()
            else:
                raise Exception("Unhandled:" + act)


        strings.append("\\draw[<-,thick,green] (" \
            + t + "," \
            + arg + ".1) -- (" \
            + t + "," \
            + arg + ".8);")


        ### Now we add the path:
        ### First part should be a FIRE
        (ftime, fact, farg, fdata) = path[0]
        assert(fact == "FIRE")

        x1 = int(ftime)/10
        y1 = int(farg) + 1

        # We peek to draw the first line, afterwards we check pairwise
        (time, act, _, _) = path[1]
        assert(act == "START")
        x2 = int(time)/10
        y2 = y1

        strings.append("\\draw[thick, blue] (" \
            + str(x1) + "," \
            + str(y1) + ") -- (" \
            + str(x2) + "," \
            + str(y2) + ");")
        last_x, last_y = x2, y2

        for i in range(1, len(path), 2):
            (time1, act1, arg1, data1) = path[i]
            (time2, act2, arg2, data2) = path[i+1]
            assert(act1 == "START" and act2 == "DONE")

            # Draw a line from last_x, last_y to START,
            x1 = int(time1)/10
            y1 = int(arg1) + 0.5
            strings.append("\\draw[thick, blue] (" \
                + str(last_x) + "," \
                + str(last_y) + ") -- (" \
                + str(x1) + "," \
                + str(y1) + ");")

            # and from START to DONE
            x2 = int(time2)/10
            y2 = y1
            strings.append("\\draw[thick, blue] (" \
                + str(x1) + "," \
                + str(y1) + ") -- (" \
                + str(x2) + "," \
                + str(y2) + ");")

            last_x, last_y = x2, y2

        strings.append("\\end{tikzpicture}")
        strings.append("\\end{figure}")
        strings.append("\\end{document}")
        return strings
