#!/bin/bash
script_dir=$(realpath $(dirname $0))

cd $script_dir/../backend
uv sync
cd ./.venv/bin
rm python*
cp $(readlink -f $(which python3)) python
cp python python3
cp python python3.12