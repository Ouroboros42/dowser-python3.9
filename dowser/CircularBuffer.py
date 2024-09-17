import numpy as np

class CircularBuffer:
    slots = 'array', 'head'

    def __init__(self, length: int):
        self.array = np.zeros(length, dtype=int)
        self.head = 0

    def __len__(self):
        return len(self.array)
    
    def __getitem__(self, index: int):
        return self.array.take(index + self.head, mode='wrap')

    def __setitem__(self, index: int, value: int):
        return self.array.put(index + self.head, value, mode='wrap')

    def inc_head(self, increment: int = 1):
        self.head = (self.head + increment) % len(self)

    def append(self, value: int):
        self.inc_head()
        self[0] = value

    def minmax(self):
        return np.min(self.array), np.max(self.array)

    def __iter__(self):
        for i in range(1, len(self) + 1):
            yield self[i]

if __name__ == "__main__":
    assert minmax(range(4)) == (0, 3)
    assert minmax([1, 10, 4, -100]) == (-100, 10)

    egbuff = CircularBuffer(10)
    assert all(egbuff[i] == 0 for i in range(len(egbuff)))

    egbuff[10] = 3
    assert egbuff[0] == 3
    egbuff.append(7)
    assert egbuff[0] == 7
    assert egbuff[-1] == 3
    
    expected = [ 7 ] + ([0] * 8) + [3]
    for a, b in zip(egbuff, expected):
        assert a == b

    for i in egbuff:
        pass