#!/bin/bash
# =============================================================================
# Filename: calib.sh
# Description:
#   This is the main script running calibration procedures.
#   You may run it or use .py version (recommended).
#   This instance is better for running tests and developing
#   new modules.
# =============================================================================

# for tests:
path_to_config_file="./config/LISNYKY_Moravian-C4-16000.ini"
#path_to_config_file="./config/BIALKOW_Andor-DW432.ini"

# (0) Cleaning & preparing:
mkdir -p ./work ./results/aux &>/dev/null

###################################################################
## testing:
#dir_path="test-data-B"
dir_path="test-data-L"
lst_path=""
test_preplists_skip=0
test_masterbias_skip=0
test_mastercorr_skip=0
test_masterdark_skip=0
test_masterdcorr_skip=0
test_checkflats_skip=0
test_createflats_skip=0
test_calibrateobjects_skip=0

##################################################################
## variables:
list_IN="${dir_path}.lst"
list_d="${dir_path}-d.lst"
list_b="${dir_path}-b.lst"
list_bd="${dir_path}-bd.lst"
list_df="${dir_path}.lst"
list_bf="${dir_path}.lst"
list_bdf="${dir_path}-bdf.lst"
##################################################################

##################################################################
##################################################################
####################### Here pipeline stars ######################
##################################################################
##################################################################

##################################################################
##### () Prepare all needed lists of files:
# Some of these list may not be needed and will be deleted while the program 
# is running. They are created for consistency and testing. 
### TO DO: delete some of these in the future
#
# 
echo -n "Preparing list of files..."
if [ $test_preplists_skip != 1 ]; then
    python3 calib_prep_lists.py -d ${dir_path}
    ## echo $list_IN, $list_d, $list_b
    ## exit
    echo "done."
else
    echo "Section skipped due to testing."
fi
echo ""

##################################################################
##### () Making masterbias file
# 
# 
# 
echo "==========================================================="
echo "=============== CREATING MASTERBIAS FILE =================="
echo "==========================================================="
echo ""

if [ $test_masterbias_skip != 1 ]; then
    python3 mkmasterbias.py -l ${list_IN} -c ${path_to_config_file} -v
else
    echo "Section skipped due to testing."
fi

##################################################################
##### () Subtracting masterbias from other files
# 
# 
# 
echo ""
echo "==========================================================="
echo "==================== BIAS CORRECTION ======================"
echo "==========================================================="
echo ""
if [ $test_mastercorr_skip != 1 ]; then
    echo -n "Applying bias correction..."
    python3 bias_correction.py ${list_IN} ${list_b} ./work/masterbias.fits ${path_to_config_file}
    echo ".done"
    echo "Bias-corrected files written to '${dir_path}'."
else
    echo "Section skipped due to testing."
fi

##################################################################

# () Making masterdark file
echo ""
echo "==========================================================="
echo "=============== CREATING MASTERDARK FILE =================="
echo "==========================================================="
echo ""
if [ $test_masterdark_skip != 1 ]; then
    python3 mkmasterdark.py -l ${list_b} -o masterdark.fits -c ${path_to_config_file} -v
else
    echo "Section skipped due to testing."
fi
## exit

##################################################################
##### () Subtracting masterdark from other files
# Here a masterdark file is created or is read from a library.
# After this the exposure time scaled dark is subtracted from
# flat-fields and object files.
echo ""
echo "==========================================================="
echo "==================== DARK CORRECTION ======================"
echo "==========================================================="
echo ""
if [ $test_masterdcorr_skip != 1 ]; then
    ## echo ${list_b} ${list_bd}
    ## exit
    echo -n "Applying dark correction..."
    python3 dark_correction.py ${list_b} ${list_bd} ./work/masterdark.fits ${path_to_config_file}
    echo ".done"
    echo "Dark-corrected files written to '${dir_path}'."
else
    echo "Section skipped due to testing."
fi
## exit 

##################################################################
##### () Creating masterflats & normalized masterflats
# Here master flats are created as well as the normalized
# masterflats which are later used to calibrate science images.
# All results are stored both in ./work/ as in ,/results/aux/.
# 
echo ""
echo "==========================================================="
echo "================= CREATING MASTERFLATS ===================="
echo "==========================================================="
echo ""
if [ $test_createflats_skip != 1 ]; then
    echo -n "Creating masterflats..."
    python3 mkmasterflats.py ${path_to_config_file} ${list_bd}
    echo ".done"
    echo "Masterflats & normalized masterflats files have been"
    echo "written to './work' & './results/aux'."
else
    echo "Section skipped due to testing."
fi
## exit

##################################################################
##### () Calibrating data
# Here we divide previously prepared scietific data
# by normalized masterflat frames. taking into account the 
# filters band for each frame
# 
echo ""
echo "==========================================================="
echo "==================== CALIBRATING DATA ====================="
echo "==========================================================="
echo ""
if [ $test_calibrateobjects_skip != 1 ]; then
    echo -n "Calibrating scientific data..."
    python3 flat_correction.py ${list_bd} ${list_bdf} ${path_to_config_file}
    echo ".done"
    
else
    echo "Section skipped due to testing."
fi
echo ""

echo "==========================================================="
echo "All calibrated science images are now stored in './results'"
echo "All calibration files are now stored in './results/aux    '"
echo "==========================================================="

echo ""
echo "Quitting."
echo ""

# Exit without errors
exit 0

### END
