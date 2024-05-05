# Four top quark production in the all-hadronic channel at \sqrt{s} = 14 TeV

## Recipes
### generate a gridpack
```bash
git clone git@github.com:cms-sw/genproductions.git
cd ./genproductions/bin/MadGraph5_aMCatNLO
NB_CORE=20 ./submit_condor_gridpack_generation.sh  TTTTTo8Q_TuneCP5_14TeV_amcatnlo-pythia8 ../../../data/cards/
```

### generate events
```bash
cmsRun ./TTTTTo8Q_TuneCP5_14TeV_amcatnlo-pythia8_cfg.py maxEvents=1000
```
