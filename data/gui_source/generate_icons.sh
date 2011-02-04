#!/bin/bash
icon_ids=`cat icons.svg | grep -o -E 'icon_[0-9A-Za-z_-]*'`

height=88
extension="png"
if [ $1 ];then extension=$1;fi


echo ${icon_ids}

for i in $icon_ids
do
 b=`echo $i | sed s/icon_//`
 echo $b
 inkscape --without-gui --export-plain-svg -f icons.svg -i $i -e icons/${b}.${extension} -h ${height}
done
