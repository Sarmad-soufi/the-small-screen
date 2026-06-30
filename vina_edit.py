import argparse
from pathlib import Path
from multiprocessing import Pool
import subprocess
import os

def dock_ligand(args):

    ligand_path, conf, receptor, out_dir = args

    out_file = out_dir / f"{ligand_path.stem}_out.pdbqt"

    if out_file.exists():
        print (f"skipping {ligand_path.name} (already docked)")
        return

    print(f"Docking {ligand_path.name}...")

    cmd = [
        "vina",
        "--ligand", str(ligand_path),
        "--receptor", str(receptor),
        "--config", str(conf),
        "--out", str(out_file),
        "--cpu", "1"
    ] 

    try:
        subprocess.run(cmd, check=True)
        print(f"Finished {ligand_path.name}")
    except subprocess.CalledProcessError:
        print(f"Skipping bad ligand: {ligand_path.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--conf", required=True)
    parser.add_argument("--receptor", required=True)
    parser.add_argument("--ligand_dir", required=True)
    parser.add_argument("--cpus", type=int, default=os.cpu_count())
    args = parser.parse_args()

    conf = Path(args.conf).expanduser()
    receptor = Path(args.receptor).expanduser()
    ligand_dir = Path(args.ligand_dir).expanduser()
    num_cpus = args.cpus

    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)

    ligands = list(ligand_dir.glob("*.pdbqt"))
    print(f"Found {len(ligands)} ligands")

    jobs = [(lig, conf, receptor, out_dir) for lig in ligands]

    with Pool(num_cpus) as pool:
        pool.map(dock_ligand, jobs)


