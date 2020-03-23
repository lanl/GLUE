#!/bin/bash

mkdir den1
#mkdir vel2
for i in *
do
cd $i
cp density1.profile ../den1/$i
#cp density2.profile ../vel2/$i
cd ../
done
