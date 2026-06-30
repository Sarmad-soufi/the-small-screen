import argparse
import subprocess
import multiprocessing
from pathlib import Path
from multiprocessing import Pool

GOLD_BIN = "/opt/programs/csd/ccdc-software/gold/GOLD/bin/gold_auto"

# Added the FITNESS FUNCTION block to explicitly call chemplp
GOLD_TEMPLATE = """GOLD CONFIGURATION FILE

DATA FILES
protein_datafile = {protein}
ligand_data_file {ligand} 10
param_file = DEFAULT
directory = {outdir}
tordist_file = DEFAULT
save_lone_pairs = 0

FITNESS FUNCTION
fitness_function = chemplp

FLOOD FILL
origin = 10.163 11.447 -8.171
radius = 15.0
do_cavity = 0

POPULATION
popsiz = 100
maxops = 100000
"""

def create_config(protein, ligand, out_dir, config_path):
    config_text = GOLD_TEMPLATE.format(
        protein=str(protein.resolve()),
        ligand=str(ligand.resolve()),
        outdir=str(out_dir.resolve())
    )
    config_path.write_text(config_text.strip())

def run_gold(job):
    ligand, protein, base_out = job
    lig_name = ligand.stem
    out_dir = base_out / lig_name
    
    worker_name = multiprocessing.current_process().name
    
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        config_file = out_dir / "gold.conf"
        
        create_config(protein, ligand, out_dir, config_file)
        
        cmd = [GOLD_BIN, str(config_file)]
        
        print(f"[{worker_name}] STARTING: Docking {lig_name}...", flush=True)
        
        # Run inside out_dir to prevent temp file collision
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=out_dir)
        
        # Save the Python subprocess stream to a separate debug file
        debug_file = out_dir / "subprocess_debug.log"
        with open(debug_file, "w") as f:
            f.write("--- STDOUT ---\n")
            f.write(result.stdout)
            f.write("\n--- STDERR ---\n")
            f.write(result.stderr)
        
        if result.returncode != 0:
            print(f"[{worker_name}] FAILED:   {lig_name} (See subprocess_debug.log)", flush=True)
            return False
        else:
            print(f"[{worker_name}] FINISHED: {lig_name}", flush=True)
            return True
            
    except Exception as e:
        print(f"[{worker_name}] ERROR on {lig_name}: {str(e)}", flush=True)
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ligand_dir", required=True)
    parser.add_argument("--receptor", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--cpus", type=int, default=8)
    args = parser.parse_args()

    ligand_dir = Path(args.ligand_dir).resolve()
    protein = Path(args.receptor).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    ligands = list(ligand_dir.glob("*.mol2"))
    if not ligands:
        raise RuntimeError("No ligands found in ligand_dir")

    print(f"Total ligands to dock: {len(ligands)}\n", flush=True)
    jobs = [(lig, protein, out_dir) for lig in ligands]

    success_count = 0
    with Pool(args.cpus) as pool:
        for success in pool.imap_unordered(run_gold, jobs):
            if success:
                success_count += 1
                
    print(f"\nAll jobs completed. Successfully processed {success_count}/{len(ligands)} ligands.", flush=True)

if __name__ == "__main__":
    main()
