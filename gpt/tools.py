
from hashlib import blake2b
import numpy as np
import json

import subprocess
import os, errno
import datetime
import time

import importlib

def execute(cmd):
    """
    
    Constantly print Subprocess output while process is running
    from: https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
    
    # Example usage:
        for path in execute(["locate", "a"]):
        print(path, end="")
        
    Useful in Jupyter notebook
    
    """
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line 
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)

# Alternative execute
def execute2(cmd, timeout=None):
    """
    Execute with time limit (timeout) in seconds, catching run errors. 
    """
    
    output = {'error':True, 'log':''}
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout = timeout)
        output['log'] = p.stdout
        output['error'] = False
        output['why_error'] =''
    except subprocess.TimeoutExpired as ex:
        output['log'] = ex.stdout+'\n'+str(ex)
        output['why_error'] = 'timeout'
    except:
        output['log'] = 'unknown run error'
        output['why_error'] = 'unknown'
    return output

def execute3(cmd, kill_msgs=[], verbose=False, timeout=1e6):

    tstart = time.time()
   
    exception = None
    run_time = 0 
    log = []

    kill_on_warning = len(kill_msgs)>1

    try:

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        while(process.poll() is None):

            pout = (process.stderr.readline())#.decode("utf-8")

            if(pout):
                log.append(pout)
                if(verbose):
                    print(pout.strip()) 

            elif pout is None:
                break

            if(pout == '' and process.poll() is not None):
                break

            if(time.time()-tstart > timeout): 
                process.kill()
                exception = "timeout"
                break

            if(kill_on_warning):
                for warning in kill_msgs:
                    if(warning in pout):
                        process.kill()
                        exception = pout               
                        break

        rc = process.poll()

    except Exception as ex:
        exectption=str(ex)

    tstop = time.time()
    if(verbose>0):
        print(f'done. Time ellapsed: {tstop-tstart} sec.')
  
    run_time=tstop-tstart

    return run_time, exception, log



"""UTC to ISO 8601 with Local TimeZone information without microsecond"""
def isotime():
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).astimezone().replace(microsecond=0).isoformat()    



def full_path(path):
    """
    Helper function to expand enviromental variables and return the absolute path
    """
    return os.path.abspath(os.path.expandvars(path))


def native_type(value):
    """
    Converts a numpy type to a native python type.
    See:
    https://stackoverflow.com/questions/9452775/converting-numpy-dtypes-to-native-python-types/11389998
    """
    return getattr(value, 'tolist', lambda: value)()    


class NpEncoder(json.JSONEncoder):
    """
    See: https://stackoverflow.com/questions/50916422/python-typeerror-object-of-type-int64-is-not-json-serializable/50916741
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)

def fingerprint(keyed_data, digest_size=16):
    """
    Creates a cryptographic fingerprint from keyed data. 
    Used JSON dumps to form strings, and the blake2b algorithm to hash.
    
    """
    h = blake2b(digest_size=16)
    for key in sorted(keyed_data.keys()):
        val = keyed_data[key]
        s = json.dumps(val, sort_keys=True, cls=NpEncoder).encode()
        h.update(s)
    return h.hexdigest()  

def get_function(name):
    """
    Returns a function from a fully qualified name or global name.
    """
    
    # Check if already a function
    if callable(name):
        return name
    
    if not isinstance(name, str):
        raise ValueError(f'{name} must be callable or a string.')
    
    if name in globals(): 
        if callable(globals()[name]):
            f = globals()[name]
        else:
            raise ValueError(f'global {name} is not callable')
    else:
        # try to import
        m_name, f_name = name.rsplit('.', 1)
        module = importlib.import_module(m_name)
        f = getattr(module, f_name)
    
    return f 


