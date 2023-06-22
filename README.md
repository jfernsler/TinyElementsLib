# Tiny Elements Library
Gives you quick access to element you have within nuke.

Store you elements as image squences in a logical directory structure such as:

* Elements
    * Fire
        * fire_01
            * fire_01.%04d.exr
        * fire_02
            * fire_02.%04d.exr
    * Smoke
    * ...

Adjust the globals.py file to point to this directory and the tool will list out all of your elements in a nuke panel and give you options for importing. 

There is thumbnail generation using ffmpeg as well if you have that installed. Thumbnails will be generated to a maximum of 100 frames in duration selected evenly thorughout any sequence longer than 100 frames. 

There is also an option to add additional metadata to your elements by identifying the 'source' location of the element. This allows you to import multiple options all sourcing from the same location so you can easily sample a variety. 

enjoy.