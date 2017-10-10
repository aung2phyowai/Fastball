from Tkinter import *
import tkFileDialog
import tkMessageBox
import random, os
from datetime import datetime


##an object that allows the user to select a directory location where
##relevant files arefound
class filebrowser(object):
    root=None
    def __init__(self,field):
        self.location=tkFileDialog.askdirectory(initialdir=currentlocation,\
title="Select the location of your files")
#replace the current contents of the corresponding text field with the
#selected location
        field.delete(0,END)
        field.insert(END,self.location)
        
##an object that presents the user with a warning message        
class errorbox(object):
    root=None
    def __init__(self,message):
        self.location=tkMessageBox.showwarning("Warning",message)
        
##an object that presents the user with an information message
class msgbox(object):
    root=None
    def __init__(self,message):
        self.location=tkMessageBox.showinfo("Information",message)
        
##a function that fetches all the image files from a given directory        
def getimages(imagedir):
    imlist=[]
    for candfile in os.listdir(imagedir):
#look in the given directory for all candidate files
        if candfile.endswith(".png") or candfile.endswith(".jpg") or \
candfile.endswith(".bmp"):
#any filetypes to be included should be listed here
            imlist.append(candfile)
#add successful candidates to the list
    return imlist
    
##a function that checks whether all the parameters given by the user are OK    
def acceptParams(name,ppts,cycles,ratio,frames,standdir,devdir,exploc):
    if not name or not ppts or not cycles or not ratio or not frames \
or not standdir or not devdir or not exploc:
#if any of the fields are empty, this is no good
        return False, "Please complete all the fields",None,None,None
    else:
        try:
            ppts=int(ppts)
            cycles=int(cycles)
            ratio=int(ratio)
            frames=int(frames)
#try converting the numerical parameter inputs to valid integerts
        except ValueError:
#if this doesn't work, object
            return False, "Check that your numerical parameters are \
integers",None,None,None
        else:
            standards=getimages(standdir)
#look in the Standards folder for image files
            if standards==[]:
#if no valid files are found, object
                return False, "The Standards folder contains no valid \
images",None,None,None
            else:
#look in the Deviants folder for image files
                deviants=getimages(devdir)
                if deviants==[]:
#if no valid files are found, object
                    return False, "The Deviants folder contains no valid \
images",None,None,None        
                else:
                    os.chdir(exploc)
                    savdir=name+"_scripts"
                    #savdir=exploc+"/"+name+"_scripts"
#create a string for the name of the folder where the experiment will be saved
#needs generalising to Windows form
                    try:
                        os.makedirs(savdir)
#try creating the folder
                    except OSError:
                        return False, "The experiment already exists \
in this location",None,None,None
#if it already exists, object
                    else:
#if all parameters are ok, return the directory information and image 
#lists and continue
                        return True, "",savdir,standards,deviants
                        
##a function that takes randomisation parameters and creates script files for
##each participant
#this should also take some parameters relating to the randomisation?
def stimallocation(ppts,cycles,ratio,standards,deviants,randtype):
    fullrandomisation=[]
#define empty list to put participant scripts in

#randomise with replacement
    if randtype=="with replacement":
        for p in range(int(ppts)):
#make a list of cycles for each participant        
            thisscript=[]
            for c in range(int(cycles)):
                thiscycle=[]
                for s in range(int(ratio)):
#for each cycle, randomly choose the requisite number of standards, 
#plus one deviant
                    thiscycle.append(random.choice(standards))
                thiscycle.append(random.choice(deviants))
                thisscript.append(thiscycle)
#add the cycle to the list for this participant
            fullrandomisation.append(thisscript)
#when finished with a participant, add their list to the main list of scripts

    else:
#randomisation without replacement
        storig=list(standards)
        devorig=list(deviants)
        for p in range(int(ppts)):
            standards=list(storig)
            deviants=list(devorig)
            thisscript=[]
            for c in range(int(cycles)):
                thiscycle=[]
                for s in range(int(ratio)):
                    if len(standards)==0:
                        standards=list(storig)
                    selection=random.choice(range(len(standards)))
                    thiscycle.append(standards[selection])
                    standards.pop(selection)
                if len(deviants)==0:
                    deviants=list(devorig)
                selection=random.choice(range(len(deviants)))
                thiscycle.append(deviants[selection])
                deviants.pop(selection)
                thisscript.append(thiscycle)
            fullrandomisation.append(thisscript)  


    return fullrandomisation



##a function to turn a list of stimulus allocations into saved files    
def savepptfiles(name,randomisation,cycles,ratio,frames,standdir,devdir,savedir):
    os.chdir(savedir)
    pptno=1
#step through each participant's list of cycles in the randomisation list
    for ppt in randomisation:
#create an appropriate filename for that participant's script file
        filename=name+"_participant_"+str(pptno)+".csv"
#write some appropriate headers to the file
        with open(filename,"w") as scriptinput:
            scriptinput.write("SCRIPT INPUT CREATED,"\
+datetime.now().strftime("%Y-%m-%d %H:%M:%S")+\
"\n\nPARAMETERS\n\nName of experiment,"+name+\
"\nParticipant," +str(pptno)+\
"\nNumber of standard+deviant cycles," + str(cycles) +\
"\nNumber of standards per deviant," + str(ratio) +\
"\nImage duration (frames)," + str(frames) +\
"\nLocation of Standard image files," + standdir +\
"\nLocation of Deviant image files," + devdir+\
"\n\n"+"standard,"*int(ratio)+"deviant\n")
#step through each standards+deviant cycle for that participant            
        for cycle in ppt:
#write the appropriate stimulus information to the file
                with open(filename,"a") as scriptinput:
                    scriptinput.write(",".join(cycle)+"\n")
        pptno=pptno+1
        
#add a folder for logfiles
    os.mkdir("Logfiles")
            
    
##a function that checks for a viable set of parameters and then uses them
##to run the randomisation and create participant files for the experiment        
def createExperiment(name,ppts,cycles,ratio,frames,standdir,devdir,exploc,randtype):
#check whether the parameters are acceptable
    accepted,message,savedir,standards,deviants=acceptParams(name,ppts,cycles,\
ratio,frames,standdir,devdir,exploc)           
    if not accepted:
#if there's a problem, report it to the user        
        errorbox(message)    
    else:    
#otherwise, apply the randomisation to allocate stimuli
        fullrandomisation = stimallocation(ppts,cycles,ratio,standards,deviants,randtype)
#and generate corresponding files to save them to the specified folder
        savepptfiles(name,fullrandomisation,cycles,ratio,frames,standdir,\
devdir,savedir)
#and let the user know everything is done
        msgbox("Your files have been saved! Please use the Quit button \
to exit the Fastball experiment generator.")        

        
        
##set up the GUI
class Expcreator(Frame):
    
##a function that puts interative items on the GUI    
    def createWidgets(self):
    
##a function that adds label+textfield combinations    
        def addfield(self,labtext,y,default):
            self.l=Label(self,text=labtext,anchor="e",width=30)
            self.l.padx=20
            self.l.pady=20
            self.l.grid(row=y,column=0)
            self.e=Entry(self,width=50)
            self.e.padx=20
            self.e.pady=20
            self.e.insert(END,default)
            self.e.grid(row=y,column=1)
            return self.l, self.e

#add a dummy label for some space at the top    
        self.descrip=Label(self)
        self.descrip["text"]=""
        self.descrip.padx=20
        self.descrip.grid(row=0,column=0)

#add label+textfield combinations for parameters the GUI is collecting        
        self.expnamelabel, self.expnameentry = addfield(self,\
"Name of your experiment",1,"MyFastballExperiment")
        self.pplabel, self.ppentry = addfield(self,"Number of participants",\
2,"20")
        self.cycleslabel, self.cyclesentry = addfield(self,"Number of \
standard+deviant cycles",3,"100")
        self.ratioslabel, self.ratiosentry = addfield(self,"Number of \
standards per deviant",4,"5")
        self.frameslabel, self.framesentry = addfield(self,"Image duration \
(frames)",5,"5")
        self.stloclabel, self.stlocentry = addfield(self,"Location of \
Standard images",6,"")
        self.devloclabel, self.devlocentry = addfield(self,"Location of \
Deviant images",7,"")

#add label + entry for dropdown menu
        self.randtype= StringVar(root)
        self.randtype.set("with replacement")
    
        self.exploclabel, self.explocentry = addfield(self,"Location to \
save experiment",8,"")
        self.randtypelabel = Label(self, text="Randomise stimuli:", anchor="e", width="30")
        self.randtypelabel.padx=20
        self.randtypelabel.pady=20
        self.randtypelabel.grid(row=9,column=0)
        self.randtypeentry = Label(self, text="",anchor="w",width=50)
        self.randtypeentry.padx=20
        self.randtypeentry.pady=20
        self.randtypeentry.grid(row=9,column=1)
        
        def change_dropdown(*args):
            return(self.randtype.get())

#add some Browse buttons that allow participants to browse for 
#directory locations        
        self.stloc=Button(self)
        self.stloc["text"]="Browse"
        self.stloc["command"] = lambda: filebrowser(self.stlocentry)
        self.stloc.grid(row=6,column=2)
        
        self.devloc=Button(self)
        self.devloc["text"]="Browse"
        self.devloc["command"] = lambda: filebrowser(self.devlocentry)
        self.devloc.grid(row=7,column=2)
        
        self.exploc=Button(self)
        self.exploc["text"]="Browse"
        self.exploc["command"] = lambda: filebrowser(self.explocentry)
        self.exploc.grid(row=8,column=2)
        
###add a dropdown for randomisation type
        self.randmenu = OptionMenu(self, self.randtype, *{"with replacement","without replacement"})
        self.randmenu.padx=20
        self.randmenu.pady=20
        self.randmenu.grid(row=9,column=1)
        
        self.randtype.trace("w",change_dropdown)
        
#add a quit button 
        self.QUIT=Button(self)
        self.QUIT["text"] = "QUIT"
        self.QUIT["command"] = self.quit
        self.QUIT.padx=20
        self.QUIT.pady=20
        self.QUIT.grid(row=9,column=4)

#add a submit button that tries to create the experiment with the currently 
#given parameters        
        self.CREATE = Button(self)
        self.CREATE["text"] = "CREATE EXPERIMENT FILES"
        self.CREATE["command"] = lambda: createExperiment(\
self.expnameentry.get(),self.ppentry.get(),self.cyclesentry.get(),\
self.ratiosentry.get(),self.framesentry.get(),\
self.stlocentry.get(),self.devlocentry.get(),self.explocentry.get(),\
self.randtype.get())
        self.CREATE.padx=20
        self.CREATE.pady=20
        self.CREATE.grid(row=9,column=3)       
        
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()


#find the current directory that we're working in (for use in filebrowsers)
currentlocation=Tk()
currentlocation.withdraw()


#initialise and run the main GUI        
root=Tk()
root.title("Create New Fastball Experiment")
xloc=(root.winfo_screenwidth()/2)-500
yloc=(root.winfo_screenheight()/2)-120
root.geometry("1000x240+%d+%d" % (xloc, yloc))
app=Expcreator(master=root)
app.mainloop()
root.destroy()
