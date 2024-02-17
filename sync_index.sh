#!/bin/bash

cd odrive_sync || exit 1

git pull
git add .
git commit -m "sync"

git push