#!/bin/bash

log="tabata.log"
if ! ./tabata.py 2>>$log; then
    tail -25 $log
fi
