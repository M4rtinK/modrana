#!/bin/sh
for png in `find $1 -name "*.png"`;
do
 echo "optipng $png"
 optipng "$png"
done;
