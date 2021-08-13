import numpy as np

import matplotlib.pyplot as plt
import matplotlib.animation as animation

"""
# Fixing random state for reproducibility
np.random.seed(19680801)
# Fixing bin edges
HIST_BINS = np.linspace(-4, 4, 100)

# histogram our data with numpy
data = np.random.randn(1000)
n, _ = np.histogram(data, HIST_BINS)

def prepare_animation(bar_container):

    def animate(frame_number):
        # simulate new data coming in
        data = np.random.randn(1000)
        n, _ = np.histogram(data, HIST_BINS)
        for count, rect in zip(n, bar_container.patches):
            rect.set_height(count)
        return bar_container.patches
    return animate

fig, ax = plt.subplots()
_, _, bar_container = ax.hist(data, HIST_BINS, lw=1,
                              ec="yellow", fc="green", alpha=0.5)
ax.set_ylim(top=55)  # set safe limit to ensure that all data is visible.

ani = animation.FuncAnimation(fig, prepare_animation(bar_container), 50,
                              repeat=False, blit=True)
plt.show()
"""

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

bar_container1 = plt.barh(range(1, 25), range(1, 25), color='green')
bar_container2 = plt.barh(range(1, 25), range(1, 25), color='green')


def prepare_animation(bar_container1, bar_container2):
    def animate(frame_number):
        bar_container1_new = plt.barh(range(1, 25), 5, color='green')
        bar_container2_new = plt.barh(range(1, 25), 6, left=5, color='red')
        bar_container1.patches = bar_container1_new.patches
        bar_container2.patches = bar_container2_new.patches
    return animate

ani = animation.FuncAnimation(fig, prepare_animation(bar_container1, bar_container2), repeat=False, interval=1000)

plt.show()
