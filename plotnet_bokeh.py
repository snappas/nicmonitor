import numpy as np
from bokeh.layouts import row, column, gridplot
from bokeh.models import ColumnDataSource, Slider, Select
from bokeh.plotting import curdoc, figure
from bokeh.driving import count
from bokeh.models.widgets import CheckboxGroup
from bokeh.models.widgets.inputs import AutocompleteInput
import datetime
from collections import Counter
import time
import os
import pty
import tempfile
import time
from functools import partial
#from pympler.tracker import SummaryTracker
#from pympler import muppy
#from pympler import refbrowser
from pympler.web import start_in_background
from pympler import classtracker
from bokeh.palettes import viridis


p = figure(plot_height=500, tools="xpan,xwheel_zoom,xbox_zoom,reset, hover", x_axis_type='datetime', y_axis_type='log',y_axis_location="right")

dataSource = ColumnDataSource()
class StatRecord:
    def __init__(self, statName, indexOfStat, isStatEnabled,interfaceName):
        self.statName = statName
        self.indexOfStat = indexOfStat
        self.isStatEnabled = isStatEnabled
        self.currentStat = 0
        self.previousStat = 0
        self.perSecondStats = None
        self.interfaceName = interfaceName

    def update(self, listOfStats):
        self.currentStat = int(listOfStats[self.indexOfStat])
        if self.perSecondStats == None:
            self.previousStat = self.currentStat
        if self.statName == "tx_bits" or self.statName == "rx_bits":
            self.perSecondStats = ((self.currentStat - self.previousStat)*8)
        else:
            self.perSecondStats = (self.currentStat - self.previousStat)
        self.previousStat = self.currentStat
        if self.perSecondStats == 0:
            self.perSecondStats = 1e-1
        return dict({str(self.interfaceName+"_"+self.statName):[self.perSecondStats]})

class InterfaceStats:
    def __init__(self, interfaceName, isInterfaceEnabled, stats):
        self.interfaceName = interfaceName
        self.isInterfaceEnabled = isInterfaceEnabled
        self.interfaceStats = dict()
        for statKey, statValue in stats.items():
            self.interfaceStats[statKey] = StatRecord(statKey, statValue[0], statValue[1], self.interfaceName)

    def getStats(self):
        return self.interfaceStats

    def getStat(self, statName):
        return self.interfaceStats[statName]

    def update(self, listOfStats):
        collect = dict()
        for stat in list(self.interfaceStats.values()):
            #print(collect)
            new_stats = stat.update(listOfStats)
            collect = {**collect, **new_stats, **{k: op(collect[k], new_stats[k]) for k in new_stats.keys() & collect}}
        return collect
class InterfaceContainer:
    def __init__(self):
        self.interfaces = dict()
        self.timetag = list()
        self.stats = {
                "rx_bits":[1,True],
                "rx_packets":[2,False],
                "rx_errs": [3,False],
                "rx_drop":[4,False],
                "rx_fifo":[5,False],
                "rx_frame":[6,False],
                "rx_compressed":[7,False],
                "rx_multicast":[8,False],
                "tx_bits":[9,True],
                "tx_packets":[10,False],
                "tx_errs":[11,False],
                "tx_drop":[12,False],
                "tx_fifo":[13,False],
                "tx_colls":[14,False],
                "tx_carrier":[15,False],
                "tx_compressed":[16,False]
                }

    def getInterface(self, interfaceName):
        self.interfaces.setdefault(interfaceName, InterfaceStats(interfaceName, True, self.stats))
        return self.interfaces[interfaceName]

    def getInterfaces(self):
        return list(self.interfaces.keys())
    def getInterfacesEnabled(self):
        print([int(interface.isInterfaceEnabled) for interface in self.interfaces.values()])
        return [int(interface.isInterfaceEnabled) for interface in self.interfaces.values()]

    def update(self):
        output = ""
        with open("/proc/net/dev", "r") as f:
            output = f.read()
        listOfInterfaces = output.split('\n')
        del listOfInterfaces[0:2] #remove headers
        self.timetag = datetime.datetime.now()
        collect = dict()
        for interfaceString in listOfInterfaces:
            if len(interfaceString) > 0:
                listOfStats = interfaceString.split()
                new_stats = self.getInterface(listOfStats[0].strip(':')).update(listOfStats)
                collect = {**collect, **new_stats, **{k: op(collect[k], new_stats[k]) for k in new_stats.keys() & collect}}

        time = dict({"time":[self.timetag]})
        collect = {**collect, **time, **{k: op(collect[k], time[k]) for k in time.keys() & collect}}
        return collect
        #print(collect)
        #dataSource.stream(collect, 60)

    def __call__(self):
        dataSource.stream(self.update(), 60)

mean = Slider(title="mean", value=0, start=-0.01, end=0.01, step=0.001)
stddev = Slider(title="stddev", value=0.04, start=0.01, end=0.1, step=0.01)

#trackerThread = classtracker.ClassTracker().start_periodic_snapshots()
interfaceContainer = InterfaceContainer()
dataDict = interfaceContainer.update()
dataSource.data=dataDict
palette = viridis(len(dataDict))
for i, (key, value) in enumerate(dataDict.items()):
    if key != 'time':
        p.line(x='time', y=key, source=dataSource, color=palette[i])
        print(key)

#p.legend.location= "bottom_center"
#p.legend.click_policy = "mute"
#p.legend.orientation="horizontal"
interfaceSelection = CheckboxGroup(labels=interfaceContainer.getInterfaces(),active=[i for i in range(len(interfaceContainer.getInterfaces()))])
statSelection = CheckboxGroup(labels=list(interfaceContainer.stats.keys()),active=[i for i in range(len(interfaceContainer.getInterfaces()))])
def update_selected(wttr,old,new):
    a_val = autocomp.value
    print(a_val)
#start_in_background(tracker=trackerThread)
autocomp = AutocompleteInput(completions=['test2','test3','hello','goodbye'])
autocomp.on_change('value',update_selected )


curdoc().add_root(column(row(autocomp, interfaceSelection,statSelection),row(mean, stddev), gridplot([[p]], toolbar_location="left", plot_width=1000)))
curdoc().add_periodic_callback(interfaceContainer, 1000)
curdoc().title = "OHLC"

