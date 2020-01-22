from pmd_beamphysics import ParticleGroup


import numpy as np


def identify_species(mass, charge):
    """
    Simple function to identify a species based on its mass in kg and charge in C.
    
    Finds species:
        'electron'
        'positron'
    
    TODO: more species
    
    """
    m = round(mass*1e32)/1e32
    q = round(charge*1e20)/1e20
    if m == 9.1e-31:
        if q == 1.6e-19:
            return 'positron'
        if q == -1.6e-19:
            return 'electron'
        
    raise Exception(f'Cannot identify species with mass {mass} and charge {charge}')
   


    
def tout_to_particle_data(tout):
    """
    Convert a tout dict to a standard form
    
    """
    data = {}
    data['x'] = tout['x']
    data['y'] = tout['y']
    data['z'] = tout['z']
    factor = 299792458.**2 /1.60217662e-19 # kg -> eV
    data['px'] = tout['GBx']*tout['m']*factor
    data['py'] = tout['GBy']*tout['m']*factor
    data['pz'] = tout['GBz']*tout['m']*factor
    data['t'] = tout['t']
    data['status'] = 1
    data['weight'] = abs(tout['q']*tout['nmacro'])
    
    masses = np.unique(tout['m'])
    charges = np.unique(tout['q'])
    assert len(masses) == 1, 'All masses must be the same.'
    assert len(charges) == 1, 'All charges must be the same'
    mass = masses[0]
    charge = charges[0]

    species = identify_species(mass, charge)
    
    data['species'] = species
    data['n_particle'] = len(data['x'])
    return data




def touts_to_particlegroups(touts):
    """
    Coverts a list of touts to a list of ParticleGroup objects
    """
    return [ ParticleGroup(data=tout_to_particle_data(tout))  for tout in touts ] 



def particle_stats(particle_groups, key):
    """
    Gets statistic of a list of particle groups
    
    
    key can be any key that ParticleGroup can calculate:
        mean_energy
        mean_z
        mean_t
        sigma_x
        norm_emit_x
        mean_kinetic_energy
        ...
        
    
    """
    return np.array([p[key] for p in particle_groups])

    
    
    