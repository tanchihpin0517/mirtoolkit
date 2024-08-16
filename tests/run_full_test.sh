#!/usr/bin/env bash

versions=("3.8" "3.9" "3.10" "3.11" "3.12")
prefix="_mirtoolkit_test"

for version in "${versions[@]}"; do
    conda create -n ${prefix}${version} python=${version} -y > /dev/null

    if [ "$version" != "3.12" ]; then
        conda install -n ${prefix}${version} mpi4py -y > /dev/null # Required for sheetsage
    fi

    conda run -n ${prefix}${version} --no-capture-output python -m pip install .[test] > /dev/null
    conda run -n ${prefix}${version} --no-capture-output python -m pytest
    r=$?
    conda remove -n ${prefix}${version} --all -y > /dev/null
    if [ $r -ne 0 ]; then
        exit $r
    fi
done
