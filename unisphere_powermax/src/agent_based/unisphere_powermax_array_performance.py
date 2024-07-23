#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#<<<unisphere_powermax_array_performance:sep(30)>>>
#SYMMETRIX_000297900498-RZ1{"Average": {"FEReqs": 17565.527, "FEWriteMissReqs": 333.76, "SystemMaxWPLimit": 11847405.0, "WriteResponseTime": 1.3820363, "FEHitReqs": 16194.116, "PercentCacheWP": 1.3488692, "DeviceWPEvents": 0.0, "ReadResponseTime": 0.42482662, "FEWriteHitReqs": 5894.95, "BEReqs": 12193.817, "HostIOs": 12869.486, "SystemWPEvents": 0.0, "timestamp": 1615458300000, "HostMBs": 684.82007, "FEReadMissReqs": 1037.6501, "BEIOs": 22252.123, "FEReadHitReqs": 10299.166, "FEWriteReqs": 6228.71, "BEReadReqs": 5830.823, "BEWriteReqs": 6362.993, "WPCount": 159806.0, "FEReadReqs": 11336.817}, "Maximum": {"FEReqs": 36209.227, "FEWriteMissReqs": 1147.6667, "SystemMaxWPLimit": 11847405.0, "WriteResponseTime": 2.5043576, "FEHitReqs": 33233.87, "PercentCacheWP": 1.3886416, "DeviceWPEvents": 0.0, "ReadResponseTime": 0.61653674, "FEWriteHitReqs": 11954.507, "BEReqs": 20315.166, "HostIOs": 30688.465, "SystemWPEvents": 0.0, "timestamp": 1615458300000, "HostMBs": 1389.8188, "FEReadMissReqs": 3889.6648, "BEIOs": 31872.55, "FEReadHitReqs": 27527.486, "FEWriteReqs": 12991.903, "BEReadReqs": 11549.166, "BEWriteReqs": 10000.0, "WPCount": 164518.0, "FEReadReqs": 28857.14}}



import json
from pprint import pprint
import re

from .agent_based_api.v1 import (
    register,
    Service,
    Result,
    State,
    Metric,
)


def camel_to_snake(name):
  name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
  return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

def discover_wp_cache(section):
    for i in section:
        j = json.loads(i[1])
        if j.get('Average', {}).get('PercentCacheWP', None) is not None and j.get('Maximum', {}).get('PercentCacheWP', None) is not None:
            yield Service(item=i[0])

def check_wp_cache(item, params, section):
    perf_info = list(filter(lambda x: x[0] == item, section))
    if len(perf_info) != 1:
        return

    perf_data = json.loads(perf_info[0][1])

    state = State.OK
    info_text = ""

    average_wp_cache = perf_data.get('Average', {}).get('PercentCacheWP', None)
    maximum_wp_cache = perf_data.get('Maximum', {}).get('PercentCacheWP', None)

    if average_wp_cache is None or maximum_wp_cache is None:
       yield Result(state=State.UNKNOWN, summary="got no data from agent")
       return
    
    average_hint = ''
    maximum_hint = ''
    if average_wp_cache >= params['average_levels'][1]:
        state = State.CRIT
        average_hint = '(!!)'
    elif average_wp_cache >= params['average_levels'][0]:
        state = State.WARN
        average_hint = '(!)'

    if maximum_wp_cache >= params['maximum_levels'][1]:
        state = State.CRIT
        average_hint = '(!!)'
    elif maximum_wp_cache >= params['maximum_levels'][0]:
        state = State.WARN
        average_hint = '(!)'

    info_text = "Average WP Cache usage: %s%% (last 5min)  %s (warn/crit %s/%s), Maximum WP Cache usage: %s%% (last 5min) %s (warn/crit %s/%s)" % ((average_wp_cache, average_hint) + params['average_levels'] + (maximum_wp_cache, maximum_hint) + params['maximum_levels'])

    yield Metric(name='average_wp_cache_5min', 
                 value=average_wp_cache,
                 levels=(params['average_levels'][0], params['average_levels'][1]),
                 boundaries=(0, 100))
    yield Metric(name='maximum_wp_cache_5min', 
                 value=maximum_wp_cache,
                 levels=(params['maximum_levels'][0], params['maximum_levels'][1]),
                 boundaries=(0, 100))

    yield Result(state=state, summary=info_text)

def discover_perf_info(section):
    for i in section:
        j = json.loads(i[1])
        if j.get('Average', None) is not None and j.get('Maximum', None) is not None:
            yield Service(item=i[0])

def check_perf_info(item, params, section):
    perf_info = list(filter(lambda x: x[0] == item, section))
    if len(perf_info) != 1:
        return

    perf_data = json.loads(perf_info[0][1])

    state = State.OK
    info_text = "Performance info check for gathering performance graphs"

    for x in perf_data.get('Average').keys():
        yield Metric(name="average_{}_5min".format(camel_to_snake(x)),
                     value=perf_data.get('Average')[x])

    yield Result(state=state, summary=info_text)

    
register.check_plugin(
    name = "unisphere_powermax_array_performance_wp_cache",
    sections = ['unisphere_powermax_array_performance'],
    service_name = 'Array WP Cache %s',
    discovery_function = discover_wp_cache,
    check_function = check_wp_cache,
    check_ruleset_name="unisphere_powermax_powermax_array_performance_wp_cache",
    check_default_parameters =  {"average_levels": (70, 90), "maximum_levels": (70, 90)}
)

register.check_plugin(
    name = "unisphere_powermax_array_performance_perf_info",
    sections = ['unisphere_powermax_array_performance'],
    service_name = 'Array Performance Info %s',
    discovery_function = discover_perf_info,
    check_function = check_perf_info,
    check_ruleset_name="unisphere_powermax_powermax_array_performance_info",
    check_default_parameters =  {}
)
