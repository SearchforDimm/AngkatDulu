#!/bin/bash
# PPP-static satu hari: statis.sh ST DOY KONFIG
st=$1; d=$2; conf=$3; RNX=/home/claude/rtklibexplorer/rtklib/app/consapp/rnx2rtkp/gcc/rnx2rtkp
p=$(ls prod/COD0MGXFIN_2026${d}0000_01D_05M_ORB.SP3 2>/dev/null || ls prod/COD0OPSRAP_2026${d}0000_01D_05M_ORB.SP3)
c=${p/05M_ORB.SP3/30S_CLK.CLK}
$RNX -k $conf -o sta_$st/$st$d.pos obs_$st/${st}${d}0_dengan_fcn.26o obs_$st/${st}${d}0.26n $p $c >/dev/null 2>&1
