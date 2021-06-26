import copy
from . import easygdf
import time
import numpy as np
import re
import os

from gpt.tools import full_path

import shutil

# ------ Number parsing ------
def isfloat(value):
      try:
            float(value)
            return True
      except ValueError:
            return False

def find_path(line, pattern=r'"([^"]+\.gdf)"'):

    matches=re.findall(pattern, line)
    return matches
 
  
 
def set_support_files(lines, original_path, target_path='', copy_files=False, pattern=r'"([^"]+\.gdf)"', verbose=False):

    for ii, line in enumerate(lines):

        support_files = find_path(line, pattern=pattern)

        for support_file in support_files:

            #print(full_path(support_file))

            abs_original_path = full_path( os.path.join(original_path, os.path.expandvars(support_file)) )
            
            #print(support_file, original_path, abs_original_path)


            if(copy_files):
            
                abs_target_path = os.path.join(target_path, support_file) 
                shutil.copyfile(abs_original_path, abs_target_path, follow_symlinks=True)            

                if(verbose):
                    print("Copying file: ", abs_original_path,'->',abs_target_path)   

            else:

                if(os.path.isfile(abs_original_path)):
                    lines[ii] = line.replace(support_file, abs_original_path)
                    if(verbose):
                        print("Set path to file: ",lines[ii])        

def parse_gpt_input_file(filePath, condense=False, verbose=False):
    """
    Parses GPT input file 
    """

    finput={}

    with open(filePath, 'r') as f:

        clean_lines = []

        # Get lines without comments
        for line in f:
            tokens = line.strip().split('#')
            if(len(tokens[0])>0):
                clean_line = tokens[0].strip().replace('\n', '')
                clean_lines.append(clean_line)

    variables={}

    for ii,line in enumerate(clean_lines):
      
        tokens = line.split("=")

        if(len(tokens)==2 and isfloat(tokens[1][:-1].strip())):
 
            name = tokens[0].strip()
            value = float(tokens[1][:-1].strip())
            
            if(name not in variables.keys()):
                variables[name]=value 
            elif(verbose):
                print(f'Warning: multiple definitions of variable {name} on line {ii}.')

    for line in clean_lines:
        find_path(line)

    finput['lines']=clean_lines
    finput['variables']=variables

    return finput


def write_gpt_input_file(finput, inputFile, ccs_beg='wcs'):

    #print(inputFile)
    for var in finput['variables'].keys():

        value=finput['variables'][var]
        for index,line in enumerate(finput['lines']):
            tokens = line.split('=')
            if(len(tokens)==2 and tokens[0].strip()==var):
                finput["lines"][index]=f'{var}={value};'
                break

    with open(inputFile,'w') as f:

        for line in finput["lines"]:
            f.write(line+"\n")

        if(ccs_beg!="wcs"):
            f.write(f'settransform("{ccs_beg}", 0,0,0, 1,0,0, 0,1,0, "beam");\n')

def read_particle_gdf_file(gdffile, verbose=0.0, extra_screen_keys=['q','nmacro'], load_files=False): #,'ID', 'm']):

    with open(gdffile, 'rb') as f:
      data = easygdf.load_initial_distribution(f, extra_screen_keys=extra_screen_keys)

    screen = {}
    n = len(data[0,:])
    if(n>0):

        q = data[7,:]          # elemental charge/macroparticle
        nmacro = data[8,:]     # number of elemental charges/macroparticle
                   
        weights = np.abs(data[7,:]*data[8,:])/np.sum(np.abs(data[7,:]*data[8,:]))

        screen = {"x":data[0,:],"GBx":data[1,:],
                  "y":data[2,:],"GBy":data[3,:],
                  "z":data[4,:],"GBz":data[5,:],
                  "t":data[6,:],
                  "q":data[7,:],
                  "nmacro":data[8,:],
                  "w":weights,
                  "G":np.sqrt(data[1,:]*data[1,:]+data[3,:]*data[3,:]+data[5,:]*data[5,:]+1)}
                
                    #screen["Bx"]=screen["GBx"]/screen["G"]
                    #screen["By"]=screen["GBy"]/screen["G"]
                    #screen["Bz"]=screen["GBz"]/screen["G"]

        screen["time"]=np.sum(screen["w"]*screen["t"])
        screen["n"]=n          

    return screen

def read_gdf_file(gdffile, verbose=False, load_fields=False):
      
    # Read in file:

  
    #self.vprint("Current file: '"+data_file+"'",1,True)
    #self.vprint("Reading data...",1,False)
    t1 = time.time()
    with open(gdffile, 'rb') as f:
        
        if(load_fields):
            extra_tout_keys   = ['q', 'nmacro', 'ID', 'm', 'fEx', 'fEy', 'fEz', 'fBx', 'fBy', 'fBz']
        else:
            extra_tout_keys   = ['q', 'nmacro', 'ID', 'm']
        
        touts, screens = easygdf.load(f, extra_screen_keys=['q','nmacro', 'ID', 'm'], extra_tout_keys=extra_tout_keys)
        
    t2 = time.time()
    if(verbose):
        print(f'   GDF data loaded, time ellapsed: {t2-t1:G} (sec).')
            
    #self.vprint("Saving wcs tout and ccs screen data structures...",1,False)

    tdata, fields = make_tout_dict(touts, load_fields=load_fields)
    pdata = make_screen_dict(screens)

    return (tdata, pdata, fields)




def make_tout_dict(touts, load_fields=False):

    tdata=[]
    fields = []
    count = 0
    for data in touts:
        n=len(data[0,:])
        
        if(n>0):

            q = data[7,:]       # elemental charge/macroparticle
            nmacro = data[8,:]  # number of elemental charges/macroparticle
                    
            if(np.sum(q)==0 or np.sum(nmacro)==0):
                weights = data[10,:]/np.sum(data[10,:])  # Use the mass if no charge is specified
            else:
                weights = np.abs(data[7,:]*data[8,:])/np.sum(np.abs(data[7,:]*data[8,:]))

            tout = {"x":data[0,:],"GBx":data[1,:],
                    "y":data[2,:],"GBy":data[3,:],
                    "z":data[4,:],"GBz":data[5,:],
                    "t":data[6,:],
                    "q":data[7,:],
                    "nmacro":data[8,:],
                    "ID":data[9,:],
                    "m":data[10,:],
                    "w":weights,
                    "G":np.sqrt(data[1,:]*data[1,:]+data[3,:]*data[3,:]+data[5,:]*data[5,:]+1)}

            #tout["Bx"]=tout["GBx"]/tout["G"]
            #tout["By"]=tout["GBy"]/tout["G"]
            #tout["Bz"]=tout["GBz"]/tout["G"]

            tout["time"]=np.sum(tout["w"]*tout["t"])
            tout["n"]=len(tout["x"])
            tout["number"]=count
            
            if(load_fields):
                field = {'Ex':data[11,:], 'Ey':data[12,:], 'Ez':data[13,:],
                          'Bx':data[14,:], 'By':data[15,:], 'Bz':data[16,:]}
            else:
                field=None
            
            fields.append(field)

            count=count+1
            tdata.append(tout)

    return tdata, fields

def make_screen_dict(screens):

    pdata=[]
         
    count=0
    for data in screens:
        n = len(data[0,:])
        if(n>0):

            q = data[7,:]          # elemental charge/macroparticle
            nmacro = data[8,:]     # number of elemental charges/macroparticle
                   
            if(np.sum(q)==0 or np.sum(nmacro)==0):
                weights = data[10,:]/np.sum(data[10,:])  # Use the mass if no charge is specified
            else:
                weights = np.abs(data[7,:]*data[8,:])/np.sum(np.abs(data[7,:]*data[8,:]))

            screen = {"x":data[0,:],"GBx":data[1,:],
                      "y":data[2,:],"GBy":data[3,:],
                      "z":data[4,:],"GBz":data[5,:],
                      "t":data[6,:],
                      "q":data[7,:],
                      "nmacro":data[8,:],
                      "ID":data[9,:],
                      "m":data[10,:],
                      "w":weights,
                      "G":np.sqrt(data[1,:]*data[1,:]+data[3,:]*data[3,:]+data[5,:]*data[5,:]+1)}
                
                    #screen["Bx"]=screen["GBx"]/screen["G"]
                    #screen["By"]=screen["GBy"]/screen["G"]
                    #screen["Bz"]=screen["GBz"]/screen["G"]

            screen["time"]=np.sum(screen["w"]*screen["t"])
            screen["n"]=n
            screen["number"]=count

            count=count+1
            pdata.append(screen)
                    
    t2 = time.time()
    #self.vprint("done. Time ellapsed: "+self.ptime(t1,t2)+".",0,True)

    ts=np.array([screen['time'] for screen in pdata])
    sorted_indices = np.argsort(ts)
    return [pdata[sii] for sii in sorted_indices]

def parse_gpt_string(line):
    return re.findall(r'\"(.+?)\"',line) 

def replace_gpt_string(line,oldstr,newstr):

    strs = parse_gpt_string(line)
    assert oldstr in strs, 'Could not find string '+oldstr+' for string replacement.'
    line.replace(oldstr,newstr)

