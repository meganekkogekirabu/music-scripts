#!/usr/bin/env fish

set meta "m3u|m3u8|cue|nfo|xgeq"
set lrc lrc
set all "\.($meta|$lrc)\$"

echo "deleting lyrics and tracklists..."

set unwanted (find | grep -Pi $all)

if [ (count unwanted) = 0 ]
    echo "none found"
else
    echo $unwanted | xargs -p rm -f
end

echo "deleting empty folders..."

find -type d -empty | xargs -p rm -rf
