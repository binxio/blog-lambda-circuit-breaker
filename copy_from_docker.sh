#!/bin/bash
ID=$(docker create my-lambda /bin/true)
docker cp $ID:/lambda.zip ./dist
