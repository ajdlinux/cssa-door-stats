#!/usr/bin/env python

from __future__ import division

import sys
import csv
import datetime

# Input log
if len(sys.argv) == 2:
    log_filename = sys.argv[1]
else:
    log_filename = '/var/log/door'

csv_reader = csv.reader(open(log_filename))

log_events = [(datetime.datetime.strptime(e[0], '%a %b %d %H:%M:%S %Y'), e[1]) for e in csv_reader]
log_events.sort() # not that this should be necessary

open_periods = []
open_period_start = None

for e in log_events:
    if e[1] == "open" and open_period_start == None:
	open_period_start = e[0]
    elif e[1] == "closed" and open_period_start != None:
	open_periods.append((open_period_start, e[0]))
	open_period_start = None
    elif e[1] == "stopped" and open_period_start != None:
	open_periods.append((open_period_start, e[0]))
	open_period_start = None
# TODO: if the door is open when the logfile ends, we just completely ignore it at the moment

def is_open(dt1, dt2=None, whole_period=False):
    """Return whether or not the door was open at a given time or period, as bool.
    
    dt1 - time to test / start of period to test
    dt2 = None - end of period to test
    whole_period = False - only return True if the door was open for the entire period
    """
    
    if dt2 == None:
        dt2 = dt1
    
    for period in open_periods:
        if whole_period:
            if period[0] <= dt1 <= dt2 <= period[1]:
                return True
        else:
            if period[0] <= dt1 <= period[1] or period[0] <= dt2 <= period[1] or (period[0] >= dt1 and period[1] <= dt2):
                return True
    return False

# TODO: perhaps need to make these functions exclude the moment of the end_time again?

def is_open_by_period(timedelta, start_time, end_time):
    """Return whether or not the door was open at regular intervals in a given period.
    
    timedelta - sampling interval
    start_time - start of period to test
    end_time - end of period to test"""
    
    is_open_periods = []
    current_time = start_time
    while current_time <= end_time:
        is_open_periods.append((current_time, is_open(current_time, current_time + timedelta)))
        current_time += timedelta
    return is_open_periods

def is_open_distribution(timedelta1, timedelta2, start_time, end_time):
    """Return the proportion of samples (taken at interval timedelta1) where the door is open... something something timedelta2
    TODO: Document this function better"""
    
    current_time = start_time
    
    frequency_open = []
    
    num_periods = 0
    while current_time <= end_time:
        is_open_periods = is_open_by_period(timedelta1, current_time, current_time + timedelta2) # FIXME: this may not properly account for when the last interval goes over end_time
        #print "is_open_periods: " + str(is_open_periods)
        
        if frequency_open == []:
            #print "instantiating frequency_open...",
            frequency_open = [status[1] and 1 or 0 for status in is_open_periods]
            #print frequency_open
        else:
            frequency_open = [status[1] and (freq + 1) or freq for status, freq in zip(is_open_periods, frequency_open)] # FIXME: if len(frequency_open) < len(is_open_periods)
        
        current_time += timedelta2
        num_periods += 1
    
    distribution = [f / num_periods for f in frequency_open]
    
    return distribution

def open_duration(start_time, end_time):
    duration = datetime.timedelta()
    
    for period in open_periods:
        if (period[0] <= start_time and period[1] >= start_time) \
            or (period[0] <= end_time and period[1] >= end_time) \
            or (start_time <= period[0] <= end_time and start_time <= period[1] <= end_time):
            duration += min(period[1], end_time) - max(period[0], start_time)
    
    return duration

###


def weekly_distribution_by_hour(start_time, end_time):
    """Return the proportion of samples (taken hourly) where the door is open, over a week, something something something
    TODO: Document this function better"""
    return is_open_distribution(datetime.timedelta(seconds=60*60), datetime.timedelta(seconds=60*60*24), start_time, end_time)

def average_open_duration_by_day(start_time, end_time):
    raise NotImplemented