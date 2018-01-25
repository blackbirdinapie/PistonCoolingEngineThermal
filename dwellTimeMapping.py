import os
import shutil
import math
import re
import platform
import sys
import time

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
    writeFile.write('<table mapped_size="'+str(int(numLinesRead-2))+'" allowed_error="2.0">'+'\n')
    numLines = 0
    for line in readFile:
        if(numLines>1):
            writeFile.write(line)
        numLines=numLines+1
    writeFile.write('</table>')
    readFile.close()
    writeFile.close()

def calcDwellTime(cr,rl,crangle,step,omega):
    stepRad = step*math.pi/180
    dispNow = cr*math.cos(crangle) + math.sqrt(rl**2 - (cr*math.sin(crangle))**2)
    dispPrev = cr*math.cos(crangle-stepRad) + math.sqrt(rl**2 - (cr*math.sin(crangle-stepRad))**2)
    term1Now=(rl**2 - (cr*math.sin(crangle))**2)
    term1Prev=(rl**2 - (cr*math.sin(crangle-stepRad))**2)
    rot = omega*2*math.pi/60
    velNow= (cr*rot)*math.sin(crangle)*(-1*cr*math.cos(crangle)/math.sqrt(term1Now) - 1)
    velPrev= (cr*rot)*math.sin(crangle-stepRad)*(-1*cr*math.cos(crangle-stepRad)/math.sqrt(term1Prev) - 1)
    vel = 0.5*(velNow+velPrev)
    dt = abs((dispNow-dispPrev)/vel)
    return dt

def insert(originalfile,string):
    with open(originalfile,'r') as f:
        with open('newfile.txt','w') as f2: 
            f2.write(string)
            f2.write(f.read())
    f.close()
    f2.close()
    os.remove(originalfile)
    os.rename('newfile.txt',originalfile)

################# Inputs #############################################

mappingCaseName = "pistonMapping"
boundaryNames = ["Piston_liner_mgi_top", "Piston_liner_mgi_bot", "Piston_liner_mgi_mid","Piston_skirt1" ,"Piston_skirt2"]
outNames = ["top_ring","bot_ring", "mid_ring","skirt1","skirt2"]

#crankshaft radius
cr=43e-3
#conrod length
rl=152.5e-3
# engine RPM
omega = 5250

simerics_path = r'"C:\Program Files\Simerics\PumpLinx.exe"'

numDegrees = 360
step = 1

################# End of Inputs #############################################

begin = time.time()

words = simerics_path.split()
plString = " ".join(words)
simPath='"'+plString+'"'+" -run "

mappingRunCommand = simPath+mappingCaseName+".spro"

print ("Mapping liner temperature to piston boundaries")
print mappingRunCommand
os.system (mappingRunCommand)

for b in xrange(0,len(boundaryNames)):

    boundaryName = boundaryNames[b]
    outName = outNames[b]

    print ("Averaging on the boundary "+boundaryName)

    degstr = str(int(numDegrees))
    degname = degstr.zfill(4)
    x=[]
    y=[]
    z=[]
    T=[]
    dwellTime=0
    numPoints=0

    #piston1FluidMapping_0360_Piston_liner_mgi_bot_temperature.txt
    lastFileName = mappingCaseName+"_"+degname+"_"+boundaryName+"_temperature"+".txt"
    lastFile = check_open(lastFileName,'r')
    for line in lastFile:
        words=line.split()    
        try:
            float(words[0])
        except ValueError:
            continue    
        x.append(float(words[0]))
        y.append(float(words[1]))
        z.append(float(words[2]))
        T.append(0)
        numPoints=numPoints+1
    lastFile.close()

    checkFile = open("check.txt",'w')

    k=0

    for i in xrange(step,numDegrees+step,step):
        degstr = str(i)
        degname = degstr.zfill(4)
        fileName = mappingCaseName+"_"+degname+"_"+boundaryName+"_temperature"+".txt"
        tfile = check_open(fileName,'r')
        j=0
        angle = i*math.pi/180
        dt = calcDwellTime(cr,rl,angle,step,omega)
        checkFile.write(str(i)+'\t'+str(dt)+'\n')
        dwellTime=dwellTime+dt
        for line in tfile:
            words=line.split()    
            try:
                float(words[0])
            except ValueError:
                continue
            temperature=float(words[3])
            T[j]=T[j]+temperature
            j=j+1
        k=k+1
        tfile.close()
    checkFile.close()

    print("Number of degrees used for average: "+ str(k))

    writeFileName = "temperature_dtAveraged_"+outName+".txt"
    writeFile = check_open(writeFileName,'w')
    writeFile.write('<?xml version="1.0" encoding="ISO-8859-1"?>'+'\n')
    writeFile.write('<table mapped_size="'+str(int(numPoints))+'" allowed_error="0.1">'+'\n')

    for i in xrange(0,len(T)):
        avTemp = T[i]/(k)
        writeFile.write(str(x[i])+'\t'+str(y[i])+'\t'+str(z[i])+'\t'+str(avTemp)+'\n')
    writeFile.write('</table>')
    writeFile.close()

elapsed = time.time() - begin
print ("Time taken for mapping:"+str(int(elapsed/60))+" mins") 
raw_input("Press enter to continue")    




