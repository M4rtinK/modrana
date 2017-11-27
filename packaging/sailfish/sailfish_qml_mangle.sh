#!/bin/bash

echo "* mangling source for Sailfish"

export PATH_TO_SOURCE=$1

# make sure the PWD is consistent even if the script is called
# from a different directory
#cd "$(dirname "$0")"

pwd

## change Universal Component import to relative imports
## as the Sailfish QML launcher is not able to support
## adding custom import paths and using a custom C++ loader
## doesn't seem like a good idea for othervise
## pure Python/QML application

qt5_qml_path="${PATH_TO_SOURCE}/modules/gui_modules/gui_qt5/qml"
qt5_qml_path_relative=
UC_silica_path="${qt5_qml_path}/universal_components/silica/UC"
UC_silica_path_relative="../modules/gui_modules/gui_qt5/qml/universal_components/silica/UC"

## move the qml folder to future install folder top-level
mv $qt5_qml_path ${PATH_TO_SOURCE}

## move the UC Silica module to the QML folder because #unlike qmlscene, the
## Sailfish QML launcher does not support appending additional import paths
mv ${PATH_TO_SOURCE}/qml/universal_components/silica/UC ${PATH_TO_SOURCE}/qml/UC
## remove the other UC backends that are not used on Sailfish OS
rm -rf ${PATH_TO_SOURCE}/qml/universal_components/

## replace proper module imports with directory-relative ones

## thanks to sailfish-qml I have been able to learn all these nice
## bash & sed commands :)
function replace_import {
    patern1=${PATH_TO_SOURCE}/qml/modrana_components/
    patern2=${PATH_TO_SOURCE}/qml/backend/
    patern3=${PATH_TO_SOURCE}/qml/sailfish_specific/
    patern4=${PATH_TO_SOURCE}/qml/pinchmap/
    patern5=${PATH_TO_SOURCE}/qml/map_components/
    if [[ $1 = $patern1* ]] || [[ $1 = $patern2* ]] || [[ $1 = $patern3* ]] || [[ $1 = $patern4* ]] || [[ $1 = $patern5* ]]
    then
        sed -i 's/import UC 1\.0/import "\..\/UC"/g' $1
    else
        sed -i 's/import UC 1\.0/import "\.\/UC"/g' $1
    fi

}
export -f replace_import

find ${PATH_TO_SOURCE}/qml -type f -exec bash -c 'replace_import "$0"' {} \;

## tell the main QML script the platform id so that we don't have to run
## platform detection
sed -i 's/property string \_PLATFORM\_ID\_/property string \_PLATFORM\_ID\_ \: "jolla"/g' ${PATH_TO_SOURCE}/qml/main.qml

## also, the sailfish-qml launcher, in its infinite wisdom, sets PWD to /home/nemo.......
## so we have to account for this (why oh why we need to do such hacks...)    
sed -i 's/property string \_PYTHON\_IMPORT\_PATH\_/property string \_PYTHON\_IMPORT\_PATH\_ \: "\/usr\/share\/harbour-modrana"/g' ${PATH_TO_SOURCE}/qml/main.qml

## furthermore the inflexible Sailfish QML launcher needs the app structured like this:
## /usr/share/harbour-<app name>/qml/harbour-<app name>.qml
## so we need to rename the sensibly named main.qml to harbour-modrana.qml
mv ${PATH_TO_SOURCE}/qml/main.qml ${PATH_TO_SOURCE}/qml/harbour-modrana.qml


