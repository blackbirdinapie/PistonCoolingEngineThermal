import os
import shutil
import math
import re
import platform
import sys
import time
from shutil import copyfile
from operator import sub

def check_open (fileName, mode):
    try:
        fileOpen = open(fileName,mode)
    except (OSError,IOError):
        print( "Error, Unable to open file! Please check that the following file exists and is not already open :"+fileName)
        raw_input("Press enter to continue") 
        exit()
    return fileOpen

def check_copyfile (fileOutName, fileOutName_Old):
    try:
        copyfile(fileOutName,fileOutName_Old)
    except (IOError):
        return


########## inputs ###############################################################################

mappingCaseName = "createLinerHTCCoarse_check2"
boundaryName = "cylinder"
numDegrees = 360
step = 180

fluxOutName_Old = "piston_cycle_averaged_flux_old.txt"
tempOutName_Old = "piston_cycle_averaged_T_old.txt"


fluxOutName = "piston_cycle_averaged_flux.txt"
tempOutName = "piston_cycle_averaged_T.txt"

#crankshaft radius
cr=43e-3
#conrod length
rl=152.5e-3
# engine RPM
omega = 5250


simerics_path = r'"C:\Program Files\Simerics\PumpLinx.exe"'

########## end of inputs ###############################################################################
begin = time.time()


check_copyfile(fluxOutName, fluxOutName_Old)
check_copyfile(tempOutName, tempOutName_Old)

words = simerics_path.split()
plString = " ".join(words)
simPath='"'+plString+'"'+" -run "

degstr = str(int(numDegrees/step))
degname = degstr.zfill(4)
x=[]
y=[]
z=[]
hflux=[]
Tliner=[]

caseFileName = mappingCaseName+".spro"
runFileName = mappingCaseName+"_run.spro"
runResName = mappingCaseName+"_run.sres"

print ("Peform initial simulations \n")
initRun = simPath+caseFileName
os.system(initRun)

firstFileName = mappingCaseName+"_"+boundaryName+"_temperature.txt"

linerTempFileName = mappingCaseName+"_run_"+boundaryName+"_temperature.txt"
linerFluxFileName = mappingCaseName+"_run_"+boundaryName+"_q_bc.txt"

firstFile = check_open(firstFileName,'r')

linerCells=0

for line2 in firstFile:
    words=line2.split()
    try:
        float(words[0])
    except ValueError:
        continue    
    x.append(float(words[0]))
    y.append(float(words[1]))
    z.append(float(words[2]))
    Tliner.append(0)
    hflux.append(0)
    linerCells = linerCells+1
firstFile.close()


count = 0
for degree in xrange(0,numDegrees,step):
    rad = degree*math.pi/180
    caseFile = check_open(caseFileName,'r')
    runFile = open(runFileName,'w')

    for line in caseFile:
        words=line.split()
        if len(words)==0:
            continue
        if words[0]=="#":
            continue
        if (words[0]== "phase"):
            newLine = "phase = "+str(rad)+"\n"
            runFile.write(newLine)        
        else:
            runFile.write(line)
    runFile.close()
    if(count==0):
        runCommand = simPath+runFileName
    else:
        runCommand = simPath+runResName
##    runCommand = simPath+runFileName
    print "Mapping for crank angle:"+str(degree)
    print (runCommand)
    print "Calculation for crank angle:"+str(degree)
    os.system(runCommand)
    time.sleep(2)


    linerTempFile = check_open(linerTempFileName,'r')
    linerCell=0
    for line2 in linerTempFile:
        words=line2.split()
        try:
            float(words[0])
        except ValueError:
            continue
        Tliner[linerCell]=Tliner[linerCell]+float(words[3])
        linerCell=linerCell+1
    linerTempFile.close()
            
    linerFluxFile = check_open(linerFluxFileName,'r')
    linerCell=0
    for line2 in linerFluxFile:
        words=line2.split()
        try:
            float(words[0])
        except ValueError:
            continue
        hflux[linerCell]=hflux[linerCell]+float(words[3])
        linerCell=linerCell+1
    linerFluxFile.close()
    
    count=count+1

hflux[:] = [k / count for k in hflux]
Tliner[:] = [k / count for k in Tliner]

TlinerAvg = sum(Tliner)/float(len(Tliner))

fluxOutFile = check_open(fluxOutName,'w')
fluxOutFile.write('<?xml version="1.0" encoding="ISO-8859-1"?>'+'\n')
fluxOutFile.write('<table mapped_size="'+str(int(linerCells))+'" allowed_error="0.1">'+'\n')

tempOutFile = check_open(tempOutName,'w')
tempOutFile.write('<?xml version="1.0" encoding="ISO-8859-1"?>'+'\n')
tempOutFile.write('<table mapped_size="'+str(int(linerCells))+'" allowed_error="0.1">'+'\n')

for cell in xrange(0,linerCells):
    fluxSign = math.copysign(1,hflux[cell])    
    tempOutFile.write (str(x[cell])+"\t"+str(y[cell])+"\t"+str(z[cell])+"\t"+str(Tliner[cell])+"\n")
    fluxOutFile.write (str(x[cell])+"\t"+str(y[cell])+"\t"+str(z[cell])+"\t"+str(hflux[cell])+"\n")
    

fluxOutFile.write('</table>')
fluxOutFile.close()
tempOutFile.write('</table>')
tempOutFile.close()


elapsed = time.time() - begin
print ("Time taken for mapping:"+str(int(elapsed/60))+" mins") 
   
raw_input("Press enter to continue")    




