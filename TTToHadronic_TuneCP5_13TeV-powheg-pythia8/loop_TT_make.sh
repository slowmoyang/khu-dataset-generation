#!/bin/bash
echo $0 $1

source /cvmfs/cms.cern.ch/cmsset_default.sh

#export SCRAM_ARCH=slc7_amd64_gcc700

#cmsrel CMSSW_10_6_18

cd /u/user/yewzzang/work/cms_dataset/khu-dataset-generation/CMSSW_10_6_18/src

cmsenv

cd /u/user/yewzzang/work/cms_dataset/khu-dataset-generation/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/



mkdir running_231205/run_$1
cp TT_make.py running_231205/run_$1/TT_make.py
cd running_231205/run_$1
cmsRun TT_make.py outputFile=/d0/scratch/yewzzang/TT_data/test_$1.root
