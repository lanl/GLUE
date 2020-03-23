#!/bin/bash
lu=3.73 # angrstom
co=0.2478 # conversion factor

for i in {1..1000}
do
lz=( $(shuf -i 10-206 -n 1))  # pore width range in lattice units (
tm=( $(shuf -i 300-400 -n 1)) # temperature range K
dc=( $(shuf -i 10-300 -n 1))
lz2=$(echo $lz $lu | awk '{printf "%4.3f\n",$1*$2}')
nc=$(echo $lz2 $dc $co | awk '{printf "%.0f\n",$1*$2*$3}')
mkdir $lz-$tm-$nc

cp ./input $lz-$tm-$nc
cp ./script $lz-$tm-$nc
cd $lz-$tm-$nc

sed -i -e "s/aaa/$lz/g" input
sed -i -e "s/bbb/$tm/g" input
sed -i -e "s/ccc/$nc/g" input
sed -i -e "s/zzz/$i/g" script
sbatch script
cd ../
done
