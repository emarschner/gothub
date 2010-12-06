#!/bin/sh
# Make this change first:
# In map.html, change:
#  var oVal = 0.02//get_link_opacity(link_data.length, LINK_MIN_OPACITY);
# to:
#  var oVal = get_link_opacity(link_data.length, LINK_MIN_OPACITY);
# This will restore old-style line opacity, which works better across the range
# of projects.  Otherwise, would need to do manual scaling. 
time ./mapmatrix.py --projects rails,docrails,rails-i18n,sinatra,perl,parrot,mono,git,progit,node,eventmachine,homebrew --image_dir ~/src/gothub/screenshots/ --style midnight --merge  --month_start 1/2009 --month_end 9/2010 --month_inc 4 --append_overview

