# Delphes

## Recipe
### Install
```bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
cmsrel CMSSW_10_6_18
cd CMSSW_10_6_18/src
cmsenv
cd ../..
wget http://cp3.irmp.ucl.ac.be/downloads/Delphes-3.5.0.tar.gz
tar -zxf Delphes-3.5.0.tar.gz
cd ./Delphes-3.5.0/
sed -i 's/c++0x/c++17/g' Makefile
make -j8
```

### Setup
```bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd ./CMSSW_10_6_18/src
cmsenv
cd ../../Delphes-3.5.0/
source ./DelphesEnv.sh
export PATH=${DELPHES_HOME}:${PATH}
cd ..
```

### Test
```bash
DelphesCMSFWLite ./cards/delphes_card_CMS.tcl output.root /u/user/yewzzang/work/cms_dataset/khu-dataset-generation/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/data/test_0.root
```
