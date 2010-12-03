#!/usr/bin/env python
#
# Example calls:
# ./mapmatrix.py --project git
# ./mapmatrix.py --projects git,ruby
# ./mapmatrix.py --project rails --image_dir ~/src/gothub/screenshots \
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

import os
from optparse import OptionParser
from screenshot import ScreenshotGen
from subprocess import Popen
import time

# Filename extension
EXT = ".png"

# Sleep time to get past ImageMagick issue.
SLEEP_TIME_SEC = 1

# Size of border, presumably in pixels
BORDER = 20


def getMonthArr(s_date, e_date):
    s_date = s_date.split('/')
    s_month = int(s_date[0])
    s_year = int(s_date[1])
    cur_month = s_month
    cur_year = s_year
    e_date = e_date.split('/')
    e_month = int(e_date[0])
    e_year = int(e_date[1])
    retVal = []
    while True:
        end = False
        if cur_month == e_month and cur_year == e_year:
            end = True
        retVal.append((str(cur_month), str(cur_year)))
        cur_month = cur_month + 1
        if cur_month > 12:
            cur_month = 1
            cur_year = cur_year + 1
        if end:
            break

    return retVal



# convert is part of imagemagick.
# +append puts images side-by-side.
def merge_files(dir, img_names, merged_filename, type):
    append_type = None
    if type == 'horizontal':
        append_type = "+append"
    elif type == 'vertical':
        append_type = "-append"
    else:
        raise Exception("Invalid merge_files type: %s" % type)
    args = ["convert"] + img_names + ["-border", str(BORDER), append_type, merged_filename]
    print "merging files (%s): %s" % (type, args)
    os.chdir(dir)
    Popen(args)


def gen_dates(s, dir, project, month_start, month_end,
              cumulative = False, dry = True, merge = False):
    months = getMonthArr(month_start, month_end)
    date_start = months[0][0] + "/1/" + months[0][1]
    query = {}
    query['project'] = project
    img_names = []
    for i in range(0, len(months)-1):
        img_name = project
        if cumulative:
            query['date_start'] = date_start
            query['date_end'] = months[i+1][0] + "/1/" + months[i+1][1]
            img_name += "-c"
        else:
            query['date_start'] = months[i][0] + "/1/" + months[i][1]
            query['date_end'] = months[i+1][0] + "/1/" + months[i+1][1]
        img_name += "-" + months[i][1] + '-' + months[i][0]
        img_names.append(img_name + EXT)
        print "query: %s" % query
        if not dry:
            s.generate(dir, img_name, query)
    if merge:
        merged_filename = project
        if cumulative: merged_filename += "-c"
        merged_filename += EXT
        merge_files(dir, img_names, merged_filename, 'horizontal')
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
        merged_filenames = []
        for p in self.projects:
            if self.options.monthly:
                merged_filename = gen_dates(s, dir, p, month_start, month_end, cumulative, dry, merge)
                merged_filenames.append(merged_filename)
            elif not self.options.dry_run:
                s.generate(self.image_dir, p, {'project': p})
                merged_filenames.append(p + ".png")
        s.selenium.stop()
        if merge and len(self.projects) > 1:
            output_filename = '-'.join(self.projects) + ".png"
            # Should not be necessary, but seem to fix an error.
            time.sleep(SLEEP_TIME_SEC)
            merge_files(dir, merged_filenames, output_filename, 'vertical')

    def parse_args(self):
        opts = OptionParser()
        opts.add_option('--image_dir','-f', type = 'string', 
                           default = None,
                        help = "directory for images")
        opts.add_option("--dry_run", action = "store_true", default = False,
                        help = "dry run, w/no map generation?")
        opts.add_option("--monthly", action = "store_true", default = False,
                        help = "generate one map per month?")
        opts.add_option("--merge", action = "store_true", default = False,
                        help = "merge maps for --monthly?")
        opts.add_option("--cumulative", action = "store_true", default = False,
                        help = "show cumulative maps?")
        opts.add_option("--project", "-p", type = 'string',
                        default = None, help = "project name")
        opts.add_option("--projects", type = 'string',
                        default = None, help = "project names, comma-separated")
        opts.add_option("--month_start", type = 'string',
                        default = None, help = "start month as MM/YYYY")
        opts.add_option("--month_end", type = 'string',
                        default = None, help = "end month as MM/YYYY")
        options, arguments = opts.parse_args()
        
        if options.projects:
             self.projects = options.projects.split(",")
        elif options.project: 
            self.projects = [options.project]
        else:
            raise Exception("Project not specified")

        if options.monthly and not (options.month_start and options.month_end):
            raise Exception("Monthly specified without dates")

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