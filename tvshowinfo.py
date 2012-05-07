#!/usr/bin/env python3.2
# -*- coding: utf-8 -*-
from pytvdbapi import api
import argparse
import codecs
import os
import re
import sys

# delimiter
d = "~"

tvdb_api_key = "083D567677C1B555"


def log(msg):
    """
    If verbose mode is active output is printed to screen
    """
    if args.verbose:
        print("DEBUG:" + os.path.basename(__file__) + ":" + msg)


def find_in_path(file_name, path=None):
    """
    Search for file in the defined pathes
    """
    path = path or '/etc/tvshowinfo:/etc/vdr/plugins/tvshowinfo'
    for d in path.split(os.pathsep):
        file_path = os.path.abspath(os.path.join(d, file_name))
        if os.path.exists(file_path):
            return file_path
    return file_name


def e_error(description, exit_code=1):
    """
    Print error message and exit with given code
    """
    log(description)
    sys.exit(exit_code)


def check_exceptions_tvshow(tvshow):
    """
    check for naming exceptions
    some code of this is from the sickbeard project
    """
    searchkey = ""
    db_file = find_in_path('exceptions.txt')
    db = codecs.open(db_file, 'r', 'utf-8')
    for line in db.readlines():
        tvdb_id, sep, aliases = line.partition(':')

        if not aliases:
            continue

        tvdb_id = int(tvdb_id)

        # regex out the list of shows, taking \' into account
        alias_list = [re.sub(r'\\(.)', r'\1', x) for x in re.findall(r"'(.*?)(?<!\\)',?", aliases)]
        for alias in alias_list:
            if alias == tvshow:
                searchkey = tvdb_id

    # If no result is found use the show name
    if not searchkey:
        searchkey = tvshow

    return searchkey


def main():
    # Define of variables
    global args

    # Parse Arguments
    parser = argparse.ArgumentParser(
        description='Options for finding the tvshow information.',
        epilog='All data is provided from http://www.thetvdb.com')
    parser.add_argument('-s', '--show', help='Name of the tv show', required=True)
    parser.add_argument('-e', '--episode', help='Episode Title', required=True)
    parser.add_argument('-sn', '--seasonnumber', help='Season Number', required=False, type=int)
    parser.add_argument('-en', '--episodenumber', help='Episode Number', required=False, type=int)
    parser.add_argument('-oen', '--overallepisodenumber', help='Overall Episode Number (Most time not set at thetvdb)', required=False, type=int)
    parser.add_argument('-lang', '--language', help='Only search for results in this language', required=False, default='en')
    parser.add_argument('-fus', '--forceunderscores', help='Force to use underscores instead of whitespaces', action='store_true')
    parser.add_argument('-v', dest='verbose', action='store_true')
    args = parser.parse_args()

    # Debug Logging of tvdb_api
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    tvshow = args.show
    episodename = args.episode

    # check for correct searchkey
    tvshow_searchkey = check_exceptions_tvshow(tvshow)
    log("Searching for show " + str(tvshow_searchkey))

    # Both variables have a minimum length
    if len(tvshow) <= 1:
        e_error("Show name is to short", 1)
    if len(episodename) <= 1 and not args.overallepisodenumber:
        e_error("Episode name is to short", 1)

    # use new pytvdbapi
    db = api.TVDB(tvdb_api_key)
    dbsearch = db.search(tvshow_searchkey, args.language)
    show = dbsearch[0]

    if args.seasonnumber and args.episodenumber:
        try:
            results = show[args.seasonnumber][args.episodenumber]
        except:
            e_error("Series " + tvshow + ", " + args.seasonnumber + d + args.episodenumber + " not found.", 5)

    elif args.overallepisodenumber:
        # loop through the episodes to find matching
        for season in show:
            for episode in season:
                if episode.absolute_number == args.overallepisodenumber:
                    results = episode

        try:
            results
        except:
            e_error("Series " + tvshow + ", " + args.overallepisodenumber + " not found.", 5)
    else:
        # clean not needed data
        search = re.split('[\(\)]', episodename, 2)
        episodenameclean = search[0].strip()
        # add again number extensions
        for ext in search:
            try:
                n = int(ext)
                episodenameclean = episodenameclean + " (" + ext.strip() + ")"
            except:
                continue

        log("Searching for episodename " + episodenameclean)

        # loop through the episodes to find matching
        for season in show:
            for episode in season:
                if episode.EpisodeName == episodenameclean:
                    results = episode

        try:
            results
        except:
            e_error("Series " + tvshow + "/" + episodenameclean + " not found.", 5)

    # Check for correct number of results
    try:
        results
    except:
        e_error("No Matching found.", 5)

    seasno = "%02d" % results.SeasonNumber
    epno = "%02d" % results.EpisodeNumber
    output = "Series" + d + tvshow + d + "Staffel_" + seasno + d + epno + " - " + results.EpisodeName
    if args.forceunderscores:
        output = output.replace(" ", "_")
    print(output)


if __name__ == "__main__":
    main()
