import math
import numpy as np

CONVERSION_SIZES = ["", "K", "M", "G", "T", "P", "E"]
CONVERSION_SIZES_MEM = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]
CONVERSION_SIZES_MEM_BIT = ["b", "Kb", "Mb", "Gb", "Tb", "Pb", "Eb", "Zb"]


def _scale_value(value, base):
    i = int(math.log(value) / math.log(base)) if value != 0 else 0
    scaled = np.round(value / math.pow(base, i), 2)
    return scaled, i


def human_readable_size(bytes, base=1024):
    if bytes == 0:
        return (0, "B")
    sizes = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(bytes, base)))
    p = math.pow(base, i)
    s = round(bytes / p, 2)
    return (s, sizes[i])


def human_readable_size_fixed(bytes, unit, base=1024):
    if bytes == 0:
        return 0
    sizes = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    unitPos = sizes.index(unit.upper())
    for i in range(0, unitPos):
        bytes = bytes / base
    return round(bytes, 2)


def human_size_mem(bytes, bit=False, base=1024):
    value = bytes
    if bit: value *= 8
    [v, i] = _scale_value(value, base)

    if i >= len(CONVERSION_SIZES_MEM):
        return [
            value,
            CONVERSION_SIZES_MEM_BIT[0] if bit else CONVERSION_SIZES_MEM_BIT[0]
        ]

    if bit: return [v, CONVERSION_SIZES_MEM_BIT[i]]
    return [v, CONVERSION_SIZES_MEM[i]]


def human_size(value, base=1000):
    [v, i] = _scale_value(value, base)
    if i >= len(CONVERSION_SIZES):
        return [value, CONVERSION_SIZES[0]]
    return [v, CONVERSION_SIZES[i]]


def human_size_fixed(value, unit, base=1000):
    if value == 0: return 0
    unitPos = CONVERSION_SIZES.index(unit.upper())
    for _ in range(0, unitPos):
        value = value / base

    return np.round(value, 2)


def human_size_mem_fixed(bytes, unit, bit=False, base=1024):
    if bytes == 0: return 0
    if bit: bytes *= 8
    sizes = CONVERSION_SIZES_MEM_BIT if bit else CONVERSION_SIZES_MEM
    unitPos = sizes.index(unit.upper())
    for _ in range(0, unitPos):
        bytes = bytes / base

    return np.round(bytes, 2)
