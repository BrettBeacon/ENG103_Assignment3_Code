import numpy as np

# Constants
FreqS = 25  # Sampling frequency
BUFFER_SIZE = FreqS * 4
MA4_SIZE = 4
MAX_NUM = 15
MIN_HEIGHT = 30
MIN_DISTANCE = 4

# Spo2 Table
uch_spo2_table = [
    95, 95, 95, 96, 96, 96, 97, 97, 97, 97, 97, 98, 98, 98, 98, 98, 99, 99, 99, 99,
    99, 99, 99, 99, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
    100, 100, 100, 100, 99, 99, 99, 99, 99, 99, 99, 99, 98, 98, 98, 98, 98, 98, 97, 97,
    97, 97, 96, 96, 96, 96, 95, 95, 95, 94, 94, 94, 93, 93, 93, 92, 92, 92, 91, 91,
    90, 90, 89, 89, 89, 88, 88, 87, 87, 86, 86, 85, 85, 84, 84, 83, 82, 82, 81, 81,
    80, 80, 79, 78, 78, 77, 76, 76, 75, 74, 74, 73, 72, 72, 71, 70, 69, 69, 68, 67,
    66, 66, 65, 64, 63, 62, 62, 61, 60, 59, 58, 57, 56, 56, 55, 54, 53, 52, 51, 50,
    49, 48, 47, 46, 45, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 31, 30, 29,
    28, 27, 26, 25, 23, 22, 21, 20, 19, 17, 16, 15, 14, 12, 11, 10, 9, 7, 6, 5,
    3, 2, 1
]

# Variables
an_x = np.zeros(BUFFER_SIZE, dtype=int)
an_y = np.zeros(BUFFER_SIZE, dtype=int)


def maxim_heart_rate_and_oxygen_saturation(pun_ir_buffer, n_ir_buffer_length, pun_red_buffer):
    global an_x, an_y
    
    # Reset an_x and an_y arrays
    an_x = -1 * (pun_ir_buffer - np.mean(pun_ir_buffer))
    an_y = pun_red_buffer

    # 4 pt Moving Average
    for k in range(BUFFER_SIZE - MA4_SIZE):
        an_x[k] = (an_x[k] + an_x[k+1] + an_x[k+2] + an_x[k+3]) // 4

    # Calculate threshold
    n_th1 = np.mean(an_x)
    n_th1 = max(MIN_HEIGHT, n_th1)
    n_th1 = min(60, n_th1)

    an_ir_valley_locs = np.zeros(MAX_NUM, dtype=int)
    n_npks = 0
    n_peak_interval_sum = 0

    # Find peaks
    maxim_find_peaks(an_ir_valley_locs, n_npks, an_x, BUFFER_SIZE, n_th1, MIN_DISTANCE, MAX_NUM)

    if n_npks >= 2:
        for k in range(1, n_npks):
            n_peak_interval_sum += (an_ir_valley_locs[k] - an_ir_valley_locs[k - 1])

        n_peak_interval_sum = n_peak_interval_sum / (n_npks - 1)
        pn_heart_rate = int((FreqS * 60) / n_peak_interval_sum)
        pch_hr_valid = 1
    else:
        pn_heart_rate = -999
        pch_hr_valid = 0

    n_exact_ir_valley_locs_count = n_npks
    n_ratio_average = 0
    n_i_ratio_count = 0
    an_ratio = np.zeros(5, dtype=int)

    for k in range(5):
        an_ratio[k] = 0

    for k in range(n_exact_ir_valley_locs_count - 1):
        if an_ir_valley_locs[k + 1] - an_ir_valley_locs[k] > 3:
            n_y_dc_max = -16777216
            n_x_dc_max = -16777216
            i = an_ir_valley_locs[k]
            while i < an_ir_valley_locs[k + 1]:
                if an_x[i] > n_x_dc_max:
                    n_x_dc_max = an_x[i]
                    n_x_dc_max_idx = i
                if an_y[i] > n_y_dc_max:
                    n_y_dc_max = an_y[i]
                    n_y_dc_max_idx = i
                i += 1
            n_y_ac = (an_y[an_ir_valley_locs[k + 1]] - an_y[an_ir_valley_locs[k]]) * (n_y_dc_max_idx - an_ir_valley_locs[k])
            n_y_ac = an_y[an_ir_valley_locs[k]] + n_y_ac // (an_ir_valley_locs[k + 1] - an_ir_valley_locs[k])
            n_y_ac = an_y[n_y_dc_max_idx] - n_y_ac
            n_x_ac = (an_x[an_ir_valley_locs[k + 1]] - an_x[an_ir_valley_locs[k]]) * (n_x_dc_max_idx - an_ir_valley_locs[k])
            n_x_ac = an_x[an_ir_valley_locs[k]] + n_x_ac // (an_ir_valley_locs[k + 1] - an_ir_valley_locs[k])
            n_x_ac = an_x[n_y_dc_max_idx] - n_x_ac
            n_nume = (n_y_ac * n_x_dc_max)
            n_denom = (n_x_ac * n_y_dc_max)

            if n_denom > 0 and n_i_ratio_count < 5 and n_nume != 0:
                an_ratio[n_i_ratio_count] = (n_nume * 100) // n_denom
                n_i_ratio_count += 1

    an_ratio.sort()
    n_middle_idx = n_i_ratio_count // 2

    if n_middle_idx > 1:
        n_ratio_average = (an_ratio[n_middle_idx - 1] + an_ratio[n_middle_idx]) // 2
    else:
        n_ratio_average = an_ratio[n_middle_idx]

    if 2 < n_ratio_average < 184:
        n_spo2_calc = uch_spo2_table[n_ratio_average]
        pn_spo2 = n_spo2_calc
        pch_spo2_valid = 1
    else:
        pn_spo2 = -999
        pch_spo2_valid = 0


def maxim_find_peaks(pn_locs, n_npks, pn_x, n_size, n_min_height, n_min_distance, n_max_num):
    maxim_peaks_above_min_height(pn_locs, n_npks, pn_x, n_size, n_min_height)
    maxim_remove_close_peaks(pn_locs, n_npks, pn_x, n_min_distance)
    n_npks = min(n_npks, n_max_num)


def maxim_peaks_above_min_height(pn_locs, n_npks, pn_x, n_size, n_min_height):
    i = 1
    n_width = 0
    n_npks = 0

    while i < n_size - 1:
        if pn_x[i] > n_min_height and pn_x[i] > pn_x[i - 1]:
            n_width = 1
            while i + n_width < n_size and pn_x[i] == pn_x[i + n_width]:
                n_width += 1

            if pn_x[i] > pn_x[i + n_width] and n_npks < MAX_NUM:
                pn_locs[n_npks] = i
                i += n_width + 1
                n_npks += 1
            else:
                i += n_width
        else:
            i += 1


def maxim_remove_close_peaks(pn_locs, n_npks, pn_x, n_min_distance):
    i = -1
    n_old_npks = 0
    n_dist = 0

    pn_locs.sort()

    for i in range(n_npks + 1):
        n_old_npks = n_npks
        n_npks = i + 1

        for j in range(i + 1, n_old_npks):
            n_dist = pn_locs[j] - (pn_locs[i] if i == -1 else pn_locs[i])

            if n_dist > n_min_distance or n_dist < -n_min_distance:
                pn_locs[n_npks] = pn_locs[j]