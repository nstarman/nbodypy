"""
NAME:

   Evolve

PURPOSE:

   A prescription based code for evolving star cluster analytically

INPUT:

     cluster,pot,
     initial_true_anomaly=0,
     initial_time=0,
     final_time=30000,
     initial_time_step=1,
     output_frequency=1,
     critical_mass_fraction=0.01,
     critical_half_mass_radius=0.0,
     output_filename='output',
     output_datafile_extension='dat',
     output_infofile_extension='info',
     output_path='./Output/',
     integration_method='RK4',
     fast,write
OUTPUT:
    StarClusterSimulation

HISTORY:

   2019 - Hamid Ebrahimi et al. https://ui.adsabs.harvard.edu/abs/2019arXiv190405896E/abstract
   2019 - Webb (UofT) - wrote interface with nbodypy and replace orbit calculations with galpy.orbit

"""
#
# Import modules
# ----------------------------------------------------------------
from datetime import datetime
from os.path import join, abspath
from scipy.special import erf

import numpy as np
import sys
import time

from galpy import potential
from galpy.util import bovy_conversion

from ..nbodypy.orbit import integrate_orbit
from .simulation import StarClusterSimulation
from ..nbodypy.operations import *

r0=8.
v0=220.


#
# A function to calculate the elapsed time
# ----------------------------------------------------------------
def timeit(func):
    def timer(*args, **kwargs):
        before = time.time()
        func(*args, **kwargs)
        after = time.time()
        print('time: %s' % (after - before))

    return timer


#
# A function to show errors
# ----------------------------------------------------------------
def show_error_message(error_message):
    sys.stderr.write("\nError: %s\n\n" % error_message)
    sys.exit(0)


#
# Constants
# ----------------------------------------------------------------
class const():
    G = 4.3e-3
    rhoc00 = 0.055
    gamma = 0.11
    alpha = 2.2
    zeta = 0.1
    xi1 = 0.0142
    RevJ1 = 0.145
    z = 1.61
    x = 0.75
    N1 = 15000
    N2 = 12
    N3 = 15000
    f = 0.3
    delta1 = -0.09
    delta2 = -0.002
    tcon=3.086e13/(3600.0*24.0*365.0*1000000.0)

#
# Simulation
# ----------------------------------------------------------------
class Simulation(object):
    def __init__(self,cluster,pot=None,
                 initial_true_anomaly=0,
                 initial_time=0,
                 final_time=30000,
                 initial_time_step=1,
                 output_frequency=1,
                 critical_mass_fraction=0.01,
                 critical_half_mass_radius=0.0,
                 output_filename='output',
                 output_datafile_extension='dat',
                 output_infofile_extension='info',
                 output_path='./Output/',
                 integration_method='RK4',fast=False,write=False):

        self.step_counter = 0

        self.cluster=cluster
        self.pot=pot
        self.fast=fast
        self.write=write

        ts,o=integrate_orbit(self.cluster,self.pot,tfinal=final_time/1000.,nt=(final_time-initial_time)/initial_time_step)
        apogalactic_distance=self.cluster.orbit.rap()
        perigalactic_distance=self.cluster.orbit.rperi()


        #Find point-mass which yields the same potential at apogalacticon
        self.MG=-potential.evaluatePotentials(self.pot,apogalactic_distance/r0,0.,ro=r0,vo=v0)*(apogalactic_distance*1000.0)/const.G
        print('MG = ',self.MG)

        if not fast:
            self.rjnorm=potential.rtide(self.pot,self.cluster.orbit.R(ts)/r0,self.cluster.orbit.z(ts)/r0,M=1./bovy_conversion.mass_in_msol(ro=r0,vo=v0))*r0*1000.
            self.x=self.cluster.orbit.x(ts)
            self.y=self.cluster.orbit.y(ts)
            self.r=self.cluster.orbit.r(ts)
            print(ts[0]*bovy_conversion.time_in_Gyr(ro=r0,vo=v0),ts[-1]*bovy_conversion.time_in_Gyr(ro=r0,vo=v0),len(ts))

        # check for invalid arguments
        all_args = locals()
        for item in all_args:
            if item != 'self':
                if not isinstance(all_args[item], (int, str, float, object)):
                    show_error_message("'%s' has a wrong type!" % item)
                elif isinstance(all_args[item], (int, float)):
                    if all_args[item] < 0:
                        show_error_message("The value of '%s' must be greater than 0." % item)

        if final_time < initial_time:
            show_error_message("'final_time' must be larger than 'initial_time'!")

        # any parameter stored in self.state will change as cluster undergoes evolution
        self.state = dict()

        self.state['M'] = self.M0 = self.cluster.mtot
        self.mav0 = self.cluster.mmean
        self.state['N'] = self.N0 = self.M0 / self.mav0
        self.state['rh'] = self.rh0 = self.cluster.rm

        # initial core radius [CAUTION: for the Plummer model only!]
        self.state['rc'] = self.rc0 = 0.4 * self.rh0

        # initial virial radius [CAUTION: for the Plummer model only!]
        self.state['rv'] = self.rv0 = 1.3 * self.rh0

        # initial form factor
        self.state['kappa'] = self.kappa0 = self.rh0 / (4 * self.rv0)

        # initial energy (potential + kinetic)
        self.energy0 = -const.G * self.M0 ** 2 * self.kappa0 / self.rh0

        self.ra = 1000 * apogalactic_distance
        self.rp = 1000 * perigalactic_distance

        # eccentricity of the cluster orbit  
        self.e = (self.ra - self.rp) / (self.ra + self.rp)

        # semi-major axis of the cluster orbit
        self.a = (self.ra + self.rp) / 2.0

        if fast:

            # mean angular velocity of the cluster around the centre of the galaxy
            self.omega = np.sqrt(const.G * self.MG / self.a ** 3)
            self.omega *= const.tcon

            # orbital period of the cluster
            self.T = 2 * np.pi / self.omega

            # calculate the initial true anomaly "nu0" and initial phase
            if initial_true_anomaly < 0 or initial_true_anomaly > 2 * np.pi:
                show_error_message("'initial_true_anomaly' must be in the range [0, 2*pi] (inclusive).")
            self.nu0 = initial_true_anomaly
            self.E0, self.orbit_time0 = self.calculate_initial_phase_from_initial_true_anomaly(self.e,
                                                                                               self.omega,
                                                                                               self.nu0)

        # conversion factor of the core density
        self.rhoc0 = self.M0 * const.rhoc00 / self.rv0 ** 0.8

        self.state['t'] = self.t0 = initial_time
        self.tf = final_time
        self.state['dt'] = self.dt0 = initial_time_step
        self.output_frequency = output_frequency
        self.M_crit_frac = critical_mass_fraction
        self.M_crit = self.M_crit_frac * self.M0
        self.rh_crit = critical_half_mass_radius

        self.output_filename = output_filename
        self.output_infofile_extension = output_infofile_extension
        self.output_datafile_extension = output_datafile_extension
        self.output_path = output_path
        if self.write:
            self.__make_output_files()

        self.all_param_labels = ('t', 'M', 'rh', 'kappa', 'rc',
                                 'x', 'y', 'rJ', 'rv', 'Lambda', 'xi', 'trh',
                                 'mu', 'delta')

        self.output_param_labels = ('t', 'M', 'rh', 'rc', 'rJ', 'rv', 'x', 'y')
        self.output_format_string = '\t'.join(['{:+7.5e}'] * len(self.output_param_labels))
        self.header_format_string = '\t'.join(['{:^12}'] * len(self.output_param_labels))

        self.available_integration_methods = {'RK4': self.__RK4, 'EULER': self.__Euler}
        try:
            self.integrator_function = self.available_integration_methods[integration_method.upper()]
        except KeyError:
            show_error_message("'integration_method' must be either 'Euler' or 'RK4' (case-insensitive).")
        self.integration_method = integration_method

        self.dot_functions_list = [self.__t_dot, self.__M_dot, self.__rh_dot, self.__kappa_dot,
                                   self.__rc_dot]
        self.dot_functions = dict(zip(self.all_param_labels[:5], self.dot_functions_list))
        self.dot_functions_keys = self.dot_functions.keys()

        self.state = self.calculate_cluster_parameters(**self.state)

        self.simulation=StarClusterSimulation(t=self.state['t'],m=self.state['M'],rm=self.state['rh'],rc=self.state['rc'])

        print('INITIAL:')
        print(self.state['M'],self.state['rh'],self.state['rc'],self.energy0,self.state['kappa'],self.state['rJ'])

    # ----------------------------------------------------------------
    def __make_output_files(self):

        err_msg = """I could not make the '%s' as a result of an invalid filename or output path.
        Please specify a valid filename or output path and try again."""

        self.info_full_filename = join(self.output_path + self.output_filename) + '.' + self.output_infofile_extension
        try:
            with open(self.info_full_filename, 'w'):
                pass
        except IOError:
            show_error_message(err_msg % 'infofile')

        self.data_full_filename = join(self.output_path + self.output_filename) + '.' + self.output_datafile_extension
        try:
            with open(self.data_full_filename, 'w'):
                pass
        except IOError:
            show_error_message(err_msg % 'datafile')

    # ----------------------------------------------------------------
    def __write_info(self):
        with open(self.info_full_filename, 'a') as f:
            f.write('   initial number of stars: %s\n' % round(self.N0))
            f.write('     average mass of stars: %s [Msun]\n' % self.mav0)
            f.write('     initial mass of stars: %s [Msun]\n' % self.M0)
            f.write('  initial half-mass radius: %s [pc]\n' % self.rh0)
            f.write('      apogalactic distance: %s [pc]\n' % self.ra)
            f.write('     perigalactic distance: %s [pc]\n' % self.rp)
            if self.fast:
                f.write('      initial true anomaly: %s [rad]\n' % self.nu0)
            f.write('              eccentricity: %s\n' % self.e)
            if self.fast:
                f.write('     mean angular velocity: %s [Myr^-1]\n' % self.omega)
                f.write('            orbital period: %s [Myr]\n' % self.T)
            f.write('              initial time: %s [Myr]\n' % self.t0)
            f.write('                final time: %s [Myr]\n' % self.tf)
            f.write('         initial time step: %s [Myr]\n' % self.dt0)
            f.write('    critical mass fraction: %s\n' % self.M_crit_frac)
            f.write(' critical half-mass radius: %s\n' % self.rh_crit)
            f.write('               output path: %s\n' % abspath(self.output_path))
            f.write('           output filename: %s\n' % self.output_filename)
            f.write('output data file extension: %s\n' % self.output_datafile_extension)
            f.write('output info file extension: %s\n' % self.output_infofile_extension)
            f.write('        integration method: %s\n' % self.integration_method)
            f.write('        simulation started: %s\n' % datetime.now())

    # ----------------------------------------------------------------
    def __write_data(self, file):
        dat = [self.state[label] for label in self.output_param_labels]
        file.write(self.output_format_string.format(*dat) + '\n')

    # ----------------------------------------------------------------
    def __write_header_data(self, file):
        file.write(self.header_format_string.format(*self.output_param_labels) + '\n')

    # ----------------------------------------------------------------
    def calculate_initial_phase_from_initial_true_anomaly(self, e, omega, nu0):

        E0 = 2 * np.arctan(np.sqrt((1 - e) / (1 + e)) * np.tan(0.5 * nu0))
        if nu0 > np.pi:
            E0 += 2 * np.pi
        M0 = E0 - e * np.sin(E0)
        orbit_time0 = M0 / omega

        return E0, orbit_time0

    # ----------------------------------------------------------------
    def calculate_cluster_position_and_distance(self, time, tolerance=1e-10):

        E = M = self.omega * (time + self.orbit_time0)
        while abs(M + self.e * np.sin(E) - E) > tolerance:
            E += (M + self.e * np.sin(E) - E) / (1 - self.e * np.cos(E))

        x = self.a * (np.cos(E) - self.e)
        y = self.a * np.sin(E) * np.sqrt(1 - self.e ** 2)
        r = self.a * (1 - self.e * np.cos(E))

        return x, y, r

    # ----------------------------------------------------------------
    def __update_cluster_parameters_for_output(self):
        self.state['N'] = self.state['M'] / self.mav0
        if self.fast:
            x, y, r = self.calculate_cluster_position_and_distance(self.state['t'])
            self.state['rJ'] = (self.state['M'] / self.MG) ** (1 / 3) * (self.a * r ** 4 / (self.ra * self.rp + 2 * self.a * r)) ** (1 / 3)
        else:
            x, y, r = self.x[self.step_counter]*1000.,self.y[self.step_counter]*1000.,self.r[self.step_counter]*1000.
            self.state['rJ'] = self.rjnorm[self.step_counter]*(self.state['M']**(1./3.))

        self.state['rv'] = self.state['rh'] / (4.0 * self.state['kappa'])
        self.state['x'] = x
        self.state['y'] = y

    # ----------------------------------------------------------------
    def calculate_cluster_parameters(self, **kwargs):

        # unpack args from kwargs        
        M = kwargs['M']
        N = M / self.mav0
        rh = kwargs['rh']
        rc = kwargs['rc']
        kappa = kwargs['kappa']


        if self.fast:
            # find the location of the cluster in the orbit 
            x, y, r = self.calculate_cluster_position_and_distance(kwargs['t'])
            rJ = (M / self.MG) ** (1 / 3) * (self.a * r ** 4 / (self.ra * self.rp + 2 * self.a * r)) ** (1 / 3)
        else:
            x, y, r = self.x[self.step_counter]*1000.,self.y[self.step_counter]*1000.,self.r[self.step_counter]*1000.
            rJ = self.rjnorm[self.step_counter]*(M**(1./3.))

        RehJ = rh / rJ
        Rech = rc / rh
        rv = rh / (4.0 * kappa)
        RevJ = rv / rJ
        trh = 0.138 * N ** 0.5 * rh ** 1.5 / (np.log(const.gamma * N) * np.sqrt(const.G * self.mav0))
        trh *= const.tcon

        Pe = (RevJ / const.RevJ1) ** const.z * ((N / const.N1) * np.log(const.gamma * const.N1) / np.log(
            const.gamma * N)) ** (1 - const.x) * ((1 - self.e ** 2.0) * (1 - 0.5 * self.e ** 2.0)) ** (- 1.0)

        # criterion to distinguish between pre- & post-collapse phase
        Rechmin = (const.N2 / N + const.N2 / const.N3) ** (2 / 3)

        # unbalanced (pre-collapse) evolution 
        if Rech > Rechmin:
            kappa0 = self.rh0 / (4 * self.rv0)
            kappa1 = 0.295
            Rech0 = 0.1
            Fe = Rechmin / Rech
            Ye = Rech / Rech0

            sigmac = np.sqrt(8 / 3 * np.pi * const.G * self.rhoc0 * rc ** (2 - const.alpha))
            rhoc = self.rhoc0 * rc ** (-const.alpha)
            trc = sigmac ** 3 / (15.4 * const.G ** 2 * self.mav0 * rhoc * np.log(const.gamma * N))
            trc *= const.tcon

            xi = Fe * const.xi1 * (1 - Pe) + (const.f + (1 - const.f) * Fe) * 3 / 5 * const.zeta * Pe
            delta = const.delta1 + const.delta2 * trh / trc
            Ke = 2 * Ye * (kappa0 - kappa1) * np.exp(-Ye ** 2) / (np.sqrt(np.pi) * kappa)
            mu = ((RehJ / kappa - 2) * xi + Ke * delta) / (1 + Ke)
            Lambda = Ke * (delta - mu)

        # balanced (post-collapse) evolution 
        else:
            kappa0 = 0.200
            kappa1 = 0.265
            Rech0 = 0.22
            Fe = 1.0
            Ye = Rech / Rech0

            xi = Fe * const.xi1 * (1.0 - Pe) + (const.f + (1 - const.f) * Fe) * 3.0 / 5.0 * const.zeta * Pe
            Ke = 2 * Ye * (kappa0 - kappa1) * np.exp(-Ye ** 2) / (np.sqrt(np.pi) * kappa)
            mu = const.zeta + xi * (2 / 3 * Ke / (1.0 + N / const.N3) - 2)
            delta = mu + 2 / 3 * xi / (1 + N / const.N3)
            kappaRech = kappa1 + (kappa0 - kappa1) * erf(Ye)
            Lambda = Ke * (delta - mu) + (kappaRech - kappa) / kappaRech

        for label in self.all_param_labels[5:]:
            kwargs[label] = eval(label)

        return kwargs

    # ----------------------------------------------------------------
    def __t_dot(self, state):
        return 1

    def __M_dot(self, state):
        return -1.0 * state['M'] * state['xi'] / state['trh']

    def __rh_dot(self, state):
        return state['rh'] * state['mu'] / state['trh']

    def __kappa_dot(self, state):
        return state['kappa'] * state['Lambda'] / state['trh']

    def __rc_dot(self, state):
        return state['rc'] * state['delta'] / state['trh']

    # ----------------------------------------------------------------
    def __add(self, cc, kk, **kwargs):
        for key in self.dot_functions_keys:
            kwargs[key] += (cc * kk[key])
        return kwargs

    # ----------------------------------------------------------------
    def __Euler(self, dt):

        params = self.calculate_cluster_parameters(**self.state)
        for key in self.dot_functions_keys:
            self.state[key] += (dt * self.dot_functions[key](params))

        self.__update_cluster_parameters_for_output()

    # ----------------------------------------------------------------
    def __RK4(self, dt):

        # RK4 coefficients
        K = [{}, {}, {}, {}, {}]
        cc = [1, 0.5, 0.5, 1]

        for j in range(4):
            if j == 0:
                params = self.__add(cc[j] * dt,
                                    {'t': 0, 'M': 0, 'rh': 0, 'kappa': 0, 'rc': 0},
                                    **self.state)
            else:
                params = self.__add(cc[j] * dt, K[j], **self.state)

            params = self.calculate_cluster_parameters(**params)

            for key in self.dot_functions_keys:
                K[j + 1][key] = self.dot_functions[key](params)

        for key in self.dot_functions_keys:
            self.state[key] += dt * (K[1][key] + 2 * (K[2][key] + K[3][key]) + K[4][key]) / 6.0

        self.__update_cluster_parameters_for_output()
    # ----------------------------------------------------------------
    @timeit
    def evolve_cluster(self):

        if self.write:
            self.__write_info()
            data_file=open(self.data_full_filename, 'a')
            self.__write_header_data(data_file)
            self.__write_data(data_file)

        self.step_counter = 0


        while self.state['t'] < self.tf and self.state['M'] >= self.M_crit and self.state['rh'] >= self.rh_crit:
            self.integrator_function(self.state['dt'])
            self.step_counter += 1
            if self.step_counter % self.output_frequency == 0:
                if self.write:
                    self.__write_data(data_file)
                #self.step_counter = 0

            self.simulation.add_snapshot(t=self.state['t'],m=self.state['M'],rm=self.state['rh'],rc=self.state['rc'])

        if self.write: 
            data_file.close()


#
# Main            
# ----------------------------------------------------------------
def simulate(cluster,pot=potential.MWPotential2014,tfinal=12000.,fast=False,write=False,**kwargs):

    units0,origin0=save_cluster(cluster)
    cluster.to_realpc()
    cluster.to_centre()

    sim=Simulation(cluster,pot,
    initial_true_anomaly=int(kwargs.get('initial_true_anomaly','0')),
    initial_time=int(kwargs.get('initial_time','0')),
    final_time=tfinal,
    initial_time_step=1,
    output_frequency=1,
    critical_mass_fraction=0.01,
    critical_half_mass_radius=0.0,
    output_filename='evolve',
    output_datafile_extension='dat',
    output_infofile_extension='info',
    output_path='',
    integration_method='RK4',
    fast=fast,write=write)

    sim.evolve_cluster()

    return_cluster(cluster,units0,origin0)

    return sim.simulation