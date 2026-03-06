#!/usr/bin/env fish

# rsyncing from an ffmpegfs can cause some issues, so
# we can force preprocessing all of them before syncing.
# `./preprocess.fish () && tungbou`

set target $argv[1]

find $target -type f \
    | pv -lteb \
    | parallel -j4 'cat {} > /dev/null'
