import argparse
from pathlib import Path
from multiprocessing import Pool
import subprocess
import os
import sys

VINA_BIN = "/home/sarmad/.micromamba/envs/zinc/bin/vina"


def dock_ligand(args):

    ligand_path, receptor, config_file, out_dir = args

    base = ligand_path.stem

    out_file = out_dir / f"{base}_out.pdbqt"
    log_file = out_dir / f"{base}.log"

    if out_file.exists():
        print(f"Skipping {base} (already docked)")
        return

    cmd = [
        VINA_BIN,
        "--ligand", str(ligand_path),
        "--receptor", str(receptor),
        "--config", str(config_file),
        "--scoring", "vinardo",
        "--out", str(out_file),
        "--cpu", "1"
    ]

    print(f"Docking {base}...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        with open(log_file, "w") as f:
            f.write(result.stdout)
            f.write("\n")
            f.write(result.stderr)

        if result.returncode != 0:
            print(f"ERROR docking {base}")
        else:
            print(f"Finished {base}")

    except Exception as e:
        print(f"Exception docking {base}: {e}")


def main():

    parser = argparse.ArgumentParser(
        description="Batch docking with Vina (Vinardo scoring)"
    )

    parser.add_argument("--ligand_dir", required=True)
    parser.add_argument("--receptor", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--cpus", type=int, default=os.cpu_count())

    args = parser.parse_args()

    ligand_dir = Path(args.ligand_dir).expanduser().resolve()
    receptor = Path(args.receptor).expanduser().resolve()
    config_file = Path(args.config).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()

    if not ligand_dir.exists():
        sys.exit("Ligand directory does not exist")

    if not receptor.exists():
        sys.exit("Receptor file does not exist")

    if not config_file.exists():
        sys.exit("Config file does not exist")

    out_dir.mkdir(parents=True, exist_ok=True)

    ligands = list(ligand_dir.glob("*.pdbqt"))

    if not ligands:
        sys.exit("No ligand PDBQT files found")

    print(f"Found {len(ligands)} ligands")
    print(f"Using {args.cpus} CPUs")
    print("Scoring: Vinardo\n")

    jobs = [(lig, receptor, config_file, out_dir) for lig in ligands]

    with Pool(args.cpus) as pool:
        pool.map(dock_ligand, jobs)

    print("Docking completed")


if __name__ == "__main__":
    main()
