from Tkinter import *
import tkFileDialog
import tkMessageBox
import csv, os
from psychopy import visual, core, gui, event

def showerror(errormsg):
    tkMessageBox.showwarning(
        "Error",
        errormsg,
    )
    return

def setparams(headers):
    global exparams
    tempparams={}
    headerlist=headers.split("\n")
    for param in headerlist:
        tempparams[param.split(",")[0]]=param.split(",")[1]
    try:
        exparams["exp"]=tempparams["Name of experiment"]
        exparams["ppt"]=tempparams["Participant"]
        exparams["n_cycles"]=int(tempparams["Number of standard+deviant cycles"])
        exparams["stperdev"]=int(tempparams["Number of standards per deviant"])
        exparams["n_frames"]=int(tempparams["Image duration (frames)"])
        exparams["stloc"]=tempparams["Location of Standard image files"]
        exparams["devloc"]=tempparams["Location of Deviant image files"]
        return
    except KeyError:
        raise KeyError
    except ValueError:
        raise ValueError

def checkscript(scriptfile):
    try:
        with open(scriptfile,"rb") as candscript:
            script=candscript.read()
            return script
    except OSError, IOError:
        raise OSError, IOError

def checkparams(script):        
    while ",\n" in script:
        script=script.replace(",\n","\n")
    try:
        parts=script.split("\n\n")
        headers=parts[2]
        stimscheduletext=parts[3]
    except IndexError:
        raise IndexError
    stimscheduletext=stimscheduletext.split("\n")
    stimschedule=[]
    for cycle in stimscheduletext:
        stimschedule.append(cycle.split(","))
    stimschedule.pop(0) #first one is headers
    #if the last one is blank, remove it
    if stimschedule[len(stimschedule)-1]==[""]:
        stimschedule.pop()
    try:
        setparams(headers)
    except KeyError:
        raise KeyError
    except ValueError:
        raise ValueError
            
    return True, stimschedule


def getimages(stimschedule):
    imglist=[]
    os.chdir(exparams["stloc"])
    try:
        for stims in stimschedule:
            cyclelist=[]
            for s in range(len(stims)):
                if s < len(stims)-1:
                    cyclelist.append(visual.ImageStim(win=fastballwin,image=stims[s]))
                else:
                    os.chdir(exparams["devloc"])
                    cyclelist.append(visual.ImageStim(win=fastballwin,image=stims[s]))
                    os.chdir(exparams["stloc"])
            imglist.append(cyclelist)
        os.chdir(scriptlocation)
        return imglist
    except OSError:
        raise OSError
    except IOError:
        raise IOError
    
def createframelist(templog):
    n_images=exparams["n_cycles"]*(exparams["stperdev"]+1)
    frames=[]
    with open(templog,"rb") as framefile: 
        framelist=framefile.read().split(", ") # split frame durations by delimiter
        #print len(framelist)
        for f in framelist: 
            frames.append(float(f))#collect frame durations
    prestimes=[]
    for img in range(n_images): 
        time=0 
        for frame in range(exparams["n_frames"]): #collect the next set of frame durations from the appropriate starting point
            time=time+float(frames[img*exparams["n_frames"]+frame]) #add onto time so far
        prestimes.append(time) #add the total time for that image to the list of presentation times
    return prestimes
    

def createlogfile(filename,stimschedule,prestimes):
    with open(filename,"w") as logfile:
        logfile.write("Stimulus,Type,Duration\n")        
    with open(filename,"a") as logfile:
        for cycle in stimschedule:
            n=0
            while n<exparams["stperdev"]:
                logfile.write(cycle[n]+",Standard,"+str(prestimes[0])+"\n")
                #print len(prestimes)
                prestimes.pop(0)
                n=n+1
            logfile.write(cycle[n]+",Deviant,"+str(prestimes[0])+"\n")
            prestimes.pop(0)
            
def acceptscript(filename):
    #find the script
    try:
        script=checkscript(filename)
    except:
        raise OSError("Couldn't read that script file.")
    try:
        status, stimschedule = checkparams(script)
    except KeyError:
        raise KeyError("A parameter is missing from the script file.")
    except ValueError:
        raise ValueError("A parameter in the script file is unusable. Check \
that all numerical parameters are integers.")
    except IndexError:
        raise IndexError("Couldn't parse the script file headers. Check that \
file structure is correct.")
  
    try:
        stimlist=getimages(stimschedule)
        return True, stimlist, stimschedule
    except OSError:
        raise OSError("A stimulus file could not be found. Check that the \
location parameters are correct and that no files are missing.")
    except IOError:
        raise IOError("A stimulus file could not be used. Check that all \
stimulus files are of an accepted type.") 

    
def showtext(string,window):
    screentext=visual.TextStim(win=window, color='black', height=10.5, text=string, alignHoriz='center')# this is alignment to the screen not the text alignment, irritatingly
    screentext.draw()
    fastballwin.flip()
    core.wait(3)#prevent accidental presses. 
    
    #wait for response
    responsegiven=False
    while not responsegiven:
        for key in event.getKeys():
            if key in (['escape']):
                mywin.close()
                core.quit()
            elif key in (['space']):
                responsegiven=True
    return
    
exparams={} #global variable
stimschedule=[] #global variable

currentlocation=Tk()
currentlocation.withdraw()
scriptlocation=os.getcwd()

fastballwin = visual.Window(fullscr=True, monitor="testmonitor",size=[800,600], units="pix", color =[1,1,1])# to set a window use size [800,600] and remove the fullscr arguement, you can choose "deg" = visual angle, or "pix" for pixels, this then use the approp units in your image defs below
#may need to add param monitor="testmonitor"
fastballwin.setMouseVisible(False)# stops the mouse appearing ontop

loadingok=False

while not loadingok:
    

    try:

        exparams["scriptfilename"]=tkFileDialog.askopenfilename(initialdir=scriptlocation,\
        title="Select the script you want to run",\
        filetypes=(("CSV files","*.csv"),))
        
        if not exparams["scriptfilename"]: #cancel button
            loadingok=True
            core.quit()
        else:

            loadingok, stimlist, stimschedule = acceptscript(exparams["scriptfilename"])

    except Exception as err:
        #print "the error was "+err.args[0]
        showerror(err.args[0])
        

showtext('You will now see a series of images presented rapidly.\n\n\
Simply keep your gaze in the centre of the screen\n\
and pay attention to all the images.\n\n\
Press the spacebar to start',fastballwin)

fastballwin.flip()
core.wait(1)        



#start logging frame durations
fastballwin.setRecordFrameIntervals(True)# this turns on recording frame durations
#fastballwin._refreshThreshold=1/60.0+0.004 #i've got 60Hz monitor and want to allow 4ms tolerance


#present the stimuli

for cycle in stimlist:
    for s in cycle:
        for frameN in range(exparams["n_frames"]):
            s.draw()
            fastballwin.flip()
       
fastballwin.flip()
fastballwin.saveFrameIntervals("tempframelog.csv",clear=True)



#log the presented image and duration info

presentedtimes=createframelist("tempframelog.csv")

filename=exparams["exp"]+"_ppt_"+exparams["ppt"]+"_logfile.csv"

createlogfile(filename,stimschedule,presentedtimes)

showtext("The test is complete. Thank you for participating.",fastballwin)
    
fastballwin.close()
core.quit()

