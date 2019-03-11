from matplotlib.ticker import FuncFormatter
from matplotlib.widgets import CheckButtons
from matplotlib import dates
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import datetime
import time
import os
import pty
import tempfile
import time
from functools import partial
#from pympler.tracker import SummaryTracker
#from pympler import muppy

timetag = list()
fig, ax = plt.subplots()
interfaces = dict()
prev_interfaces = dict()
persec_interface = dict()
display_stat = dict()
interface_list = dict()
check_if = None
check_stat = None
#tracker = SummaryTracker()
stats = {
        "rx_bits":[1,True],
        "rx_packets":[2,True],
        "rx_errs": [3,False],
        "rx_drop":[4,False],
        "rx_fifo":[5,False],
        "rx_frame":[6,False],
        "rx_compressed":[7,False],
        "rx_multicast":[8,False],
        "tx_bits":[9,True],
        "tx_packets":[10,True],
        "tx_errs":[11,False],
        "tx_drop":[12,False],
        "tx_fifo":[13,False],
        "tx_colls":[14,False],
        "tx_carrier":[15,False],
        "tx_compressed":[16,False]
        }

def update():
    global interfaces, prev_interfaces, persec_interfaces, timetag, display_stat
    output = ""
    with open("/proc/net/dev", "r") as f:
        output = f.read()
    lines = output.split('\n')
    del lines[0:2] #remove headers
        #Inter-|   Receive                                                |  Transmit
        # face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    for line in lines:
        interface = line.split()
        if len(interface) > 0:
            if_name = interface[0].strip(':')
            interface_list.setdefault(if_name, True)
            for stats_key in stats:
                if stats_key == "rx_bits" or stats_key == "tx_bits":
                    interfaces[if_name+"_"+stats_key] = [int(interface[stats[stats_key][0]])*8,interface_list[if_name], stats[stats_key][1]]
                else:
                    interfaces[if_name+"_"+stats_key] = [int(interface[stats[stats_key][0]]),interface_list[if_name], stats[stats_key][1]]

    if len(prev_interfaces) == 0:
        for key in interfaces:
            prev_interfaces[key] = interfaces[key][0]

    for key in interfaces:
        display_stat.setdefault(key, True)
        persec_interface.setdefault(key, [list(), True, True])
        persec_interface[key][0].append(interfaces[key][0] - prev_interfaces[key])
        persec_interface[key][1] = interfaces[key][1]
        persec_interface[key][2] = interfaces[key][2]
        if len(persec_interface[key][0]) > 60:
            del persec_interface[key][0][0]

    for key in interfaces:
        del prev_interfaces[key]
        prev_interfaces[key] = interfaces[key][0]
    del interfaces[key]
    timetag.append(datetime.datetime.now())
    if len(timetag) > 60:
        del timetag[0]


def format_date():
    xfmt = dates.DateFormatter("%d-%m-%y %H:%M:%S")
    ax.xaxis.set_major_formatter(xfmt)
    fig.autofmt_xdate()

def y_fmt(y, pos):
    decades = [1e9, 1e6, 1e3, 1e0, 1e-3, 1e-6, 1e-9 ]
    suffix  = ["G", "M", "k", "" , "m" , "u", "n"  ]
    if y == 0:
        return str(0)
    for i, d in enumerate(decades):
        if np.abs(y) >=d:
            val = y/float(d)
            signf = len(str(val).split(".")[1])
            if signf == 0:
                return '{val:d} {suffix}'.format(val=int(val), suffix=suffix[i])
            else:
                if signf == 1:
                    if str(val).split(".")[1] == "0":
                       return '{val:d} {suffix}'.format(val=int(round(val)), suffix=suffix[i])
                tx = "{"+"val:.{signf}f".format(signf = signf) +"} {suffix}"
                return tx.format(val=val, suffix=suffix[i])

                #return y
    return y

def draw_plots():
    for key in persec_interface:
        if persec_interface[key][1]:
            if persec_interface[key][2]:
                ax.plot(timetag, list(persec_interface[key][0]), label=key)
            #else:
            #    ax.plot(timetag, [0]*len(timetag), label=key+ " (off)")
    ax.set_yscale('log', nonposy='clip')
    ax.yaxis.set_major_formatter(FuncFormatter(y_fmt))

def draw_legend():
    leg = ax.legend(loc='upper center', bbox_to_anchor=(0.5,-0.05), ncol=8, fancybox=True)
    leg.get_frame().set_alpha(0.4)
    for legtext in leg.get_texts():
        legtext.set_picker(5)

def draw_checkboxes():
    global check_if, check_stat
    if check_if == None:
        rax = plt.axes([0.01, 0.8, 0.05, 0.05], title="interfaces")
        check_if = CheckButtons(rax, interface_list.keys(), interface_list.values())
        check_if.on_clicked(partial(oncheck))
    if check_stat == None:
        rax = plt.axes([0.01, 0.5, 0.08, 0.15], title="stats")
        vis = [value[1] for value in stats.values()]
        check_stat = CheckButtons(rax, stats.keys(), vis)
        check_stat.on_clicked(partial(oncheck_stats))

def animate(i):
    ax.clear()
    update()
    draw_plots()
    format_date()
    draw_legend()
    draw_checkboxes()
    #tracker.print_diff()
    #all_objects = muppy.get_objects()
    #print(len(all_objects))

def onpick(event):
    legtext = event.artist.get_text().split()[0]
    display_stat[legtext] = not display_stat[legtext]
    fig.canvas.draw()

def oncheck(label):
    interface_list[label] = not interface_list[label]
    plt.draw()

def oncheck_stats(label):
    stats[label][1] = not stats[label][1]
    plt.draw()



fig.canvas.mpl_connect('pick_event', onpick)
ani = animation.FuncAnimation(fig, animate, interval=1000)
plt.show(block=True)
