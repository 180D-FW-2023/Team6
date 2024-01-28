#!/bin/bash

parec --rate 48000 --format s32le --channels 1 | \
    sox -t raw -r 48000 -b 32 -e signed-integer -c 1 - -t wav - | \
    aubioonset --verbose -