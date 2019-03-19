from __future__ import with_statement
import os
import shutil
import xml.etree.ElementTree as ET
import math
import re
import platform
import sys
from shutil import copyfile


def check_open (fileName, mode):
    try:
        fileOpen = open(fileName,mode)
    except (OSError,IOError):
        print( "Error, Unable to open file! Please check that the following file exists and is not already open :"+fileName)
        raw_input("Press enter to continue") 
        exit()
    return fileOpen

def write_sim_input (writeFileName, readFileName,numLinesRead):
    readFile = check_open(readFileName,'r')
    writeFile = check_open(writeFileName,'w')
    writeFile.write('<?xml version="1.0" encoding="ISO-8859-1"?>'+'\n')
    writeFile.write('<table mapped_size="'+str(int(numLinesRead-2))+'" allowed_error="0.1">'+'\n')
    numLines = 0
    for line in readFile:
        if(numLines>1):
            writeFile.write(line)
        numLines=numLines+1
    writeFile.write('</table>')
    readFile.close()
    writeFile.close()


def mapFluidToSolid (fluidSurfs,fluidBaseName,resultCorr,tag,solidFileName):
    count = 0
    writeFile = open(solidFileName,'w').close()
    for j in xrange(0,len(fluidSurfs)):
        fluidFileName = fluidBaseName+'_'+resultCorr+"_"+fluidSurfs[j]+tag
        readFile=check_open(fluidFileName,'r')
        writeFile=check_open(solidFileName,'a')
        for line in readFile:
            words=line.split()    
            try:
                float(words[0])
            except ValueError:
                continue    
            writeFile.write(line)
            #writeFile.write("\n")
            count=count+1
        writeFile.close()
    writeFile = check_open(solidFileName,'a')
    writeFile.write('</table>')
    writeFile.close()
    line = '<table mapped_size="'+str(int(count))+'" allowed_error="1">'+'\n'
    insert(solidFileName,line)
    line = '<?xml version="1.0" encoding="ISO-8859-1"?>'+'\n'
    insert (solidFileName,line)


def mapSolidToFluid (solidSurfs,solidBaseName,tag,fluidFileName):
    count = 0
    writeFile = open(fluidFileName,'w').close()
    for j in xrange(0,len(solidSurfs)):
        solidFileName = solidBaseName+'_'+solidSurfs[j]+tag
        readFile=check_open(solidFileName,'r')
        writeFile=check_open(fluidFileName,'a')
        for line in readFile:
            words=line.split()    
            try:
                float(words[0])
            except ValueError:
                continue    
            writeFile.write(line)
            #writeFile.write("\n")
            count=count+1
        writeFile.close()
    writeFile = check_open(fluidFileName,'a')
    writeFile.write('</table>')
    writeFile.close()
    line = '<table mapped_size="'+str(int(count))+'" allowed_error="1">'+'\n'
    insert(fluidFileName,line)
    line = '<?xml version="1.0" encoding="ISO-8859-1"?>'+'\n'
    insert (fluidFileName,line)

def insert(originalfile,string):
    with open(originalfile,'r') as f:
        with open('newfile.txt','w') as f2: 
            f2.write(string)
            f2.write(f.read())
    f.close()
    f2.close()
    os.remove(originalfile)
    os.rename('newfile.txt',originalfile)

def check_copyfile (fileOutName, fileOutName_Old):
    try:
        copyfile(fileOutName,fileOutName_Old)
    except (IOError):
        return

            
setupFileName = "setup.txt"

##if (len(sys.argv)!=3):
##    print "Error:Incorrect number of arguments. Provide both fluid and solid project names"
##    print 'EG. python pistonCoolingSimulation.py "fluid_model.spro" "solid_model.spro"'
##    raw_input("Press enter to continue") 
##    exit()

##fluidSpro = sys.argv[1]
##solidSpro = sys.argv[2]


fluidSurfs=[]
solidSurfs=[]
errors=[]

setupFile = check_open(setupFileName,'r')
for line in setupFile:
    words=line.split()
    if len(words)==0:
        continue
    if words[0]=="#":
        continue
    if words[0]=="simerics_path":
        words.pop(0)
        plString = " ".join(words)
        simPath='"'+plString+'"'+" -run "
    if words[0]=="fluid_model":
        fluidSpro = (words[1])
    if words[0]=="solid_model":
        solidSpro = (words[1])
    if words[0]=="fluid_surfaces":
        for i in xrange(1,len(words)):
            fluidSurfs.append((words[i]))
    if words[0]=="solid_surfaces":
        for i in xrange(1,len(words)):
            solidSurfs.append((words[i]))
    if words[0]=="number_cycles":
        numCycles = int(words[1])
    if words[0]=="restart_option":
        restartOption = (words[1])
    if words[0]=="restart_time_step":
        if(len(words)>1):
            restartTimeStep = int(words[1])
        else:
            restartTimeStep = 1e12

setupFile.close()

name = fluidSpro.split(".sp")
fluidBaseName = name[0]
name = solidSpro.split(".sp")
solidBaseName = name[0]

fluidSproCheck = check_open(fluidSpro,'r')
fluidSproCheck.close()

solidSproCheck = check_open(solidSpro,'r')
solidSproCheck.close()

if (restartOption!="yes" and restartOption!="no" and restartOption!="map" and restartOption!="mapstart"):
    errors.append('Provide either yes (to re-start with fluid), map (to re-start with solid), mapstart (to start with solid without existing solid result) or no for restart option!')
if ((restartOption=="yes" or restartOption=="map" or restartOption=="mapstart")   and restartTimeStep == 1e12):
    errors.append('Please provide time-step to restart from. Result must have been saved at this time-step.')

if(len(errors)>0):
    for i in xrange(0,len(errors)):
        print (errors[i]+"\n")
    print ("Please correct setup file errors above and submit again.")
    raw_input("Press enter to continue") 
    exit() 

tree = ET.parse(fluidSpro)
root = tree.getroot()

#### testing only
##monitorFile = open("monitor.txt",'w')
##monitorFile.close()


for module in root.getiterator('module'):
        if (module.get('type')=="share"):
            interval = int(module.get('cycle_computation_interval'))

for i in xrange(0,numCycles):

    if (restartOption!="no"):
        initNum=restartTimeStep
        restrtStr = str(initNum)
        restrtCorr = restrtStr.zfill(4)
    else:
        initNum=0
    if (restartOption!="map" and restartOption!="mapstart"):    
        resultNum = int(initNum+(i+1)*interval)
        resultStr = str(resultNum)
        resultCorr = resultStr.zfill(4)
    else:
        resultNum = int(initNum+(i)*interval)
        resultStr = str(resultNum)
        resultCorr = resultStr.zfill(4)
##    resultStr = str(interval)
##    resultCorr = resultStr.zfill(4)
    
    if (i==0 and restartOption=="no"):
        fluidRun = simPath+ fluidSpro
        solidRun = simPath+ solidSpro
    elif(i==0 and restartOption=="yes"):
        fluidRun = simPath+ fluidBaseName+'_'+restrtCorr+".sres"
        solidRun = simPath+ solidBaseName+".sres"
    elif(i==0 and restartOption=="map"):
        solidRun = simPath+ solidBaseName+".sres"
    elif(i==0 and restartOption=="mapstart"):
        solidRun = simPath+ solidBaseName+".spro"
    else:
##        fluidRun = simPath+ fluidSpro+' '+ fluidBaseName+'_'+resultCorrPrev+".sres"
        fluidRun = simPath+ fluidBaseName+'_'+resultCorrPrev+".sres"
        solidRun = simPath+ solidBaseName+".sres"

    if (i==0 and (restartOption=="map" or restartOption=="mapstart")):
        print ("Perform Mapping for Solid Simulation")
    else:
        print ("Running Fluid Simulation")
        print (fluidRun)
        err=1
        while (err!=0):            
            err=os.system(fluidRun)
            #print err

    solidFileName = "hflux_solid.txt"
    mapFluidToSolid (fluidSurfs,fluidBaseName,resultCorr,"_Average_heat_flux.txt",solidFileName)
    solidFileName = "htc_solid.txt"
    mapFluidToSolid (fluidSurfs,fluidBaseName,resultCorr,"_Average_h_coeff.txt",solidFileName)
    solidFileName = "temperature_solid.txt"
##    solidFileNamePrev = "temperature_solid_prev.txt"
##    check_copyfile(solidFileName, solidFileNamePrev)    
    mapFluidToSolid (fluidSurfs,fluidBaseName,resultCorr,"_Average_reference_temp.txt",solidFileName)         
    print ("Running Solid Simulation")
    print (solidRun)
    os.system(solidRun)
    fluidFileName = "temperature_fluid.txt"
    mapSolidToFluid (solidSurfs,solidBaseName,"_temperature.txt",fluidFileName)
    print ("Completed coupled cycle:"+str(i+1))
    resultCorrPrev = resultCorr

##    #only for testing
##    monitorFile = open("monitor.txt",'a')
##    solidIntegFileName = solidBaseName+"_integrals.txt"
##    solidIntegFile=check_open(solidIntegFileName,'r')
##    for line in solidIntegFile:
##        words=line.split()
##    monitorFile.write(str(i)+" "+words[1]+"\n")
##    print words[1]
##    solidIntegFile.close()
##    monitorFile.close()
##    ## end of testing
    
raw_input("Press enter to continue")    




