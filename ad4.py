import argparse
from pathlib import Path
from multiprocessing import Pool
import subprocess
import os

def dock_ligand(args):
    ligand_path, map_prefix, out_dir = args
    base = ligand_path.stem
    out_file = out_dir / f"{base}_out.pdbqt"
    log_file = out_dir / f"{base}.log"

    if out_file.exists():
        print(f"Skipping {base} (already docked)")
        return

    print(f"Docking {base}...")

    cmd = [
        #"directory to vina bin",
        "--ligand", str(ligand_path),
        "--maps", str(map_prefix),
        "--scoring", "ad4",
        "--out", str(out_file),
        "--cpu", "1"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ERROR docking {base}:\n{result.stderr}")
            return 
        with open(log_file, "w") as f:
            f.write(result.stdout)
        print(f"Finished docking {base}")
    except Exception as e:
        print(f"Skipping {base} due to error: {e}")


def worker(args):
    return dock_ligand(*args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ligand_dir", required=True, help="Folder with ligand PDBQT files")
    parser.add_argument("--map_prefix", required=True, help="Prefix of precomputed AD4 maps (without .A.map etc.)")
    parser.add_argument("--out_dir", required=True, help="Folder to save outputs")
    parser.add_argument("--cpus", type=int, default=os.cpu_count())
    args = parser.parse_args()

    ligand_dir = Path(args.ligand_dir).expanduser()
    map_prefix = Path(args.map_prefix).expanduser()
    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(exist_ok=True)
    num_cpus = args.cpus

    ligands = list(ligand_dir.glob("*.pdbqt"))
    print(f"Found {len(ligands)} ligands")

    jobs = [(lig, map_prefix, out_dir) for lig in ligands]

    with Pool(num_cpus) as pool:
        pool.map(dock_ligand, jobs)
