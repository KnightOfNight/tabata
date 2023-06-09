#!/bin/bash

log="tabata.log"
if ! python3 tabata.py 2>>$log; then
    tail -25 $log
fi
