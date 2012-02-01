#!/usr/bin/env bash

echo Ordinary upload. Expecting 200
curl -X POST -d 'label=tab1' -d 'composer=Radiohead' -d 'title=Karma Police'
-d 'notation=tab' -d 'text=foobar'

echo Missing composer field. Expecting 500
curl -X POST -d 'label=tab1' -d 'title=Karma Police' -d 'notation=tab' 
-d 'text=foobar'

echo No XOR field is specified. Expecting 500
curl -X POST -d 'label=tab1' -d 'composer=Radiohead' -d 'title=Karma Police'
-d 'notation=tab'

echo Multiple XOR fields specified. Expecting 500
curl -X POST -d 'label=tab1' -d 'composer=Radiohead' -d 'title=Karma Police'
-d 'notation=tab' -d 'text=foobar' -d 'url=http://google.com'

echo Invalid file specified
