def minmax(iterable):
    vmin = vmax = None
    for val in iterable:
        if vmin is None or val < vmin:
            vmin = val
        if vmax is None or val > vmax:
            vmax = val
    return vmin, vmax

if __name__ == "__main__":
    assert minmax(range(4)) == (0, 3)
    assert minmax([1, 10, 4, -100]) == (-100, 10)