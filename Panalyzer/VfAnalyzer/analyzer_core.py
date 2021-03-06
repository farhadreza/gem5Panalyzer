import numpy as np
from pathlib import Path
from Panalyzer.TraceParser.csv2np import csv2np


class AvfAnalyzer:
    def __init__(self, access_history, tick, masking_history):
        self.wr_list = access_history
        self.t_list = tick
        self.masking_history = masking_history

    def ace_calculator_wr(self):
        tick_list = self.t_list
        w_history = self.wr_list[0, :]
        r_history = self.wr_list[1, :]
        m_history = self.masking_history
        w_history[0], w_history[-1] = 1, 1  # intentionally alternating the boundary of write history to handle weird
        # special cases more easily

        ace_realtime = np.vstack((tick_list, np.zeros([1, tick_list.size], dtype=np.int64)))  # For the purpose of
        # the easier debugging, ace_realtime matrix of current reg is constructed as:
        # First row: Tick; Second row: Ace ticks correspond to the current Tick
        prev_w = 0
        ace_prev = 0
        ace_total = 0

        for i in range(tick_list.size):
            if r_history[i] == 1:
                ace_local = (tick_list[i] - tick_list[prev_w] - ace_prev) * (1 - m_history[i])  # The ACE interval will
                # be masked if M=1. Otherwise, ACE interval will be 100% vulnerable if M=0
                ace_total = ace_total + ace_local
                ace_prev = ace_prev + ace_local
                ace_realtime[1, i] = ace_total
            else:
                ace_realtime[1, i] = ace_realtime[1, i - 1]

            if w_history[i] == 1 and r_history[i] == 0:
                prev_w = i
                ace_prev = 0
            elif w_history[i] == 1 and r_history[i] == 1:
                prev_w = prev_w
                ace_prev = ace_prev
            else:
                prev_w = prev_w
                ace_prev = ace_prev
        return ace_realtime


if __name__ == "__main__":
    M = np.full(13000, 0.9, dtype=float)
    reg_num = 16
    """
    expected output:
    1 3 [20]
    4 8 [30]
    4 8 [30, 50]
    4 8 [30, 50, 60]
    8 10 [20]
    10 12 [20]

    [[  0  10  30  40  50  80 100 110 130 150 180 200]
     [  0   0  20   0   0  30  50  60   0  20   0  20]]
    """
    project_dir = Path(__file__).resolve().parent.parent
    csv_dir = project_dir.joinpath('tempcsv')
    fname = "prime.csv"
    T = csv2np(csv_dir / fname, 0, 1000, 16).arm32detailed()
    details = csv2np(csv_dir / fname, 0, 1000, 16).arm32detailed()
    ace_regs = np.zeros(reg_num + 1, dtype=np.int64)
    for i in range(reg_num):
        ace = AvfAnalyzer(details['wr'][i, :, :], details['tick'], details['masking'][i, :]).ace_calculator_wr()[1, :]
        ace_regs[i] = ace[-1]
    ace_regs[-1] = details['tick'][-1]
    print(ace_regs)
