#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 30 17:33:03 2019

@author: giorgiod
"""

import numpy as np
from horton import*
from co_scf_toNN import uhf

distance=1.*angstrom
pseudo_numbers=[6.,8.]
natoms=np.array([6,8] )

coordinates=np.array([[-distance/2.,0.,0.],[distance/2.,0.,0.]])

mol=IOData(title='CO')
mol.numbers=natoms
mol.coordinates=coordinates
mol.pseudo_numbers=pseudo_numbers

e_CO=uhf(distance,[6.,8.],'sto-3g',True)[0]
rho=uhf(distance,[6.,8.],'sto-3g',True)[1]

grid=grid.BeckeMolGrid(mol.coordinates,mol.numbers,mol.pseudo_numbers,random_rotate=False)
#r = (grid.points[:, 0]**2 + grid.points[:, 1]**2 + grid.points[:, 2]**2)**0.5
#ds1 = np.linalg.norm(grid.points - mol.coordinates[0], axis=1)

#V1 e V2 sono funzioni della griglia 
V1=((grid.points[:, 0]-mol.coordinates[0][0])**2+(grid.points[:, 1]-mol.coordinates[0][1])**2+(grid.points[:, 2]-mol.coordinates[0][2])**2)**-0.5
V2=((grid.points[:, 0]-mol.coordinates[1][0])**2+(grid.points[:, 1]-mol.coordinates[1][1])**2+(grid.points[:, 2]-mol.coordinates[1][2])**2)**-0.5
anm1=V2-V1

h=.1
dRho=(uhf(distance,[6.+h/2,8.-h/2],'sto-3g',True)[1]-uhf(distance,[6.-h/2,8.+h/2],'sto-3g',True)[1])/h

d1=grid.integrate(rho,anm1)
d2=grid.integrate(dRho,anm1)
