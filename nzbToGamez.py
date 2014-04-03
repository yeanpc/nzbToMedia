#!/usr/bin/env python
#
##############################################################################
### NZBGET POST-PROCESSING SCRIPT                                          ###

# Post-Process to Gamez.
#
# This script sends the download to your automated media management servers.
#
# NOTE: This script requires Python to be installed on your system.

##############################################################################
### OPTIONS                                                                ###

## Gamez

# Gamez script category.
#
# category that gets called for post-processing with Gamez.
#gzCategory=games

# Gamez api key.
#gzapikey=

# Gamez host.
#gzhost=localhost

# Gamez port.
#gzport=8085

# Gamez uses ssl (0, 1).
#
# Set to 1 if using ssl, else set to 0.
#gzssl=0

# Gamez web_root.
#
# set this if using a reverse proxy.
#gzweb_root=

## WakeOnLan

# use WOL (0, 1).
#
# set to 1 to send WOL broadcast to the mac and test the server (e.g. xbmc) on the host and port specified.
#wolwake=0

# WOL MAC
#
# enter the mac address of the system to be woken.
#wolmac=00:01:2e:2D:64:e1

# Set the Host and Port of a server to verify system has woken.
#wolhost=192.168.1.37
#wolport=80

### NZBGET POST-PROCESSING SCRIPT                                          ###
##############################################################################


# Exit codes used by NZBGet
import logging
import os
import sys
from nzbtomedia.autoProcess.autoProcessGames import autoProcessGames
from nzbtomedia.migratecfg import migratecfg
from nzbtomedia.nzbToMediaConfig import config
from nzbtomedia.nzbToMediaUtil import WakeUp, nzbtomedia_configure_logging, get_dirnames

# run migrate to convert old cfg to new style cfg plus fix any cfg missing values/options.
if migratecfg().migrate():
    # check to write settings from nzbGet UI to autoProcessMedia.cfg.
    if os.environ.has_key('NZBOP_SCRIPTDIR'):
        migratecfg().addnzbget()

    nzbtomedia_configure_logging(config.LOG_FILE)
    Logger = logging.getLogger(__name__)
    Logger.info("====================")  # Seperate old from new log
    Logger.info("nzbToGamez %s", config.NZBTOMEDIA_VERSION)

    Logger.info("MAIN: Loading config from %s", config.CONFIG_FILE)
else:
    sys.exit(-1)

# gamez category
gzCategory = (config().get("Gamez", "gzCategory")).split(',')  # gamez

WakeUp()

# NZBGet V11+
# Check if the script is called from nzbget 11.0 or later
if os.environ.has_key('NZBOP_SCRIPTDIR') and not os.environ['NZBOP_VERSION'][0:5] < '11.0':
    Logger.info("MAIN: Script triggered from NZBGet (11.0 or later).")

    # Check nzbget.conf options
    status = 0

    if os.environ['NZBOP_UNPACK'] != 'yes':
        Logger.error("MAIN: Please enable option \"Unpack\" in nzbget configuration file, exiting")
        sys.exit(config.NZBGET_POSTPROCESS_ERROR)

    # Check par status
    if os.environ['NZBPP_PARSTATUS'] == '3':
        Logger.warning("MAIN: Par-check successful, but Par-repair disabled, exiting")
        Logger.info("MAIN: Please check your Par-repair settings for future downloads.")
        sys.exit(config.NZBGET_POSTPROCESS_NONE)

    if os.environ['NZBPP_PARSTATUS'] == '1' or os.environ['NZBPP_PARSTATUS'] == '4':
        Logger.warning("MAIN: Par-repair failed, setting status \"failed\"")
        status = 1

    # Check unpack status
    if os.environ['NZBPP_UNPACKSTATUS'] == '1':
        Logger.warning("MAIN: Unpack failed, setting status \"failed\"")
        status = 1

    if os.environ['NZBPP_UNPACKSTATUS'] == '0' and os.environ['NZBPP_PARSTATUS'] == '0':
        # Unpack was skipped due to nzb-file properties or due to errors during par-check

        if os.environ['NZBPP_HEALTH'] < 1000:
            Logger.warning("MAIN: Download health is compromised and Par-check/repair disabled or no .par2 files found. Setting status \"failed\"")
            Logger.info("MAIN: Please check your Par-check/repair settings for future downloads.")
            status = 1

        else:
            Logger.info("MAIN: Par-check/repair disabled or no .par2 files found, and Unpack not required. Health is ok so handle as though download successful")
            Logger.info("MAIN: Please check your Par-check/repair settings for future downloads.")

    # Check if destination directory exists (important for reprocessing of history items)
    if not os.path.isdir(os.environ['NZBPP_DIRECTORY']):
        Logger.error("MAIN: Nothing to post-process: destination directory %s doesn't exist. Setting status \"failed\"", os.environ['NZBPP_DIRECTORY'])
        status = 1

    # All checks done, now launching the script.
    Logger.info("MAIN: Script triggered from NZBGet, starting autoProcessGames...")
    result = autoProcessGames().process(os.environ['NZBPP_DIRECTORY'], os.environ['NZBPP_NZBNAME'], status)
# SABnzbd Pre 0.7.17
elif len(sys.argv) == config.SABNZB_NO_OF_ARGUMENTS:
    # SABnzbd argv:
    # 1 The final directory of the job (full path)
    # 2 The original name of the NZB file
    # 3 Clean version of the job name (no path info and ".nzb" removed)
    # 4 Indexer's report number (if supported)
    # 5 User-defined category
    # 6 Group that the NZB was posted in e.g. alt.binaries.x
    # 7 Status of post processing. 0 = OK, 1=failed verification, 2=failed unpack, 3=1+2
    Logger.info("MAIN: Script triggered from SABnzbd, starting autoProcessGames...")
    result = autoProcessGames().process(sys.argv[1], sys.argv[3], sys.argv[7])
# SABnzbd 0.7.17+
elif len(sys.argv) >= config.SABNZB_0717_NO_OF_ARGUMENTS:
    # SABnzbd argv:
    # 1 The final directory of the job (full path)
    # 2 The original name of the NZB file
    # 3 Clean version of the job name (no path info and ".nzb" removed)
    # 4 Indexer's report number (if supported)
    # 5 User-defined category
    # 6 Group that the NZB was posted in e.g. alt.binaries.x
    # 7 Status of post processing. 0 = OK, 1=failed verification, 2=failed unpack, 3=1+2
    # 8 Failure URL
    Logger.info("MAIN: Script triggered from SABnzbd 0.7.17+, starting autoProcessGames...")
    result = autoProcessGames().process(sys.argv[1], sys.argv[3], sys.argv[7])
else:
    result = 0
    Logger.warn("MAIN: Invalid number of arguments received from client. Exiting")
    Logger.info("MAIN: Running autoProcessGames as a manual run...")

    for dirName in get_dirnames("Gamez", gzCategory[0]):
        Logger.info("MAIN: Calling Gamez to post-process: %s", dirName)
        result = autoProcessGames().process(dirName, dirName, 0)
        if result != 0: break

if result == 0:
    Logger.info("MAIN: The autoProcessGames script completed successfully.")
    if os.environ.has_key('NZBOP_SCRIPTDIR'): # return code for nzbget v11
        sys.exit(config.NZBGET_POSTPROCESS_SUCCESS)
else:
    Logger.info("MAIN: A problem was reported in the autoProcessGames script.")
    if os.environ.has_key('NZBOP_SCRIPTDIR'): # return code for nzbget v11
        sys.exit(config.NZBGET_POSTPROCESS_ERROR)
