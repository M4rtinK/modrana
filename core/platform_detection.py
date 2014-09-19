# modRana current-platform detection
import os
import sys

DEFAULT_DEVICE_MODULE_ID = "pc"
DEFAULT_GUI_MODULE_ID = "GTK"

import logging
log = logging.getLogger("core.platform_detection")

def getBestDeviceModuleId():
    log.info("** detecting current device **")

    result = _check()

    if result is not None:
        deviceModuleId = result
    else:
        deviceModuleId = DEFAULT_DEVICE_MODULE_ID # use GTK GUI module as fallback
        log.info("* no known device detected")

    log.info("** selected %s as device module ID **" % deviceModuleId)
    return deviceModuleId


def getBestGUIModuleId():
    return DEFAULT_GUI_MODULE_ID


def _check():
    """
    try to detect current device
    """
    # check CPU architecture
    import subprocess

    proc = subprocess.Popen(['uname', '-m', ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    arch = str(proc.communicate()[0])
    if ("i686" in arch) or ("x86_64" in arch):
        log.info("* PC detected")
        return "pc" # we are most probably on a PC
    if sys.platform == "qnx6":
        log.info("* BlackBerry 10 device detected")
        return "bb10"

    # check procFS
    if os.path.exists("/proc/cpuinfo"):
        f = open("/proc/cpuinfo", "r")
        cpuinfo = f.read()
        f.close()
        if "Nokia RX-51" in cpuinfo: # N900
            log.info("* Nokia N900 detected")
            return "n900"
        # N9 and N950 share the same device module
        elif "Nokia RM-680" in cpuinfo: # N950
            log.info("* Nokia N950 detected")
            return "n9"
        elif "Nokia RM-696" in cpuinfo: # N9
            log.info("* Nokia N9 detected")
            return "n9"
        elif "GTA02" in cpuinfo: # N9
            log.info("* Neo FreeRunner GTA02 detected")
            return "neo"

    # check lsb_release
    try:
        proc = subprocess.Popen(['lsb_release', '-s', '-i'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        distributionId = proc.communicate()[0].decode("utf-8").lower().strip()
        log.info(distributionId)
        # import pdb; pdb.set_trace()
        if distributionId == 'mer':
            # TODO: could be ale Nemo mobile or other Mer based distro,
            # we should probably discern those two in the future
            log.info("* Jolla (or other Mer based device) detected")
            return "jolla"
    except:
        log.exception("running lsb_release during platform detection failed")

    return None


