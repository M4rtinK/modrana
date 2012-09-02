#/bin/sh

dbus-send --system --type=method_call --dest=com.nokia.icd /com/nokia/icd com.nokia.icd.connect string:"[ANY]" uint32:0