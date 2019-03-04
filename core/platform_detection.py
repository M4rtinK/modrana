# modRana current-platform detection
import os

from core import qrc

DEFAULT_DEVICE_MODULE_ID = "pc"
DEFAULT_GUI_MODULE_ID = "GTK"

import logging
log = logging.getLogger("core.platform_detection")

def get_best_device_module_id():
    log.info("** detecting current device **")

    result = _check()

    if result is not None:
        deviceModuleId = result
    else:
        deviceModuleId = DEFAULT_DEVICE_MODULE_ID # use GTK GUI module as fallback
        log.info("* no known device detected")

    log.info("** selected %s as device module ID **" % deviceModuleId)
    return deviceModuleId


def get_best_gui_module_id():
    return DEFAULT_GUI_MODULE_ID


def _check():
    """Try to detect current device."""

    # TODO: turn platform IDs to proper constants

    # qrc is currently used only on Android, so if we are running with
    # qrc, we are on Android
    if qrc.is_qrc:
        return "android"

    try:
        import platform
        if platform.node() == "Sailfish":
            return "jolla"
    except:
        log.exception("the Python stdlib platform module is apparently unusable on this platform")

    # check CPU architecture
    import subprocess

    proc = subprocess.Popen(['uname', '-m', ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    arch = str(proc.communicate()[0])
    if ("i686" in arch) or ("x86_64" in arch):
        log.info("* PC detected")
        return "pc" # we are most probably on a PC

    # check procFS
    if os.path.exists("/proc/cpuinfo"):
        f = open("/proc/cpuinfo", "r")
        cpuinfo = f.read()
        f.close()
        if "Nokia RX-51" in cpuinfo: # N900
            log.info("* Nokia N900 detected")
            return "n900"

    # check lsb_release
    try:
        proc = subprocess.Popen(['lsb_release', '-s', '-i'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        distribution_id = proc.communicate()[0].decode("utf-8").lower().strip()
        log.info("lsb_release distro id: %s ", distribution_id)
        # import pdb; pdb.set_trace()
        if distribution_id == 'mer':
            # TODO: could be also Nemo mobile or other Mer based distro,
            # we should probably discern those two in the future
            log.info("* Jolla (or other Mer based device) detected")
            return "jolla"
    except:
        log.exception("running lsb_release during platform detection failed")

    return None


