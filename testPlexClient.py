import time
from PlexClient import PlexClient
from PlexUtil import PlexUtil
from RealtimePlot import RealtimePlot
from matplotlib import pyplot as plt
import time, random

start = time.time()

if __name__ == "__main__":
    fig, axes = plt.subplots()
    display = RealtimePlot(axes)

    with PlexClient() as pc:
        count_e = 0
        while True:
            time.sleep(1)
            arr = pc.getDataFromLongWave()
            for num in arr[64]:
                display.add(time.time() - start, num)
                plt.pause(0.001)