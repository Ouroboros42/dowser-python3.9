import time

if __name__ == "__main__":
    from dowser.app import MemoryApp

    with MemoryApp(8080):
        v = 10
        w = 'a'
        x = { v: v, w: w }
        x2 = x.copy()

        b = [ 0 ] * 1000

        input("End input (return) to close app.")

        print(dir())