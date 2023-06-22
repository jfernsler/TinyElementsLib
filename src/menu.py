import os

# import tinyelements and define the panel settings
from tinyelements import TinyElements_Library

pathToClass='TinyElements_Library' #the full python path to your panel
HRName='Tiny 2D Element Library' #the Human-readable name you want for your panel
regName='JF.NukePanel.ElementLibrary' #the internal registered name for this panel (used for saving and loading layouts)
nukescripts.panels.registerWidgetAsPanel(pathToClass, HRName, regName, True).addToPane(nuke.getPaneFor('Properties.1'))
### End