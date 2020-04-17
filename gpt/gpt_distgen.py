from gpt import GPT
from gpt.tools import full_path
from gpt.gpt import run_gpt

from distgen import Generator   
from distgen.writers import write_gpt
from distgen.tools import update_nested_dict

from gpt.gpt_phasing import gpt_phasing

import yaml
import os
import time

def set_gpt_and_distgen(gpt, distgen_input, settings, verbose=False):
    """
    Searches gpt and distgen input for keys in settings, and sets their values to the appropriate input.
    """
    for k, v in settings.items():
        found=gpt.set_variable(k,v)
        #print(k,v,found)
        if verbose and found:
            print(k, 'is in gpt')
        
        if not found:
            distgen_input = update_nested_dict(distgen_input, {k:v}, verbose=bool(verbose))
            #set_nested_dict(distgen_input, k, v)    
    
    return gpt, distgen_input
    
def run_gpt_with_distgen(settings=None,
                         gpt_input_file=None,
                         distgen_input_file=None,
                         workdir=None, 
                         use_tempdir=True,
                         gpt_bin='$GPT_BIN',
                         timeout=2500,
                         auto_phase=False,
                         verbose=False,
                         gpt_verbose=False,
                         asci2gdf_bin='$ASCI2GDF_BIN'
                         ):
    """
    Run gpt with particles generated by distgen. 
    
        settings: dict with keys that can appear in an gpt or distgen Generator input file. 
        
    Example usage:
        G = run_gpt_with_distgen({'lspch':False},
                       gpt_input_file='$LCLS_LATTICE/gpt/models/gunb_eic/gpt.in',
                       distgen_input_file='$LCLS_LATTICE/distgen/models/gunb_gaussian/gunb_gaussian.json',
                       verbose=True,
                       timeout=None
                      )        
        
    """

    # Call simpler evaluation if there is no generator:
    if not distgen_input_file:
        return run_gpt(settings=settings, 
                       gpt_input_file=gpt_input_file, 
                       workdir=workdir,
                       use_tempdir=use_tempdir,
                       gpt_bin=gpt_bin, 
                       timeout=timeout, 
                       verbose=verbose)
    
    if(verbose):
        print('Run GPT with Distgen:') 

    # Make gpt and generator objects
    G = GPT(gpt_bin=gpt_bin, input_file=gpt_input_file, workdir=workdir, use_tempdir=use_tempdir)
    G.timeout=timeout
    G.verbose = verbose

    # Distgen generator
    gen = Generator(verbose=verbose)
    f = full_path(distgen_input_file)
    distgen_params = yaml.safe_load(open(f))

    # Set inputs
    if settings:
        G, distgen_params = set_gpt_and_distgen(G, distgen_params, settings, verbose=verbose)
    
    # Link particle files
    particle_file = os.path.join(G.path, G.get_dist_file())

    if(verbose):
        print('Linking particle files, distgen output will point to -> "'+os.path.basename(particle_file)+'" in working directory.')

    G.set_dist_file(particle_file)

    if('output' in distgen_params and verbose):
        print('Replacing Distgen output params')

    distgen_params['output'] = {'type':'gpt','file':particle_file}

    if(verbose):
        print('\nDistgen >------\n')
    # Configure distgen
    gen.parse_input(distgen_params)   
        

    # Run
    beam = gen.beam()
    write_gpt(beam, particle_file, verbose=verbose, asci2gdf_bin=asci2gdf_bin)

    if(verbose):
        print('------< Distgen\n')

    if(auto_phase): 

        if(verbose):
            print('\nAuto Phasing >------\n')
        t1 = time.time()

        # Create the distribution used for phasing
        if(verbose):
            print('****> Creating intiial distribution for phasing...')

        phasing_beam = get_distgen_beam_for_phasing(beam, n_particle=10, verbose=verbose)
        phasing_particle_file = os.path.join(G.path, 'gpt_particles.phasing.gdf')
        write_gpt(phasing_beam, phasing_particle_file, verbose=verbose, asci2gdf_bin=asci2gdf_bin)
    
        if(verbose):
            print('<**** Created intiial distribution for phasing.\n')    

        G.write_input_file()   # Write the unphased input file

        try: 

            phased_file_name, phased_settings = gpt_phasing(G.input_file, path_to_gpt_bin=G.gpt_bin[:-3], path_to_phasing_dist=phasing_particle_file, verbose=verbose)
            G.set_variables(phased_settings)
            t2 = time.time()
            if(verbose):
                print(f'Time Ellapsed: {t2-t1} sec.')
                print('------< Auto Phasing\n')

        except Exception as ex:

            G.error = True 
            run_info['error'] = self.error
            run_info['why_error'] = str(ex)
            G.output.update(run_info)

            return G

    # If here, either phasing successful, or no phasing requested
    G.run(gpt_verbose=gpt_verbose)
    
    return G


def evaluate_gpt_with_distgen(settings, archive_path=None, merit_f=None, **run_gpt_with_distgen_params):
    """
    Simple evaluate GPT.
    
    Similar to run_astra_with_distgen, but returns a flat dict of outputs. 
    
    Will raise an exception if there is an error. 
    
    """
    G = run_gpt_with_distgen(settings, **run_gpt_with_distgen_params)
        
    if merit_f:
        output = merit_f(G)
    else:
        output = default_gpt_merit(G)
    
    if output['error']:
        raise
    
    fingerprint = G.fingerprint()
    
    output['fingerprint'] = fingerprint
    
    if archive_path:
        path = full_path(archive_path)
        assert os.path.exists(path), f'archive path does not exist: {path}'
        archive_file = os.path.join(path, fingerprint+'.h5')
        G.archive(archive_file)
        output['archive'] = archive_file
        
    return output

def get_distgen_beam_for_phasing(beam, n_particle=10, verbose=False):

    variables = ['x', 'y', 'z','px', 'py', 'pz', 't']

    transforms = { f'avg_{var}':{'type': f'set_avg {var}', f'avg_{var}': { 'value': beam.avg(var).magnitude, 'units':  str(beam.avg(var).units)  } } for var in variables }
    #for var in variables:
    #  
    #    avg_var = beam.avg(var)
    #    transforms[f'set avg {var}'] = {'variables':var, 'type': 'set_avg', 
    #                                    f'avg_{var}': {'value': float(avg_var.magnitude), 'units': str(avg_var.units) }} 

    phasing_distgen_input = {'n_particle':10, 'random_type':'hammersley', 'transforms':transforms,
                             'total_charge':{'value':0.0, 'units':'C'},
                             'start': {'type':'time', 'tstart':{'value': 0.0, 'units': 's'}},}
    
    gen = Generator(phasing_distgen_input, verbose=verbose) 
    pbeam = gen.beam()

    return pbeam


