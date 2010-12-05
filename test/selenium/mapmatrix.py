#!/usr/bin/env python
#
# Example calls:
# ./mapmatrix.py --projects git
# ./mapmatrix.py --projects git,ruby
# ./mapmatrix.py --projects rails --image_dir ~/src/gothub/screenshots \
#                --monthly --month_start 1/2008 --month_end 12/2010 \
#                --cumulative
#
# To use the --merge option, which combines files into one, make sure that
# ImageMagick is installed.
#
# On OS X, with homebrew installed:
#  brew install imagemagick
#
# Projects of interest:
# rails, homebrew, dotfiles, git, perl, node, mono, cucumber, docrails, progit
# Eli's suggestions:
# what's with system-automation projects & the pacific northwest?
# puppet, cookbooks, chef, capistrano, diaspora, facebooker
#
# Projects rendered together:
# rails, docrails, rails-i18n, sinatra, perl, parrot, mono, git, progit, node, eventmachine


import os
from optparse import OptionParser
from screenshot import ScreenshotGen
from subprocess import Popen
import time
from math import floor

# Filename extension
EXT = ".png"

# Sleep time to get past ImageMagick issue.
SLEEP_TIME_SEC = 2.0

# Size of border in pixels.
BORDER_HORIZONTAL = 60
BORDER_VERTICAL = 10

# See web/static/map.html; colors match ocean color values.
DEF_STYLE = 'midnight'
STYLES = {
    'original': {'bgcolor': "#abbcc9"},
    'midnight': {'bgcolor': "#021019"},
    'blue': {'bgcolor': "#ffffff"}
}

def month_align(month, month_inc):
    # month is a number in [1..12], round to nearest month_inc
    return int(floor(((month - 1) / month_inc)) * month_inc) + 1

def getDateArr(month_inc, s_date, e_date):
    s_date = s_date.split('/')
    s_month = int(s_date[0])
    s_month = month_align(s_month, month_inc)
    s_year = int(s_date[1])
    cur_month = s_month
    cur_year = s_year
    e_date = e_date.split('/')
    e_month = int(e_date[0])
    e_month = month_align(e_month, month_inc)
    e_year = int(e_date[1])
    retVal = []
    while True:
        end = False
        if cur_month >= e_month and cur_year >= e_year:
            end = True
        retVal.append((str(cur_month), str(cur_year)))
        cur_month += month_inc
        if cur_month > 12:
            cur_month = 1
            cur_year = cur_year + 1
        if end:
            break

    return retVal


# convert is part of imagemagick.
# +append puts images side-by-side.
def merge_files(dir, img_names, merged_filename, type, style):
    append_type = None
    border_val = None
    if type == 'horizontal':
        append_type = "+append"
        border_val = BORDER_HORIZONTAL
    elif type == 'vertical':
        append_type = "-append"
        border_val = BORDER_VERTICAL
    else:
        raise Exception("Invalid merge_files type: %s" % type)
    args = ["convert"] + img_names
    args += ["-bordercolor", STYLES[style]['bgcolor']]
    args += ["-border", str(border_val)]
    args += [append_type, merged_filename]
    print "merging files (%s): %s" % (type, args)
    os.chdir(dir)
    Popen(args)

def gen_dates(s, dir, project, month_start, month_end,
              cumulative = False, dry = True, merge = False,
              month_inc = None, append_overview = None, query_base = None):
    # note: query should include a style field
    date_ranges = getDateArr(month_inc, month_start, month_end)
    date_start = date_ranges[0][0] + "/1/" + date_ranges[0][1]
    date_end = date_ranges[-1][0] + "/1/" + date_ranges[-1][1]
    query = query_base.copy()
    img_names = []
    for i in range(0, len(date_ranges)-1):
        img_name = project
        if cumulative:
            query['date_start'] = date_start
            query['date_end'] = date_ranges[i+1][0] + "/1/" + date_ranges[i+1][1]
            img_name += "-c"
        else:
            query['date_start'] = date_ranges[i][0] + "/1/" + date_ranges[i][1]
            query['date_end'] = date_ranges[i+1][0] + "/1/" + date_ranges[i+1][1]
        img_name += "-" + date_ranges[i][1] + '-' + date_ranges[i][0]
        img_names.append(img_name + EXT)
        print "query: %s" % query
        if not dry:
            s.generate(dir, img_name, query)
    if append_overview:
        filename = project + '-overview'
        query_in = query.copy()
        query_in.update({'date_start': date_start, 'date_end': date_end})
        s.generate(dir, filename, query_in)
        img_names.append(filename + EXT)
    if merge:
        merged_filename = project
        if cumulative: merged_filename += "-c"
        merged_filename += EXT
        merge_files(dir, img_names, merged_filename, 'horizontal', query_base['style'])
        return merged_filename
    else:
        return None


class MapMatrix:

    def __init__(self):
        self.parse_args()
        s = ScreenshotGen()
        month_start = self.options.month_start
        month_end = self.options.month_end
        cumulative = self.options.cumulative
        dir = self.image_dir
        dry = self.options.dry_run
        merge = self.options.merge
        style = self.options.style
        merged_filenames = []
        append_overview = self.options.append_overview
        month_inc = self.options.month_inc
        for p in self.projects:
            query_base = {'project': p, 'style': style}
            if type:
                merged_filename = gen_dates(s, dir, p, month_start, month_end, cumulative, dry, merge, month_inc, append_overview, query_base)
                merged_filenames.append(merged_filename)
            elif not self.options.dry_run:
                s.generate(self.image_dir, p, query_base)
                merged_filenames.append(p + EXT)
        s.selenium.stop()
        if merge and len(self.projects) > 1:
            output_filename = '-'.join(self.projects) + EXT
            # Should not be necessary, but seem to fix an error.
            time.sleep(SLEEP_TIME_SEC)
            merge_files(dir, merged_filenames, output_filename, 'vertical', style)

    def parse_args(self):
        opts = OptionParser()
        opts.add_option('--image_dir','-f', type = 'string', 
                           default = None,
                        help = "directory for images")
        opts.add_option("--dry_run", action = "store_true", default = False,
                        help = "dry run, w/no map generation?")
        opts.add_option("--month_inc", default = None, type = 'int',
                        help = "monthly increment?  must divide into 12.")
        opts.add_option("--merge", action = "store_true", default = False,
                        help = "merge maps for --month_inc?")
        opts.add_option("--cumulative", action = "store_true", default = False,
                        help = "show cumulative maps?")
        opts.add_option("--append_overview", action = "store_true", default = False,
                        help = "add cumulative overview for each project")
        opts.add_option("--style", type = 'string',
                        default = DEF_STYLE,
                        help = "map style: [" + ' '.join(STYLES.keys()) + ']')
        opts.add_option("--projects", type = 'string',
                        default = None, help = "project names, comma-separated")
        opts.add_option("--month_start", type = 'string',
                        default = None, help = "start month as MM/YYYY")
        opts.add_option("--month_end", type = 'string',
                        default = None, help = "end month as MM/YYYY")
        options, arguments = opts.parse_args()
        
        if options.projects:
             self.projects = options.projects.split(",")
        else:
            raise Exception("No projects specified")

        if (options.month_inc and
            not (options.month_start and options.month_end)):
            raise Exception("Month increment specified without dates")
        if (options.month_inc and
            options.month_inc not in [1, 2, 3, 4, 6]):
            raise Exception("Month increment doesn't divide into 12 - not sure what to do")

        if not options.image_dir:
            self.image_dir = os.path.join(os.path.expanduser('~'), "screenshots")
            if not os.path.isdir(self.image_dir):
                os.mkdir(self.image_dir)
                print "created image dir: %s" % self.image_dir
            else:
                print "writing files to existing dir: %s" % self.image_dir
        else:
            self.image_dir = options.image_dir

        self.options = options


if __name__ == "__main__":
    MapMatrix()
