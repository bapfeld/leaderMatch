#!/bin/bash
OS=$(uname -s)

if [[ $OS == 'Linux' ]]; then
    pyinstaller match_app.py \
                --noconfirm \
                --onefile \
                --name LeaderMatch
elif [[ $OS == 'Darwin' ]]; then
    pyinstaller match_app.py \
                --noconfirm \
                --onefile \
                --windowed \
                --name LeaderMatch
fi
