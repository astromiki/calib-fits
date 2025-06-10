# 
# 
# 
# =============================================================================
# Filename: calib.py
# Description:
#   ff
#   
#   
#   
# =============================================================================


# (0) Cleaning & preparing:




# () Prepare all needed lists of files:
dir_path = "test-data-1-B"
lst_path = ""

python3 calib_prep_lists.py -d dir_path






exit()

# () Making masterbias file
python3 mkmasterbias.py -l test-data-1-B.cat -c config/BIALKOW_Andor-DW432.ini




# () Subtracting masterbias from other files




exit()







python3 bias_correction.py test_Bialkow_1.cat masterbias.fits 


# (3)



# (4) 



# (5)



# (6) 



# (7) 



# (8)



