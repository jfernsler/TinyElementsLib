import os

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_THUMB = os.path.join(THIS_DIR, 'resources', 'placeholder.gif')

# Replace these with the paths to your global library of 2D elements, projects, and the structure of your element subpath below the project
# this needs to be constructed in an OS agnostic way, so use os.path.join
# if you have the follwing:
# GLOBAL_DIR = '.../_Library/_Elements/_2D/'
# turn it into this:
GLOBAL_DIR = os.path.join('...','_Library','_Elements','_2D')

#PROJ_DIR = '.../SHOWS'
PROJ_DIR = os.path.join('...','SHOWS')

# This subpath defines where elements will be stored under the project when copied in
SHOW_ELEMENTS_SUBPATH = os.path.join('assets', '_Elements', '_2D')

# Replace this with a call to your environment variables
SHOW = 'MyShow' #more like... os.environ['SHOW_NAME']

SHOW_DIR = os.path.join(PROJ_DIR, SHOW, SHOW_ELEMENTS_SUBPATH)

# if you have ffmpeg somewhere else.. fix it here
FFMPEG_PATH = 'ffmpeg'