from setuptools import setup
import os.path
import os

# try to  read the version file
versionFilePath = 'version.txt'
if os.path.exists(versionFilePath):
  try:
    f = open(versionFilePath, 'r')
    versionNumber = f.read()
    f.close()
    # is it really string ?
    versionNumber = str(versionNumber)
    versionNumber = versionNumber[1:]
  except Exception, e:
    print("loading version info failed")
    print(e)
else:
  print("version file not found, using default")
  versionNumber = "0.1"

# generate data files tree
data_files = []
for pathTuple in os.walk(''):
  for filename in pathTuple[2]:
    data_files.append( ('modrana', os.path.join(pathTuple[0], filename)) )
  
dist = setup (
  name = 'modRana',
  version = versionNumber,

  # just package everything in this folder
  data_files = data_files,

  # list the main modRana script
  scripts = ['modrana'],

  author = 'Martin Kolman',
  author_email = 'modrana@gmail.com',

  description = 'A flexible GPS navigation system for mobile Linux devices.',
  url = 'http://www.modrana.org',
  license = 'GNU GPLv3',
  long_description= 'Modrana is a flexible GPS navigation system for mobile Linux devices.',

  # could also include long_description, download_url, classifiers, etc.
)

installCmd = dist.get_command_obj(command="install_data")
installdir = installCmd.install_dir
installroot = installCmd.root

if not installroot:
    installroot = ""

if installdir:
    installdir = os.path.join(os.path.sep,
        installdir.replace(installroot, ""))
