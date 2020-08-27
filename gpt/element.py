import numpy as np
import os
import math, cmath
from gpt.tools import rotation_matrix
from gpt.tools import cvector
from gpt.tools import rad, deg
from gpt.tools import get_arc

from gpt.template import BASIC_TEMPLATE

from matplotlib import pyplot as plt

from numpy.linalg import norm 

def is_bend(element):

    if(element.type in ['SectorBend', 'Sectormagnet']):
        return True
    else:
        return False

def is_screen(element):
    if(element.type == 'Screen'):
        return True
    else:
        return False

class Element:

    """ Defines a basic element object """

    def __init__(self, name, length=0, width=0, height=0, angles=[0,0,0], color='k'):

        self._type='element'

        assert length>=0, 'gpt.Element->length must be >=0.'
        assert width>=0, 'gpt.Element->width must be >=0.'
        assert height>=0, 'gpt.Element->height must be >= 0.'

        self._name = name
        self._length = length
        self._width = width
        self._height = height
        self._ccs_beg='wcs'
        self._color=color

    def set_ref_trajectory(self, npts=100):

        """ Get points to visualize the reference (geometric) trajectory """

        if(self._s_beg!=self._s_end):

            self._s_ref = np.linspace(self._s_beg, self._s_end, npts) 
            self._p_ref = self._p_beg

            for s in self._s_ref[1:]:
                ps = self._p_beg + (s-self._s_beg)*cvector(self._M_beg[:,2])
                self._p_ref = np.concatenate( (self._p_ref, ps) , axis=1)

        else:
            self._s_ref = np.array([self._s_beg, self._s_end])
            self._p_ref = np.concatenate( (self._p_beg, self._p_end) , axis=1)

    def place(self, ref_element=None, ds=0):

        """ Places an element with respect to a reference element, shifted by ds
            If ds >= 0, the this is the distance from ref_element.p_end to self.p_beg 
            If ds < 0, then this is the distance from self.p_end to ref_element.p_beg
        """

        if(ref_element is None):
            ref_element=Beg()

        if(ds>=0):

            s = ref_element.s_end
            M = ref_element.M_end
            p = ref_element.p_end

            if(is_bend(ref_element)):
                self._ccs_beg_origin = p
            else:
                self._ccs_beg_origin = ref_element.ccs_beg_origin

            e3 = cvector(M[:,2])
 
            self._ccs_beg = ref_element.ccs_end
            self._ccs_end = ref_element.ccs_end  # Straight line, no ccs flips

            self._s_beg = s + ds
            self._p_beg = p + ds*e3
            self._M_beg = M

            self._p_end = self.p_beg + self._length*e3
            self._M_end = M
            self._s_end = s + ds + self._length

        else:

            s = ref_element.s_beg
            M = ref_element.M_beg
            p = ref_element.p_beg

            self._ccs_beg_origin = ref_element.ccs_beg_origin

            e3 = cvector(M[:,2])

            self._ccs_beg = ref_element.ccs_beg
            self._ccs_end = ref_element.ccs_beg  # Straight line, no ccs flips

            self._s_end = s + ds
            self._p_end = p + ds*e3

            self._p_beg = self.p_end - self._length*e3
            self._s_beg= s + ds - self._length

        self._ccs_end = ref_element.ccs_end  # Straight line, no ccs flips

        self._M_beg = M
        self._M_end = M

        self._ds = np.linalg.norm(self._p_beg - self._ccs_beg_origin)
        self.set_ref_trajectory()

    def plot_floor(self, axis=None, alpha=1.0, ax=None):

        if(ax == None):
            ax = plt.gca()

        p1 = self.p_beg + (self._width/2)*cvector(self._M_beg[:,0])
        p2 = self.p_beg - (self._width/2)*cvector(self._M_beg[:,0])
        p3 = self.p_end + (self._width/2)*cvector(self._M_end[:,0])
        p4 = self.p_end - (self._width/2)*cvector(self._M_end[:,0])

        ps = np.concatenate( (p1, p3, p4, p2, p1), axis=1)

        ax.plot(ps[2], ps[0], self.color )
        ax.set_xlabel('z (m)')
        ax.set_ylabel('x (m)')

        if(axis=='equal'):
            ax.set_aspect('equal')

    def track1(self, x0=0, px0=0, y0=0, py0=0, z0=0, pz0=1e-15, t0=0, weight=1, status=1, species='electron', s=None):
        pass

    def track_ref(self, p0=1e-15):
        pass

    def __str__(self):
      
        ostr = f'Name: {self._name}\nType: {self._type}\ns-entrance: {self._s_beg} m.\ns-exit: {self._s_end} m.\nLength: {self._length}\nWidth: {self._width} m.'
        return ostr

    def plot_3d(self):
        pass

    @property
    def name(self):
        return self._name

    @property    
    def type(self):
        return self._type

    @property
    def length(self):
        return self._length

    @property
    def s_beg(self):
        return self._s_beg

    @property
    def s(self):
        return 0.5*(self.s_beg+self.s_end)

    @property
    def s_end(self):
        return self._s_end

    @property
    def M_beg(self):
        return self._M_beg

    @property
    def M_end(self):
        return self._M_end

    @property
    def p_beg(self):
        return self._p_beg

    @property
    def p(self):
        return 0.5*(self.p_end+self.p_beg)

    @property
    def p_end(self):
        return self._p_end

    @property
    def s_ref(self):
        return self._s_ref

    @property
    def p_ref(self):
        return self._p_ref

    @property
    def e1_beg(self):
        return cvector(self._M_beg[:,0])

    @property
    def e2_beg(self):
        return cvector(self._M_beg[:,1])

    @property
    def e3_beg(self):
        return cvector(self._M_beg[:,2])

    @property
    def e1_end(self):
        return cvector(self._M_end[:,0])

    @property
    def e2_end(self):
        return cvector(self._M_end[:,1])

    @property
    def e3_end(self):
        return cvector(self._M_end[:,2])

    @property
    def ccs_beg(self):
        return self._ccs_beg

    @property
    def ccs_end(self):
        return self._ccs_end

    @property
    def ccs_beg_origin(self):
        return self._ccs_beg_origin

    @property
    def color(self):
        return self._color

    def gpt_lines(self):
        return []

    def write_element_to_gpt_file(self, gptfile):

        assert os.path.exists(gptfile)

        with open(gptfile, 'a') as fid:
            lines = self.gpt_lines()
            for line in lines:
                fid.write(line+'\n')


class Screen(Element):

    def __init__(self, name, color='k', width=0.2, n_screens=1, fix_s_position=True):

        assert n_screens>0, 'Number of screens must be > 0.'

        super().__init__(name, length=0, width=width, height=0, angles=[0, 0, 0], color=color)
        self._n_screens=n_screens
        self._fix_s_position=fix_s_position
        self._type='screen'

    def gpt_lines(self):

        lines=[]

        if(self._fix_s_position):
            s = 0.5*(self._s_beg + self._s_end)
        else:
            s= 0

        ds = np.linalg.norm( 0.5*(self.p_end + self.p_beg) - self._ccs_beg_origin) 

        if(self._n_screens == 1):

            lines.append(f'screen("{self._ccs_beg}", 0, 0, {ds-s}, 1, 0, 0, 0, 1, 0, {s});')

        return lines



class Beg(Element):

    def __init__(self, s=0, origin=[0,0,0], angles=[0,0,0]):

        self._M_beg = rotation_matrix(angles[0], angles[1], angles[2])

        super().__init__('beg', angles=[0,0,0])

        self._type = 'lattice starting element'

        self._M_beg = rotation_matrix(angles[0], angles[1], angles[2])
        self._M_end = self._M_beg
        self._s_beg = s
        self._s_end = s

        self._p_beg = cvector(origin)
        self._p_end = cvector(origin)

        self.set_ref_trajectory()

        self._ccs_beg = 'wcs'
        self._ccs_end = 'wcs'

    @property
    def ccs_beg_origin(self):
        return self._p_end
    


class Quad(Element):

    def __init__(self,
        name,
        length,
        width=0.2, 
        height=0, 
        n_screens=2,
        angles=[0,0,0],
        color='b'):

        self._type = 'Quad'
        super().__init__(name, length=length, width=width, height=height, angles=angles, color=color)


class SectorBend(Element):

    def __init__(self, name, R, angle, width=0.2, height=0, phi_in=0, phi_out=0, M=np.identity(3), plot_pole_faces=True, color='r'):

        assert np.abs(angle)>0, 'SectorBend must nonzero bending angle.'

        length = np.abs(rad(angle))*np.abs(R)

        self._R = np.abs(R)
        self._theta = angle
        self._phi = 0
        self._psi = 0
        self._phi_in = phi_in
        self._phi_out = phi_out

        self._plot_pole_faces=plot_pole_faces

        super().__init__(name, length=length, width=width, height=height, angles=[angle, 0, 0], color=color)

    def __str__(self):

        ostr = super().__str__()
        ostr = f'{ostr}\nRadius: {self.R} m.'
        if(self._phi==0 and self._psi==0):
            ostr = ostr + f'\nphi_in: {self._phi_in} deg.\nphi_out: {self._phi_out} deg.'
        ostr = f'{ostr}\nCCS into dipole: "{self._ccs_beg}"'
        return ostr

    def place(self, previous_element=Beg(), ds=0):

        """ This functin sets the element in the correct position in the lattice """

        assert ds>=0, "Bending magnets must be added in beamline order (ds>=0)."

        self._ccs_beg = previous_element.ccs_end
        self._ccs_end = f'{self.name}_ccs_end'

        s = previous_element.s_end
        M = previous_element.M_end
        p = previous_element.p_end

        if(is_bend(previous_element)):
            self._ccs_beg_origin = p
        else:
            self._ccs_beg_origin = previous_element.ccs_beg_origin

        e1 = cvector(M[:,0])
        e3 = cvector(M[:,2])

        dM = rotation_matrix(self._theta)

        self._s_beg = s + ds
        self._p_beg = p + ds*e3
        self._M_beg = M

        self._p_end = self.p_beg +np.sign(self._theta)*self._R*(e1-np.matmul(dM,e1))
        self._M_end = np.matmul(dM, M)
        self._s_end = s + ds + self._length

        self._ds = np.linalg.norm(self._p_beg - self.ccs_beg_origin)

        self.set_ref_trajectory()
        self.set_pole_faces()

    def set_ref_trajectory(self, npts=100):

        """This sets the reference trajectory of the bend, user can supply how many points for generating the 3d curve"""
      
        self._s_ref = np.linspace(self._s_beg, self._s_end, npts) 
        angles = np.linspace(0, self._theta, npts)
        self._p_ref = self._p_beg

        for ii, s in enumerate(self._s_ref[1:]):

            Mii = np.matmul(rotation_matrix(theta=angles[ii]), self._M_beg)
            e1ii = cvector(Mii[:,0])
            ps = self._p_beg +np.sign(self._theta)*self._R*(self.e1_beg-e1ii)
            self._p_ref = np.concatenate( (self._p_ref, ps) , axis=1)

    def set_pole_faces(self):

        h1 = 1.5*self._width/np.cos(rad(self._phi_in))/2
        h2 = 1.5*self._width/np.cos(rad(self._phi_out))/2

        Mbeg = rotation_matrix(+np.sign(self._theta)*self._phi_in)
        Mend = rotation_matrix(-np.sign(self._theta)*self._phi_out)

        self._pole_face_beg_a = self._p_beg + h1*np.matmul(Mbeg, self.e1_beg)
        self._pole_face_beg_b = self._p_beg - h1*np.matmul(Mbeg, self.e1_beg)

        self._pole_face_end_a = self._p_end + h1*np.matmul(Mend, self.e1_end)
        self._pole_face_end_b = self._p_end - h1*np.matmul(Mend, self.e1_end)

        self._pole_face_beg = np.concatenate( (self._pole_face_beg_a, self._pole_face_beg_b), axis=1) 
        self._pole_face_end = np.concatenate( (self._pole_face_end_a, self._pole_face_end_b), axis=1) 

    def plot_floor(self, axis='equal', ax=None):

        if(ax == None):
            ax = plt.gca()

        e1_beg = cvector(self._M_beg[:,0])
        arc1_beg = self.p_beg + np.sign(self._theta)*(self._width/2)*cvector(e1_beg)
        arc1 = get_arc(self._R-self._width/2, arc1_beg, e1_beg, self._theta )

        arc2_beg = self.p_beg - np.sign(self._theta)*(self._width/2)*cvector(e1_beg)
        arc2 = np.fliplr(get_arc(self._R+self._width/2, arc2_beg, e1_beg, self._theta ))

        ps = np.concatenate( (arc1_beg, arc1, arc2, arc1_beg), axis=1)

        ax.plot(ps[2], ps[0], self.color)
        if(self._plot_pole_faces):
            ax.plot(self._pole_face_beg[2], self._pole_face_beg[0],'k')
            ax.plot(self._pole_face_end[2], self._pole_face_end[0],'k')
        ax.set_xlabel('z (m)')
        ax.set_ylabel('x (m)')

        if(axis=='equal'):
            ax.set_aspect('equal')

        return ax

    @property
    def R(self):
        return self._R

    @property
    def angle(self):
        return self._theta


class Lattice():

    def __init__(self, name, s=0, origin=[0,0,0], angles=[0,0,0]):

        self._name=name
        self._elements=[]
        self._ds=[]

        self._bends=[]

        self._elements.append(Beg(s, origin, angles))
        self._bends.append(Beg(s, origin, angles))

    #def get_element_ds(self, ds, ref_origin, p_beg_ref, p_end_ref, element_origin, element_length):

        

    def sort(self):

        s = [ele.s_beg for ele in self._elements]
        sorted_indices = sorted(range(len(s)), key=lambda k: s[k])
        self._elements = [self._elements[sindex] for sindex in sorted_indices]


    def add(self, element, ds, ref_element=None, ref_origin='end', element_origin='beg'):

        if(ref_element is None):

            element.place(self._elements[-1], ds=ds)
            self._elements.append(element)

        else:

            ref_element = self[ref_element]
        
            if(ds>=0):
                if(element_origin =='beg' ):
                    element_delta = 0
                elif(element_origin == 'center'):
                    element_delta = -np.sign(ds)*element.length/2.0
                elif(element_origin == 'end' ):
                    element_delta = -np.sign(ds)*element.length

                if(ref_origin =='beg' ):
                    ref_delta = -ref_element.length
                elif(ref_origin == 'center'):
                    ref_delta = -ref_element.length/2.0
                elif(ref_origin == 'end' ):
                    ref_delta = 0

            elif(ds<0):

                if(element_origin =='beg' ):
                    element_delta = element.length
                elif(element_origin == 'center'):
                    element_delta = element.length/2.0
                elif(element_origin == 'end' ):
                    element_delta = 0

                if(ref_origin =='beg' ):
                    ref_delta = 0
                elif(ref_origin == 'center'):
                    ref_delta = ref_element.length/2.0
                elif(ref_origin == 'end' ):
                    ref_delta = ref_element.length

            ref_index = self._elements.index(ref_element)

            #print(element.name, ds, ref_delta, element_delta)

            element.place(ref_element, ds=ds+element_delta+ref_delta)

            if(ds<0):
                self._elements.insert(ref_index, element)
            else:
                self._elements.insert(ref_index+1, element)

            self.sort()

    def __getitem__(self, identity):

        if(isinstance(identity,int)):
            return self._elements[identity]
        elif(isinstance(identity, str)):
            for ele in self._elements:
                if(identity==ele.name):
                    return ele
            raise ValueError(f'No element in lattice with identity {identity}!')

        return self._elements[identity]

    def index(self, element_name):
        for ii, element in enumerate(self._elements):
            if(element.name==element_name):
                return ii
        return None


    @property
    def s_ref(self):
        s = self._elements[0].s_ref 
        for ele in self._elements[1:]:
            s = np.concatenate( (s, ele.s_ref) )    
        return s

    @property
    def orbit_ref(self):
        p = self._elements[0].p_ref
        for ele in self._elements[1:]:
            p = np.concatenate( (p, ele.p_ref), axis=1 )
        return p

    @property
    def s_ccs(self):
        s = []
        for ele in self._elements:
            if(ele.type in ['Sectormagnet']):
                s = np.concatenate( (s, ele.s_screen))

        return s

    @property
    def s_beg(self):
        return self._elements[0].s_beg

    @property
    def s_end(self):
        return self._elements[-1].s_end

    def plot_floor(self, axis='equal', ax=None):

        if(ax == None):
            ax = plt.gca()

        orbit = self.orbit_ref

        ax.plot(orbit[2], orbit[0], 'k')
        ax.set_xlabel('z (m)')
        ax.set_ylabel('x (m)')

        for ele in self._elements:
            ele.plot_floor(ax=ax, axis=axis)

        if(axis=='equal'):
            ax.set_aspect('equal')

        return ax

    def __str__(self):

        ostr = f'Lattice: {self._name}\ns-start: {self.s_beg} m.\ns-stop: {self.s_end}'
        for ele in self._elements:
            ostr = ostr+'\n\n'+ele.__str__()

        return ostr

    def get_M_at_s(self, s):
        pass


    def write_gpt_lines(self, template_file=None, output_file=None, slices=None):

        file_lines = []
        element_lines = []

        if(slices is None):
            elements = self._elements
        else:
            elements = self._elements[slices]

        # Write all the bend elements first
        for element in elements:
            if(is_bend(element)):
                for line in element.gpt_lines():
                    element_lines.append(line+'\n')

        for element in elements:
            if(not is_bend(element)):
                for line in element.gpt_lines():
                    element_lines.append(line+'\n')

        if(template_file is None):
            file_lines = BASIC_TEMPLATE

        else:

            assert os.path.exists(template_file), f'Template GPT file "template_file" does not exist.'

            with open(template_file,'r') as fid:
                for line in fid:
                    file_lines.append(line)

        lines = file_lines + element_lines

        if(output_file is not None):

            with open(output_file,'w') as fid:
                for line in lines:
                    fid.write(line)

        return lines






















    








