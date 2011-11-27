#!/usr/bin/env python2.6
# coding: utf-8
import tvdb_api
import sys, argparse, string, re, os, codecs

# delimiter
d = "~"

#
## logging
def log(msg):
    if args.verbose:
    	print "DEBUG:"+os.path.basename(__file__)+":"+msg

def find_in_path(file_name, path=None):
    path = path or '/etc/tvshowinfo:/etc/vdr/plugins/tvshowinfo'
    for d in path.split(os.pathsep):
        file_path = os.path.abspath(os.path.join(d, file_name))
        if os.path.exists(file_path):
            return file_path
    return file_name

#
## check for naming exceptions
## some code is from the sickbeard project
def check_exceptions_tvshow(tvshow):
    searchkey = ""
    db_file = find_in_path('exceptions.txt')
    db = codecs.open(db_file,'r', 'utf-8')
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

#
## main
def main():
    # Define of variables
    global args

    # Parse Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--show', help='Name of the tv show', required=True)
    parser.add_argument('-e', '--episode', help='Episode Title', required=True)
    parser.add_argument('-sn', '--seasonnumber', help='Season Number', required=False)
    parser.add_argument('-en', '--episodenumber',  help='Episode Number', required=False)
    parser.add_argument('-oen', '--overallepisodenumber',  help='Overall Episode Number (Most time not set at thetvdb)', required=False)
    parser.add_argument('-lang', '--language',  help='Only search for results in this language', required=False)
    parser.add_argument('-fus', '--forceunderscores',  help='Force to use underscores instead of whitespaces', action='store_true')
    parser.add_argument('-v', dest='verbose', action='store_true')
    args = parser.parse_args()

    # Debug Logging of tvdb_api
    if args.verbose:
        import logging
        logging.basicConfig(level = logging.DEBUG)

    tvshow = args.show.decode(sys.getfilesystemencoding())
    episodename = args.episode.decode(sys.getfilesystemencoding())
    if args.language:
        args.language = args.language.decode(sys.getfilesystemencoding())

    # check for correct searchkey
    tvshow_searchkey = check_exceptions_tvshow(tvshow)

    # Both variables have a minimum length
    if len(tvshow) <= 1:
        log("Show name is to short")
        sys.exit(1)
    if len(episodename) <= 1 and not args.overallepisodenumber:
        log("Episode name is to short")
        sys.exit(1)

    t = tvdb_api.Tvdb(language=args.language)
    if args.seasonnumber and args.episodenumber:
        try:
            results = t[tvshow_searchkey][args.seasonnumber][args.episodenumber]
        except tvdb_api.tvdb_shownotfound:
            print
            log("Series "+tvshow+", "+args.seasonnumber+d+args.episodenumber+" not found.")
            sys.exit(5)
    elif args.overallepisodenumber:
        try:
            results = t[tvshow_searchkey].search(args.overallepisodenumber, key = 'absolute_number')
        except tvdb_api.tvdb_shownotfound:
            print
            log("Series "+tvshow+", "+args.overallepisodenumber+" not found.")
            sys.exit(5)
    else:
        results = ""
        search = re.split('[\(\)]', episodename)
        episodenameclean=string.strip(search[0])
        log("Searching for episodename "+episodenameclean)

        try:
            results = t[tvshow_searchkey].search(episodenameclean, key = 'episodename')
        except tvdb_api.tvdb_shownotfound:
            print
            log("Series "+tvshow+" not found.")
            sys.exit(5)
        except (tvdb_api.tvdb_episodenotfound, tvdb_api.tvdb_attributenotfound, tvdb_api.tvdb_seasonnotfound):
            print
            log("Episode "+episodenameclean+" not found.")
            sys.exit(5)

    # Check for correct number of results
    if not results:
        log("No Matching found.")
        sys.exit(5)
    elif len(results) > 1:
    	log("To many matches found.")
    	sys.exit(5)

    for x in results:
        # Keys:
        # ['episodenumber', 'rating', 'overview', 'dvd_episodenumber', 'dvd_discid', 'combined_episodenumber', 'epimgflag', 'id', 'seasonid', 'seasonnumber', 'writer', 'lastupdated', 'filename', 'absolute_number', 'ratingcount', 'combined_season', 'imdb_id', 'director', 'dvd_chapter', 'dvd_season', 'gueststars', 'seriesid', 'language', 'productioncode', 'firstaired', 'episodename']
        seasno = "%02d" % int(x['seasonnumber'], 0)
        epno = "%02d" % int(x['episodenumber'], 0)
        output = "Series"+d+tvshow+d+"Staffel_"+seasno+d+epno+" - "+x['episodename']
        if args.forceunderscores:
        	output = output.replace (" ", "_")
        print output


if __name__ == "__main__":
    main()
