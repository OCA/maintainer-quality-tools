#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pstats
import sys


def print_stats(filter_fnames=None, exclude_fnames=None,
                sort_index=0, limit=0):
    """Print stats with a filter or exclude filenames, sort index and limit
    :param filter_fnames: List of relative paths to filter and show them.
    :param exclude_fnames: List of relative paths to avoid show them.
    :param sort_index: Integer with `pstats tuple` index to sort the result.
    :param limit: Integer to limit max result.
    :return: Directly print of `pstats` summarize info.
    """
    if filter_fnames is None:
        filter_fnames = ['.py']
    if exclude_fnames is None:
        exclude_fnames = []

    fname = os.path.expanduser('~/.openerp_server.stats')
    if not os.path.isfile(fname):
        print "No cProfile stats to report."
        return False
    try:
        fstats = pstats.Stats(fname)
    except TypeError:
        print "No cProfile stats valid."
        return False
    stats = fstats.stats

    stats_filter = {}
    for stat in stats:
        for tuple_stats in stats[stat][4].keys():
            for filter_fname in filter_fnames:
                if filter_fname in tuple_stats[0]:
                    exclude = False
                    for exclude_fname in exclude_fnames:
                        if exclude_fname in tuple_stats[0]:
                            exclude = True
                            break
                    if exclude:
                        break
                    old_fstats = stats_filter.setdefault(
                        tuple_stats, (0, 0, 0, 0))
                    new_fstats = stats[stat][4][tuple_stats]
                    sum_fstats = tuple([
                        old_item + new_item
                        for old_item, new_item in zip(old_fstats, new_fstats)])
                    stats_filter[tuple_stats] = sum_fstats
                    break

    def sort_stats(dict_stats, index=0, reverse=True):
        """param index: Index of tuple stats standard to sort
        :return: List of items ordered by index value"""
        return sorted(dict_stats.items(), key=lambda x: x[1][index],
                      reverse=reverse)

    # fstats.sort_stats('cumulative')
    stats_filter_sorted = sort_stats(stats_filter, sort_index)
    if limit:
        stats_filter_sorted = stats_filter_sorted[:limit]

    for file_data, stats in stats_filter_sorted:
        print "{0:10d} {1:10d} {2:10.6f} {3:10.6f}".format(*stats),
        print "%s:%s %s" % file_data
    return True

if __name__ == '__main__':
    if len(sys.argv) == 1:
        sys.argv.append('.py')
    fnames_filter = sys.argv[1].split(',')
    if len(sys.argv) == 2:
        fnames_exclude = None
    else:
        fnames_exclude = sys.argv[2].split(',')
    print_stats(fnames_filter, fnames_exclude)
