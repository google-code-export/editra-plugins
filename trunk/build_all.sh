#!/bin/bash

# Build Script for automating the building of all the plugin projects into
# Python Eggs.

# Variables
CWD=$(pwd)
EXPATH=$(dirname $0)
VERBOSE=0

# Make output pretty
BLUE="[34;01m"
CYAN="[36;01m"
GREEN="[32;01m"
RED="[31;01m"
YELLOW="[33;01m"
OFF="[0m"

### Helper Functions ###
print_help () {
    echo "Editra Plugins Build Script"
    echo "Type 'build_all.sh [hv]' to run a build command"
    echo ""
    echo "Available Options:"
    echo "  -h      Print This help message"
    echo "  -v      Verbose build information"
    echo ""
}

# Parse command line args and set associated params
while getopts "hv" flag
do
    if [[ "$flag" == "v" ]]; then
        VERBOSE=1
    elif [[ "$flag" == "h" ]]; then
        print_help
        exit
    else
        continue
    fi
done

# Commands
if [ $VERBOSE -ne 0 ]; then
    BUILD="setup.py bdist_egg --dist-dir=../."
else
    BUILD="setup.py --quiet bdist_egg --dist-dir=../."
fi

## Check if both python 2.4 and 2.5 are available ##
python2.5 -V 2>/dev/null
if [ $? -eq 0 ]; then
   PY25="python2.5"
fi

python2.4 -V 2>/dev/null
if [ $? -eq 0 ]; then
    PY24="python2.4"
fi

# Abort if no suitable python is found
if [[ -z "$PY25" && -z "$PY24" ]]; then
    echo "${RED}!!${OFF} Neither Python 2.4 or 2.5 could be found ${RED}!!${OFF}"
    echo "${RED}!!${OFF} Aborting build ${RED}!!${OFF}"
    exit
fi

#### Do the Builds ####
echo ""
echo "${YELLOW}**${OFF} Enumerating all plugins... ${YELLOW}**${OFF} "
echo ""

for plugin in $(ls); do
    if [ -d "$plugin" ]; then
        echo "${GREEN}Building${OFF} $plugin ...";
        cd $plugin
        if [ -n "$PY25" ]; then
            echo "${CYAN}Python2.5${OFF} Building..";
            `$PY25 $BUILD`
            echo "${CYAN}Python2.5${OFF} Build finished"
        fi
        if [ -n "$PY24" ]; then
            echo "${CYAN}Python2.4${OFF} Building..";
            `$PY24 $BUILD`
            echo "${CYAN}Python2.4${OFF} Build finished"
        fi
        cd ..
        echo ""
    fi
done

echo ""
echo "${YELLOW}**${OFF} Finished Building all plugins ${YELLOW}**${OFF}"
echo ""

