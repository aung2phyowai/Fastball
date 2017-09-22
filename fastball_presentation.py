from Tkinter import *
import tkFileDialog
import tkMessageBox
import csv, os
from psychopy import visual, core, gui, event


#function that deploys error message if there is a problem with the script
def showerror(errormsg):
    tkMessageBox.showwarning(
        "Error",
        errormsg,
    )
    return

#function that gets the experiment parameters from the script headers
def setparams(headers):
    #set the parameters as a global variable so that they are accessible
    #within other functions
    global exparams
    tempparams={}
    headerlist=headers.split("\n")
    for param in headerlist:
        #create a dict using the printed label in the script as the name
        #of each parameter
        tempparams[param.split(",")[0]]=param.split(",")[1]
    try:
        #look for all the parameters we need and make sure they are of the
        #correct type
        exparams["exp"]=tempparams["Name of experiment"]
        exparams["ppt"]=tempparams["Participant"]
        exparams["n_cycles"]=int(tempparams["Number of standard+deviant cycles"])
        exparams["stperdev"]=int(tempparams["Number of standards per deviant"])
        exparams["n_frames"]=int(tempparams["Image duration (frames)"])
        exparams["stloc"]=tempparams["Location of Standard image files"]
        exparams["devloc"]=tempparams["Location of Deviant image files"]
        return
    except KeyError:
        #will occur if one or more parameters is missing
        raise KeyError
    except ValueError:
        #will occur if an integer parameter can't be converted to int
        raise ValueError

#function that looks for the specified script file
def checkscript(scriptfile):
    try:
        #open the script file and collect its contents
        with open(scriptfile,"rb") as candscript:
            script=candscript.read()
            return script
    except OSError, IOError:
        #will occur if the script isn't in the given location or can't be read
        raise OSError, IOError

#function that makes sure all parts of the script are present
def checkparams(script):
    #remove windows line ending characters
    while "\r\n" in script:
        script=script.replace("\r\n","\n")
    #remove end-of-line commas that may be present        
    while ",\n" in script:
        script=script.replace(",\n","\n")
    try:
        #split the script into three parts according to expected double 
        #line breaks
        parts=script.split("\n\n")
        headers=parts[2]
        stimscheduletext=parts[3]
    except IndexError:
        #will occur if one of the parts is missing
        raise IndexError
    #turn the requisite part of the text into a list of trials
    stimscheduletext=stimscheduletext.split("\n")
    stimschedule=[]
    #split each row (cycle of standards+dev) into a separate list
    for cycle in stimscheduletext:
        stimschedule.append(cycle.split(","))
    #remove the first row as it consists of headers
    stimschedule.pop(0)
    #if a blank cycle has been left at the end, remove it
    if stimschedule[len(stimschedule)-1]==[""]:
        stimschedule.pop()
    try:
        #run the setparams function on the headers part of the script
        setparams(headers)
    #errors from setparams
    except KeyError:
        raise KeyError
    except ValueError:
        raise ValueError
        
#check for logfile already existing
    print exparams["scriptfilelocation"]
    print "literally anything"
    os.chdir(exparams["scriptfilelocation"])
    try: 
        os.chdir("Logfiles")
        if os.path.isfile(exparams["exp"]+"_ppt_"+exparams["ppt"]+"_logfile.csv"):
            raise Exception("A logfile already exists for this participant")
    except OSError: #no Logfiles directory there
        pass        
    return True, stimschedule

#function to pre-load the standard and deviant images into a correctly
#ordered list
def getimages(stimschedule):
    imglist=[]
    #go to the directory location of standard images
    os.chdir(exparams["stloc"])
    try:
        for stims in stimschedule:
            #collect each image in the stimulus list
            cyclelist=[]
            for s in range(len(stims)):
                #for each trial in the cycle
                if s < len(stims)-1:
                    #if it's not the last one, get it from the standards location
                    cyclelist.append(visual.ImageStim(win=prepwin,image=stims[s]))
                else:
                    #it's a deviant, go to the directory location of deviant images
                    os.chdir(exparams["devloc"])
                    #collect the image from deviants location
                    cyclelist.append(visual.ImageStim(win=prepwin,image=stims[s]))
                    #go back to the standards directory
                    os.chdir(exparams["stloc"])
            #add that cycle to the set of images
            imglist.append(cyclelist)
        #when finished, go back to the script directory location
        os.chdir(scriptlocation)
    except OSError:
        #will occur if missing image
        raise OSError
    except IOError:
        #will occur if unreadable image
        raise IOError
        
    return imglist
    
    
#function to turn the temporary log into a presentable list of image 
#presentation times
def createframelist(templog):
    #total number of images presented was number of cycles * images per cycle
    n_images=exparams["n_cycles"]*(exparams["stperdev"]+1)
    frames=[]
    #look in the temporary log and turn the saved text into a list
    with open(templog,"rb") as framefile: 
        framelist=framefile.read().split(", ")
        #get each frame duration and convert to float
        for f in framelist: 
            frames.append(float(f))
    prestimes=[]
    #for each image, collect the frames relating to it and sum their duration
    for img in range(n_images): 
        time=0 
        for frame in range(exparams["n_frames"]):
            time=time+float(frames[img*exparams["n_frames"]+frame])
        #add the total time for that image to the lists of presentation times
        prestimes.append(time)
    return prestimes
    
#function to create a log file of presented images and their durations
def createlogfile(filename,stimschedule,prestimes):
    os.chdir(exparams["scriptfilelocation"])
    try:
        os.chdir("Logfiles")
    except OSError:
        os.mkdir("Logfiles")
        os.chdir("Logfiles")
    with open(filename,"w") as logfile:
        #write headers into the logfile
        logfile.write("Stimulus,Type,Duration\n")        
    with open(filename,"a") as logfile:
        #write the image and presentation information for each cycle of trials
        for cycle in stimschedule:
            n=0
            while n<exparams["stperdev"]:
                logfile.write(cycle[n]+",Standard,"+str(prestimes[0])+"\n")
                prestimes.pop(0)
                n=n+1
            logfile.write(cycle[n]+",Deviant,"+str(prestimes[0])+"\n")
            prestimes.pop(0)
    os.chdir(scriptlocation)

#function to check whether the script given by the user is OK
#and, if so, use it to  set up the experiment           
def acceptscript(filename):
    #find the script and make sure it's readable
    try:
        script=checkscript(filename)
    except:
        raise OSError("Couldn't read that script file.")
    #make sure the parameters are OK
    try:
        status, stimschedule = checkparams(script)
    #self explanatory exception handling...
    except KeyError:
        raise KeyError("A parameter is missing from the script file.")
    except ValueError:
        raise ValueError("A parameter in the script file is unusable. Check \
that all numerical parameters are integers.")
    except IndexError:
        raise IndexError("Couldn't parse the script file headers. Check that \
file structure is correct.")

    #make sure the cycles and ratio parameters match the schedule of trials
 #produced
    if len(stimschedule)<>exparams["n_cycles"]:
        raise Exception("The number of trials given in the script does not \
match the parameter for the number of standard+deviant cycles.")
    for cycle in stimschedule:
        if len(cycle) <> exparams["stperdev"]+1:
            raise Exception("The number of standards per deviant provided in \
the script does not match the specification in the parameters on at least one \
trial.")         

    #collect the images specified in the trials given by the script
    try:
        stimlist=getimages(stimschedule)
    #more self explanatory exception handling...
    except OSError:
        raise OSError("A stimulus file could not be found. Check that the \
location parameters are correct and that no files are missing.")
    except IOError:
        raise IOError("A stimulus file could not be loaded. Check that all \
stimulus files are of an accepted type.")

    return True, stimlist, stimschedule

#function to present text on the screen until space bar is pressed    
def showtext(string,window):
    screentext=visual.TextStim(win=window, color='black', height=1.5, \
text=string, alignHoriz='center')
    #put the text on the screen
    screentext.draw()
    fastballwin.flip()
    #wait to prevent accidental presses
    core.wait(3) 
    
    #wait for response *** WINDOW DOES NOT HAVE FOCUS HERE?? NOT COLLECTING EVENTS
    responsegiven=False
    while not responsegiven:
        for key in event.getKeys():
            if key in (['escape']):
                #quit on Escape
                fastballwin.close()
                prepwin.close()
                core.quit()
            elif key in (['space']):
                #spacebar, continue
                responsegiven=True
    return
    
exparams={} #global variable
stimschedule=[] #global variable

#check the current directory location
currentlocation=Tk()
currentlocation.withdraw()
#use it as the assumed script location (can be changed by user later)
scriptlocation=os.getcwd()

#create a window to pre-check stimuli
prepwin = visual.Window(fullscr=False, monitor="testmonitor",size=[800,600],\
 units="deg", color =[1,1,1]) 




loadingok=False

while not loadingok:
    try:
        #ask the user for parameters using dialogue box
        exparams["scriptfilename"]=tkFileDialog.askopenfilename(initialdir=scriptlocation,\
        title="Select the script you want to run",\
        filetypes=(("CSV files","*.csv"),))
        
        if not exparams["scriptfilename"]: 
            #cancel button was pressed; quit everything
            loadingok=True
            core.quit()
        else:
            #OK was pressed; process the input
            exparams["scriptfilelocation"]=os.path.dirname(exparams["scriptfilename"])
            #print "here is the location " + os.path.dirname(exparams["scriptfilename"])
            loadingok, stimlist, stimschedule = acceptscript(exparams["scriptfilename"])
            

    except Exception as err:
        #if the input couldn't be processed, tell the user why
        showerror(err.args[0])


#all information was OK; start the experiment        

    
#start a new window here because otherwise it won't have focus
fastballwin=visual.Window(fullscr=False,monitor="surface",units="deg",\
color=[1,1,1])


#stop the mouse appearing in the experiment window (Doesn't seem to be working?)
fastballwin.setMouseVisible(False)

#stop the mouse appearing in the experiment windew
m=event.Mouse(win=fastballwin)
m.setVisible(False)

for cycle in stimlist:
    for s in cycle:
        s.win=fastballwin

#show initial instructions
showtext('You will now see a series of images presented rapidly.\n\n\
Simply keep your gaze in the centre of the screen\n\
and pay attention to all the images.\n\n\
Press the spacebar to start',fastballwin)

fastballwin.flip()
core.wait(1) 

#start logging frame durations
fastballwin.setRecordFrameIntervals(True)

ISI = visual.PatchStim(fastballwin, mask='gauss', sf=0, size=0.02, name='ISI')#GS added

#present the stimuli

for cycle in stimlist:
    for s in cycle:
        s.size=(5,5)#GS added
        for frameN in range(exparams["n_frames"]):
            s.draw()
            fastballwin.flip()
        for frameN in range(exparams["n_frames"]):#GS added
            ISI.draw()
            fastballwin.flip()
       
fastballwin.flip()
#save the recorded frame durations in a temporary log
fastballwin.saveFrameIntervals("tempframelog.csv",clear=True)


#log the presented image and duration info
presentedtimes=createframelist("tempframelog.csv")

#construct the logfile name
filename=exparams["exp"]+"_ppt_"+exparams["ppt"]+"_logfile.csv"

#create the logfile
createlogfile(filename,stimschedule,presentedtimes)

#show final message to the user
showtext("The test is complete. Thank you for participating.",fastballwin)
        
#end experiment
fastballwin.close()
prepwin.close()
core.quit()

