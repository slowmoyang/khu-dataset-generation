# Four top quark production in the all-hadronic channel at \sqrt{s} = 14 TeV

tested on `T3_KR_KNU`, whose OS is `CentOS Linux release 7.9.2009 (Core)`

## Recipes
## generate a gridpack
no need to do this step by yourself if you work on CentOS7

```bash
git clone git@github.com:cms-sw/genproductions.git
cd ./genproductions/bin/MadGraph5_aMCatNLO
NB_CORE=20 ./submit_condor_gridpack_generation.sh  TTTTTo8Q_TuneCP5_14TeV_amcatnlo-pythia8 ../../../data/cards/
```

## event generation
### setup
The gridpack on `T3_KR_KNU` is generated [genproductions](https://github.com/cms-sw/genproductions/blob/200c869/bin/MadGraph5_aMCatNLO/gridpack_generation.sh#L731C23-L731C35) using `CMSSW_12_4_8`

```bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
cmsrel CMSSW_12_4_8
```

### generate events
```bash
cd ./CMSSW_12_4_8
cmsenv
cd -
cmsRun ./TTTTTo8Q_TuneCP5_14TeV_amcatnlo-pythia8_cfg.py maxEvents=1000
```
