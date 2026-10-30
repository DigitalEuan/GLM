#!/bin/sh
# Round 40: predict the open bit at the even white diagonal w = 1420878968 (To Do 46).
# 1. exact patterns of diagonals 99997, 99998 from the automaton (exact settling certificate);
# 2. iterate the proved pattern law F to the diagonals just outside a run-up stretch of length c;
# 3. run the stretch from 6 random fillings for each c and read the pattern after the white.
# Output: r40_bit_prediction.txt.  (EMP: relies on proved laws for steps 1-2; step 3 is the
# run-up hypothesis H9, validated at the known even whites 53207 and 58286 by runup_validate.py.)
set -e
gcc -O3 -o bandfast bandfast.c; gcc -O3 -o patdump patdump.c; gcc -O3 -o fscan fscan.c
gcc -O3 -o localband localband.c
w=1420878968
P=$(./patdump 100000 1 99997 99998 | grep PAT | awk '{print substr($3,9,8)}' | tr '\n' ' ')
set -- $P
./fscan 32 $1 $2 99997 $((w-100002)) $((w-100001)) $((w-30002)) $((w-30001)) $((w-10002)) \
  $((w-10001)) $((w-3002)) $((w-3001)) $((w-1)) $w > fscan_w.txt
{
  echo "patterns of 99997, 99998: $1 $2"; cat fscan_w.txt
  for c in 3000 10000 30000 100000; do
    A=$(grep "PAT $((w-c-2)) " fscan_w.txt | awk '{print $3}')
    B=$(grep "PAT $((w-c-1)) " fscan_w.txt | awk '{print $3}')
    for fs in 0 1 2 3 4 5; do
      echo "c=$c fill=$fs $(./localband 32 $A $B $((c+300)) $fs | grep WHITE)"
    done
  done
  echo "candidates (Round 39): bit 0 -> 93425cac (next white 3340408059, even);"
  echo "                       bit 1 -> 6cbda353 (next white 2107985254, odd: period 64)"
  ./fscan 32 0 6cbda353 $w 2107985253 2107985254 3000000000
} > r40_bit_prediction.txt
cat r40_bit_prediction.txt
