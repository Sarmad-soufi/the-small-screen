import subprocess
from pathlib import Path

#container = Path("path to singularity container dir").expanduser()
#maps_dir = Path("path to grid maps dir").expanduser()
#ligand_dir = Path("path to ligand dir").expanduser()
#out_dir = Path("path to out dir").expanduser()

fld_file = "Sec16_sec13.maps.fld"  # inside /maps
out_dir.mkdir(parents=True, exist_ok=True)

ligands = list(ligand_dir.glob("*.pdbqt"))

if not ligands:
    raise FileNotFoundError(f"No PDBQT ligands found in {ligand_dir}")

for ligand_path in ligands:
    ligand_name = ligand_path.stem
    log_file = out_dir / f"{ligand_name}.log"

    cmd = [
        "singularity", "exec", "--nv",
        "-B", f"{maps_dir}:/maps",
        "-B", f"{ligand_dir}:/ligands",
        "-B", f"{out_dir}:/out",
        str(container),
        #"path to container directory",
        "--ffile", f"/maps/{fld_file}",
        "--lfile", f"/ligands/{ligand_path.name}",
        "--resnam", ligand_name,
        "--xmloutput", "1",
        "--gbest", "1",
        "--dlgoutput", "0"
    ]

    print(f"[INFO] Docking ligand {ligand_name}")
    print(f"[INFO] Command: {' '.join(cmd)}")

    with open(log_file, "w") as log:
        subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)

print("[INFO] Docking complete for all ligands.")
