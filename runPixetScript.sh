#!/bin/sh

cp AdvacamQuadController.py ../Pixet/distrib/_build/latest_debug

cd ../Pixet/distrib/_build/latest_debug

LD_LIBRARY_PATH=~/Projects/Heidelberg_Quads/Pixet/distrib/_build/latest_debug python AdvacamQuadController.py 
