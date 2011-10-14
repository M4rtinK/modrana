from setuptools import setup,find_packages
import os.path

# try to  read the version file
versionFilePath = 'version.txt'
if os.path.exists(versionFilePath):
  try:
    f = open(self.versionFilePath, 'r')
    versionNumber = f.read()
    f.close()
    # is it really string ?
    versionNumber = str(versionString)
  except Exception, e:
    print("loading version info failed")
    print(e)
else:
  print("version file not found, using default")
  versionNumber = "0.1"

setup (
  name = 'modRana',
  version = versionNumber,

  # just package everything in this folder
  data_files = [('','')],

  # list the main modRana script
  scripts = ['modrana.py'],

  author = 'Martin Kolman',
  author_email = 'modrana@gmail.com',

  summary = 'A flexible GPS navigation system for mobile Linux devices.',
  url = 'http://www.modrana.org',
  license = 'GNU GPLv3',
  long_description= 'Modrana is a flexible GPS navigation system for mobile Linux devices.',

  # could also include long_description, download_url, classifiers, etc.
)