#!/usr/bin/env python
#%%
import subprocess
import shlex
import json
import os
import numpy as np
import shutil
import matplotlib.pyplot as plt

#%%

UP = "Ni Cr Ti Mn Fe"
DN = "Ti Fe Ni Mn Cr"

UP2 = "Co Cr V Mn Fe"
DN2 = "V Fe Co Mn Cr"

UP3 = "F C B N O"
DN3 = "B O F N C"

UP4 = "Mo Mo Tc Ru Tc Ru"
DN4 = "Ru Ru Tc Mo Tc Mo"

UP5 = "Cr Cr Mn Fe Mn Fe"
DN5 = "Fe Fe Mn Cr Mn Cr"

UP6 = "Nb Tc Tc Tc"
DN6 = "Ru Mo Mo Mo"

UP7 = "Rh Nb Mo Mo"
DN7 = "Zr Ru Tc Tc"


def get_poscar(d, box, elements):
    nelements = len(elements.split())
    header = f"""generated
1
{d*nelements} 0 0
0 {box} 0
0 0 {box}
{elements}
{" 1" * nelements}

"""
    for fractionalpos in np.linspace(0, 1, num=nelements, endpoint=False):
        header += f"{fractionalpos} 0.5 0.5\n"
    return header


def run_and_extract(d, box, elements):
    rundir = "rundir/"
    with open(f"{rundir}/POSCAR", "w") as fh:
        fh.write(get_poscar(d, box, elements))

    cmd = "/mnt/c/Users/guido/opt/xtb/6.4.0/bin/xtb --gfn 0 --sp --acc 1e-4 --strict --norestart --json POSCAR"
    output = (
        subprocess.check_output(shlex.split(cmd), cwd=rundir, stderr=subprocess.DEVNULL)
        .decode("utf8")
        .split("\n")
    )
    with open(f"{rundir}/xtbout.json") as fh:
        return json.load(fh)["electronic energy"]
    total = float([_ for _ in output if ":: total energy" in _][0].strip().split()[3])
    disp = float(
        [_ for _ in output if ":: dispersion energy" in _][0].strip().split()[3]
    )
    repulsion = float(
        [_ for _ in output if ":: repulsion energy" in _][0].strip().split()[3]
    )
    return total - disp - repulsion


def run_and_extract(d, box, elements):
    rundir = "rundir/"
    shutil.rmtree(rundir)
    os.mkdir(rundir)
    with open(f"{rundir}/INCAR", "w") as fh:
        pass

    with open(f"{rundir}/POSCAR", "w") as fh:
        fh.write(get_poscar(d, box, elements))

    cmd = "mpirun -np 48  --use-hwthread-cpus /home/guido/opt/vasp/vasp.5.4.4.pl2/bin/vasp_std"
    env = os.environ
    env[
        "LD_LIBRARY_PATH"
    ] = "/opt/AMD/aocl/aocl-linux-aocc-2.2.0/lib/:/opt/AMD/aocc-compiler-2.3.0/lib/"
    with open(f"{rundir}/POTCAR", "w") as fhout:
        for element in elements.split():
            with open(f"/home/guido/opt/vasp/POT/{element}/POTCAR") as fh:
                content = fh.read()
            fhout.write(content)
    subprocess.check_output(
        shlex.split(cmd), cwd=rundir, stderr=subprocess.DEVNULL, env=env
    )
    with open(f"{rundir}/OUTCAR") as fh:
        lines = fh.readlines()

    try:
        TEWEN = float([_ for _ in lines if "TEWEN" in _][-1].strip().split()[-1])
        TOTEN = float([_ for _ in lines if "TOTEN" in _][-1].strip().split()[-2])
    except IndexError:
        print("".join(lines))
        raise

    print(d, box, elements, TOTEN - TEWEN)
    return TOTEN - TEWEN


def delta(d, box, elements1, elements2):
    try:
        return run_and_extract(d, box, elements1) - run_and_extract(d, box, elements2)
    except ValueError:
        pass


#%%
xs = np.append(np.arange(1, 3, 0.1), np.arange(3, 10, 1))
#ys1_5 = [delta(_, 5, UP, DN) for _ in xs]
#ys1_20 = [delta(_, 20, UP, DN) for _ in xs]
# ys1_50 = [delta(_, 50, UP, DN) for _ in xs]
#ys2_50 = [delta(_, 20, UP2, DN2) for _ in xs]
#ys3_50 = [delta(_, 20, UP3, DN3) for _ in xs]
#ys4_50 = [delta(_, 20, UP4, DN4) for _ in xs]
#ys5_50 = [delta(_, 20, UP5, DN5) for _ in xs]
ys6_50 = [delta(_, 20, UP6, DN6) for _ in xs]
ys7_50 = [delta(_, 20, UP7, DN7) for _ in xs]
#np.savetxt("vaspout.txt", np.vstack((xs, ys1_50, ys2_50, ys3_50, ys4_50, ys5_50)).T)
print(1 / 0)

# region
plt.axhline(0, color="grey")

plt.plot(xs, ys1_5, "o-")
plt.plot(xs, ys1_20, "o-")
plt.plot(xs, ys1_50, "o-")
# region
plt.title(
    "xTB-GFN0 non-self-consistent energy difference\n between alchemical enantiomers of a 1D string in 3D PBC\nseparated by 50 $\AA$."
)
plt.axhline(0, color="grey")

plt.plot(xs, np.array(ys1_50) * 1000, "o-", label=f"{UP}<->{DN}")
plt.plot(xs, np.array(ys2_50) * 1000, "o-", label=f"{UP2}<->{DN2}")
plt.plot(xs, np.array(ys3_50) * 1000, "o-", label=f"{UP3}<->{DN3}")
plt.plot(xs, np.array(ys4_50) * 1000, "o-", label=f"{UP4}<->{DN4}")
plt.plot(xs, np.array(ys5_50) * 1000, "o-", label=f"{UP5}<->{DN5}")
# bonding region from https://www.pnas.org/content/pnas/73/12/4290.full.pdf
plt.axvspan(2.45, 3.02, color="grey", alpha=0.2)
plt.ylim(-100, 100)
plt.ylabel("$\Delta E$ [mHa]")
plt.xlabel("Atom spacing [$\mathrm{\AA}$]")
plt.legend()


# region


def check_enantiomer_1d(elements):
    import basis_set_exchange as bse

    Zs = [bse.lut.element_Z_from_sym(_) for _ in elements]
    return np.average(Zs)


check_enantiomer_1d(UP4.split()), check_enantiomer_1d(DN4.split())


# region
# region

alpha = 2
Z = 6
xs = np.linspace(-5, 5, 500)
ys = (Z + 2) ** xs + 2 * (Z - 1) ** xs - (Z - 2) ** xs - 2 * (Z + 1) ** xs
ys = (Z + 3) ** xs + 3 * (Z - 1) ** xs - (Z - 3) ** xs - 3 * (Z + 1) ** xs

plt.semilogy(xs, abs(ys))
# region
alpha = 2
(Z + 2) ** alpha + 2 * (Z - 1) ** alpha - (Z - 2) ** alpha - 2 * (Z + 1) ** alpha
# region
def get_formation_energy(d, box, elements):
    total_e = run_and_extract(d, 50, elements)
    for element in elements.split():
        e = run_and_extract(100, 50, element)
        total_e -= e
    return total_e


for case in (UP, UP2, UP3, UP4, UP5):
    print(get_formation_energy(2, 50, case))

# region
for case in (DN, DN2, DN3, DN4, DN5):
    print(get_formation_energy(3, 50, case))
