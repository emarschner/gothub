#!/bin/sh
ONE=followers_link_dist
TWO=followers_asym_div_dist_reordered
THREE=followers_act-exp-div_dist

~/src/pv_export/pv_export.py --html matrix_blank.html -v matrix.js -d ${ONE}.js --js "jquery.min.js params_link.js" -o ${ONE}.pdf

~/src/pv_export/pv_export.py --html matrix_blank.html -v matrix.js -d ${TWO}.js --js "jquery.min.js params_asym.js" -o ${TWO}.pdf

~/src/pv_export/pv_export.py --html matrix_blank.html -v matrix.js -d ${THREE}.js --js "jquery.min.js params_act-vs-exp.js" -o ${THREE}.pdf

