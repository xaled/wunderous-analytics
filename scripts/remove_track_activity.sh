#!/bin/bash

echo_and_run() { echo "$@" ; "$@" ; }

echo_and_run systemctl stop track_activity.service
echo_and_run systemctl disable track_activity.service
echo_and_run systemctl daemon-reload
echo_and_run systemctl reset-failed