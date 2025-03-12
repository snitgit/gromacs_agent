"""
Configuration constants and settings for GROMACS Copilot
"""

# Default settings
DEFAULT_WORKSPACE = "./md_workspace"
DEFAULT_MODEL = "gpt-4o"
DEFAULT_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

# Force fields
FORCE_FIELDS = {
    "AMBER99SB-ILDN": "amber99sb-ildn",
    "CHARMM36": "charmm36-feb2021",
    "GROMOS96 53a6": "gromos53a6",
    "OPLS-AA/L": "oplsaa"
}

# Water models
WATER_MODELS = ["spc", "tip3p", "tip4p"]

# Box types
BOX_TYPES = ["cubic", "dodecahedron", "octahedron"]

# MDP file types
MDP_TYPES = ["ions", "em", "nvt", "npt", "md"]

# Default MDP parameters
DEFAULT_MDP_PARAMS = {
    "ions": {
        "integrator": "steep",
        "emtol": 1000.0,
        "emstep": 0.01,
        "nsteps": 50000,
        "nstlist": 1,
        "cutoff-scheme": "Verlet",
        "ns_type": "grid",
        "coulombtype": "cutoff",
        "rcoulomb": 1.0,
        "rvdw": 1.0,
        "pbc": "xyz"
    },
    "em": {
        "integrator": "steep",
        "emtol": 1000.0,
        "emstep": 0.01,
        "nsteps": 50000,
        "nstlist": 1,
        "cutoff-scheme": "Verlet",
        "ns_type": "grid",
        "coulombtype": "PME",
        "rcoulomb": 1.0,
        "rvdw": 1.0,
        "pbc": "xyz"
    },
    "nvt": {
        "title": "Protein-ligand complex NVT equilibration",
        "define": "-DPOSRES",
        "integrator": "md",
        "nsteps": 50000,
        "dt": 0.002,
        "nstxout": 500,
        "nstvout": 500,
        "nstenergy": 500,
        "nstlog": 500,
        "continuation": "no",
        "constraint_algorithm": "lincs",
        "constraints": "h-bonds",
        "lincs_iter": 1,
        "lincs_order": 4,
        "cutoff-scheme": "Verlet",
        "ns_type": "grid",
        "nstlist": 10,
        "rcoulomb": 1.0,
        "rvdw": 1.0,
        "DispCorr": "EnerPres",
        "coulombtype": "PME",
        "pme_order": 4,
        "fourierspacing": 0.16,
        "tcoupl": "V-rescale",
        "tc-grps": "Protein Non-Protein",
        "tau_t": "0.1 0.1",
        "ref_t": "300 300",
        "pcoupl": "no",
        "pbc": "xyz",
        "gen_vel": "yes",
        "gen_temp": 300,
        "gen_seed": -1
    },
    "npt": {
        "title": "Protein-ligand complex NPT equilibration",
        "define": "-DPOSRES",
        "integrator": "md",
        "nsteps": 50000,
        "dt": 0.002,
        "nstxout": 500,
        "nstvout": 500,
        "nstenergy": 500,
        "nstlog": 500,
        "continuation": "yes",
        "constraint_algorithm": "lincs",
        "constraints": "h-bonds",
        "lincs_iter": 1,
        "lincs_order": 4,
        "cutoff-scheme": "Verlet",
        "ns_type": "grid",
        "nstlist": 10,
        "rcoulomb": 1.0,
        "rvdw": 1.0,
        "DispCorr": "EnerPres",
        "coulombtype": "PME",
        "pme_order": 4,
        "fourierspacing": 0.16,
        "tcoupl": "V-rescale",
        "tc-grps": "Protein Non-Protein",
        "tau_t": "0.1 0.1",
        "ref_t": "300 300",
        "pcoupl": "Parrinello-Rahman",
        "pcoupltype": "isotropic",
        "tau_p": 2.0,
        "ref_p": 1.0,
        "compressibility": 4.5e-5,
        "refcoord_scaling": "com",
        "pbc": "xyz",
        "gen_vel": "no"
    },
    "md": {
        "title": "Protein-ligand complex MD simulation",
        "integrator": "md",
        "nsteps": 5000000,  # Default 10 ns
        "dt": 0.002,
        "nstxout": 5000,
        "nstvout": 5000,
        "nstenergy": 5000,
        "nstlog": 5000,
        "nstxout-compressed": 5000,
        "compressed-x-grps": "System",
        "continuation": "yes",
        "constraint_algorithm": "lincs",
        "constraints": "h-bonds",
        "lincs_iter": 1,
        "lincs_order": 4,
        "cutoff-scheme": "Verlet",
        "ns_type": "grid",
        "nstlist": 10,
        "rcoulomb": 1.0,
        "rvdw": 1.0,
        "DispCorr": "EnerPres",
        "coulombtype": "PME",
        "pme_order": 4,
        "fourierspacing": 0.16,
        "tcoupl": "V-rescale",
        "tc-grps": "Protein Non-Protein",
        "tau_t": "0.1 0.1",
        "ref_t": "300 300",
        "pcoupl": "Parrinello-Rahman",
        "pcoupltype": "isotropic",
        "tau_p": 2.0,
        "ref_p": 1.0,
        "compressibility": 4.5e-5,
        "pbc": "xyz",
        "gen_vel": "no"
    }
}

# Standard residues list
STANDARD_RESIDUES = [
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE", 
    "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
    "HOH", "WAT", "TIP", "SOL", "NA", "CL", "K", "CA", "MG", "ZN"
]

# System message for LLM
SYSTEM_MESSAGE_ADVISOR = """You are an expert molecular dynamics (MD) assistant that helps run GROMACS simulations.
            
Your primary goal is to guide the user through setting up and running MD simulations for protein systems.
You have access to various functions to interact with GROMACS and manage simulations.

1. First, you should check if GROMACS is installed using check_gromacs_installation()
2. Guide the user through the entire MD workflow in these stages:
   - Setup: Get protein file and prepare workspace
   - Prepare Protein: Generate topology with appropriate force field
   - Solvation: Add water and ions to the system
   - Energy Minimization: Remove bad contacts
   - Equilibration: Equilibrate the system (NVT and NPT)
   - Production: Run the actual MD simulation
   - Analysis: Analyze results (RMSD, RMSF, etc.)
3. The default protocol is protein only, for other functions, switch to corresponding protocol first.
- MM/GBSA: switch_to_mmpbsa_protocol
- Protein-Ligand complex: set_ligand


IMPORTANT: When running GROMACS commands that require interactive group selection, ALWAYS use echo commands to pipe the selection to the GROMACS command. For example:
- Instead of: gmx rms -s md.tpr -f md.xtc -o rmsd.xvg
- Use: echo "Protein Protein" | gmx rms -s md.tpr -f md.xtc -o rmsd.xvg


For each step:
1. Explain what you're doing and why
2. Execute the necessary functions to perform the actions
3. Check the results and handle any errors
4. Ask the user for input when needed


When you reach a point where you're waiting for the user's response or you've completed
the current stage of the workflow, end your response with: "This is the final answer at this stage."

Always provide clear explanations for technical concepts, and guide the user through the
entire process from start to finish.
"""

SYSTEM_MESSAGE_AGENT = """You are an autonomous MD agent that runs GROMACS simulations for the user.

Your primary goal is to execute molecular dynamics simulations of proteins and protein-ligand systems as requested by the user. Take direct action, making reasonable default choices when parameters aren't specified.

1. First, check if GROMACS is installed using check_gromacs_installation()
2. Execute the MD workflow efficiently
3. The default protocol is protein only, for other functions, switch to corresponding protocol first.
- MM/GBSA: switch_to_mmpbsa_protocol
- Protein-Ligand complex: set_ligand

IMPORTANT: When running GROMACS commands that require interactive group selection, use echo commands:
- Use: echo "Protein Protein" | gmx rms -s md.tpr -f md.xtc -o rmsd.xvg

For each action:
1. Execute the necessary functions without asking for confirmation
2. Check results and solve problems autonomously
3. Explain what you're doing briefly but focus on execution
4. Only ask for input when absolutely necessary

Keep in mind:
- Select reasonable default parameters when not specified
- Handle protein-ligand systems automatically when detected

When you complete a stage or need user input, end with: "This is the final answer at this stage."

Focus on efficiently completing the requested simulation with minimal user intervention.
"""