# state file generated using paraview version 5.13.1
import paraview
import numpy as np
paraview.compatibility.major = 5
paraview.compatibility.minor = 13

#### import the simple module from the paraview
from paraview.simple import *
#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# ----------------------------------------------------------------
# setup the data processing pipelines
# ----------------------------------------------------------------

# create a new 'TS Fluent Reader'
tSFluentReader1 = TSFluentReader(registrationName='TSFluentReader1', Filepath='/home/yl924/Desktop/SailPlane/Mesh/SP_wing_surface_16761386.cas')
tSFluentReader1.BCprefix = ''
tSFluentReader1.Readzonenames = 1

# create a new 'TS Select'
tSSelect1 = TSSelect(registrationName='TSSelect1', Input=tSFluentReader1)
tSSelect1.BlockIndices = [6, 7, 8, 9, 11, 12]

# create a new 'TS Set Wall'
tSSetWall1 = TSSetWall(registrationName='TSSetWall1', Input=tSSelect1)
tSSetWall1.Walltype = 'Wall function'

# create a new 'TS Select'
tSSelect2 = TSSelect(registrationName='TSSelect2', Input=tSSetWall1)
tSSelect2.BlockIndices = [10]

# create a new 'TS Set Wall'
tSSetWall2 = TSSetWall(registrationName='TSSetWall2', Input=tSSelect2)

# create a new 'TS Select'
tSSelect3 = TSSelect(registrationName='TSSelect3', Input=tSSetWall2)
tSSelect3.BlockIndices = [5]

f = open("../bcs.dat","r")
lines = f.readlines() # read boundary condition file
f.close()

# create a new 'TS Set Freestream'
tSSetFreestream1 = TSSetFreestream(registrationName='TSSetFreestream1', Input=tSSelect3)
# Properties modified on tSSetFreestream1
tSSetFreestream1.Machnumber = float(lines[0].split()[-1])
tSSetFreestream1.Staticpressure = float(lines[1].split()[-1])
tSSetFreestream1.Statictemperature = float(lines[2].split()[-1])
alpha = float(lines[3].split()[-1]) * np.pi / 180
tSSetFreestream1.Flowxcomponent = np.cos(alpha)
tSSetFreestream1.Flowzcomponent = np.sin(alpha)

# create a new 'TS Select'
tSSelect4 = TSSelect(registrationName='TSSelect4', Input=tSSetFreestream1)
tSSelect4.BlockIndices = [1]

f = open("../initial_flow.dat", "r")
lines = f.readlines()
f.close()

# create a new 'TS Set Initial Flow'
tSSetInitialFlow1 = TSSetInitialFlow(registrationName='TSSetInitialFlow1', Input=tSSelect4)
tSSetInitialFlow1.Stagnationenthalpy = float(lines[0].split()[-1])
tSSetInitialFlow1.Stagnationpressure = float(lines[1].split()[-1])
V = float(lines[2].split()[-1])
tSSetInitialFlow1.Vx = V * np.cos(alpha)
tSSetInitialFlow1.Vz = V * np.sin(alpha)

# create a new 'TS Select'
tSSelect5 = TSSelect(registrationName='TSSelect5', Input=tSSetInitialFlow1)
tSSelect5.BlockIndices = [1]

# create a new 'TS Set Wall Distance'
tSSetWallDistance1 = TSSetWallDistance(registrationName='TSSetWallDistance1', Input=tSSelect5)
tSSetWallDistance1.Useslipwalls = 0

# create a new 'TS Turbostream Writer'
tSTurbostreamWriter1 = TSTurbostreamWriter(registrationName='TSTurbostreamWriter1', Input=tSSetWallDistance1,
    Outputfilebasename='input_1')

# ----------------------------------------------------------------
tSTurbostreamWriter1.UpdatePipeline()
# ----------------------------------------------------------------


##--------------------------------------------
## You may need to add some code at the end of this python script depending on your usage, eg:
#
## Render all views to see them appears
# RenderAllViews()
#
## Interact with the view, usefull when running from pvpython
# Interact()
#
## Save a screenshot of the active view
# SaveScreenshot("path/to/screenshot.png")
#
## Save a screenshot of a layout (multiple splitted view)
# SaveScreenshot("path/to/screenshot.png", GetLayout())
#
## Save all "Extractors" from the pipeline browser
# SaveExtracts()
#
## Save a animation of the current active view
# SaveAnimation()
#
## Please refer to the documentation of paraview.simple
## https://www.paraview.org/paraview-docs/latest/python/paraview.simple.html
##--------------------------------------------