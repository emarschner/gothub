#!/bin/bash

RUN_DIR=`echo $(dirname $0)`

. "${RUN_DIR}/crawler_tasks.sh"

repos2contributors
