#!/usr/bin/env python3
# GROMACS Molecular Dynamics LLM Agent
# Created by: ChatMol Team

import os
import sys
import subprocess
import time
import logging
import json
import argparse
import requests
import shutil
from enum import Enum, auto
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("md_agent.log"),
        # We'll handle console output through our custom print function
        # Keeping this commented as reference: logging.StreamHandler(sys.stdout)
    ]
)

# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    # Bright variants
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


def print_message(message: str, msg_type: str = "info", style: str = None, width: int = None):
    """
    Print a formatted message to the console
    
    Args:
        message: The message to print
        msg_type: Type of message (info, success, warning, error, title, system, user, command, tool, final)
        style: Optional additional styling (box, divider)
        width: Width of the message box (defaults to terminal width)
    """
    # Get terminal width if not specified
    if not width:
        try:
            width = shutil.get_terminal_size().columns
        except:
            width = 80
    
    # Configure colors and prefixes based on message type
    if msg_type == "info":
        color = Colors.CYAN
        prefix = "ℹ️  INFO    │ "
    elif msg_type == "success":
        color = Colors.GREEN
        prefix = "✓  SUCCESS │ "
    elif msg_type == "warning":
        color = Colors.YELLOW
        prefix = "⚠️  WARNING │ "
    elif msg_type == "error":
        color = Colors.RED
        prefix = "✗  ERROR   │ "
    elif msg_type == "title":
        color = Colors.BRIGHT_BLUE + Colors.BOLD
        prefix = "🧪 "
    elif msg_type == "system":
        color = Colors.BRIGHT_MAGENTA
        prefix = "🤖 SYSTEM  │ "
    elif msg_type == "user":
        color = Colors.BRIGHT_CYAN
        prefix = "👤 USER    │ "
    elif msg_type == "command":
        color = Colors.BRIGHT_BLACK
        prefix = "$ "
    elif msg_type == "tool":
        color = Colors.BRIGHT_GREEN
        prefix = "🔧 TOOL    │ "
    elif msg_type == "final":
        color = Colors.BRIGHT_GREEN + Colors.BOLD
        prefix = "🏁 FINAL   │ "
    else:
        color = ""
        prefix = ""
    
    # Apply styling
    if style == "box":
        box_width = width - 4  # Account for side margins
        print(f"{color}┌{'─' * box_width}┐{Colors.RESET}")
        
        # Split message into lines that fit within the box
        lines = []
        curr_line = ""
        
        for word in message.split():
            if len(curr_line) + len(word) + 1 <= box_width - 4:  # -4 for margins
                curr_line += word + " "
            else:
                lines.append(curr_line)
                curr_line = word + " "
        if curr_line:
            lines.append(curr_line)
        
        # Print each line within the box
        for line in lines:
            padding = box_width - len(line) - 2
            print(f"{color}│ {line}{' ' * padding} │{Colors.RESET}")
        
        print(f"{color}└{'─' * box_width}┘{Colors.RESET}")
    
    elif style == "divider":
        print(f"{color}{'═' * width}{Colors.RESET}")
        print(f"{color}{prefix}{message}{Colors.RESET}")
        print(f"{color}{'═' * width}{Colors.RESET}")
    
    else:
        # Basic formatting with prefix
        print(f"{color}{prefix}{message}{Colors.RESET}")

# Use our custom print function for log output
class CustomLogHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        if record.levelno >= logging.ERROR:
            print_message(msg, "error")
        elif record.levelno >= logging.WARNING:
            print_message(msg, "warning")
        else:
            print_message(msg, "info")

class SimulationStage(Enum):
    """Stages of the MD simulation workflow"""
    SETUP = auto()
    PREPARE_PROTEIN = auto()
    SOLVATION = auto()
    ENERGY_MINIMIZATION = auto()
    EQUILIBRATION = auto()
    PRODUCTION = auto()
    ANALYSIS = auto()
    COMPLETED = auto()


class MolecularDynamicsTools:
    """Tools that can be called by the LLM agent to run MD simulations with GROMACS"""
    
    def __init__(self, workspace: str = "./md_workspace"):
        """
        Initialize the MD tools
        
        Args:
            workspace: Directory to use as the working directory
        """
        self.workspace = os.path.abspath(workspace)
        self.stage = SimulationStage.SETUP
        self.protein_file = None
        self.topology_file = None
        self.box_file = None
        self.solvated_file = None
        self.minimized_file = None
        self.equilibrated_file = None
        self.production_file = None
        
        # Create workspace if it doesn't exist
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)
        
        # Change to workspace directory
        os.chdir(self.workspace)
        
        logging.info(f"MD Tools initialized with workspace: {self.workspace}")
    
    def run_shell_command(self, command: str, capture_output: bool = True) -> Dict[str, Any]:
        """
        Run a shell command
        
        Args:
            command: Shell command to run
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            Dictionary with command result information
        """
        logging.info(f"Running command: {command}")
        print_message(command, "command")
        
        try:
            if capture_output:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    check=False,
                    text=True,
                    capture_output=True
                )
                
                if result.returncode == 0:
                    # Only show partial output if it's too long
                    if len(result.stdout) > 500:
                        trimmed_output = result.stdout[:500] + "...\n[Output trimmed for brevity]"
                        print_message(f"Command succeeded with output:\n{trimmed_output}", "success")
                    elif result.stdout.strip():
                        print_message(f"Command succeeded with output:\n{result.stdout}", "success")
                    else:
                        print_message("Command succeeded with no output", "success")
                else:
                    print_message(f"Command failed with error:\n{result.stderr}", "error")
                
                return {
                    "success": result.returncode == 0,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "command": command
                }
            else:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    check=False
                )
                
                if result.returncode == 0:
                    print_message("Command succeeded", "success")
                else:
                    print_message("Command failed", "error")
                
                return {
                    "success": result.returncode == 0,
                    "return_code": result.returncode,
                    "stdout": "Output not captured",
                    "stderr": "Error output not captured",
                    "command": command
                }
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Command execution failed: {error_msg}")
            print_message(f"Command execution failed: {error_msg}", "error")
            return {
                "success": False,
                "return_code": 1,
                "stdout": "",
                "stderr": error_msg,
                "command": command,
                "error": error_msg
            }
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """
        Get information about the current workspace
        
        Returns:
            Dictionary with workspace information
        """
        try:
            files = os.listdir(self.workspace)
            
            # Get file sizes and modification times
            file_info = []
            for file in files:
                file_path = os.path.join(self.workspace, file)
                if os.path.isfile(file_path):
                    stats = os.stat(file_path)
                    file_info.append({
                        "name": file,
                        "size_bytes": stats.st_size,
                        "modified": time.ctime(stats.st_mtime),
                        "is_directory": False
                    })
                elif os.path.isdir(file_path):
                    file_info.append({
                        "name": file,
                        "is_directory": True,
                        "modified": time.ctime(os.path.getmtime(file_path))
                    })
            
            return {
                "success": True,
                "workspace_path": self.workspace,
                "current_stage": self.stage.name,
                "files": file_info,
                "protein_file": self.protein_file,
                "topology_file": self.topology_file,
                "box_file": self.box_file,
                "solvated_file": self.solvated_file,
                "minimized_file": self.minimized_file,
                "equilibrated_file": self.equilibrated_file,
                "production_file": self.production_file
            }
        except Exception as e:
            logging.error(f"Error getting workspace info: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "workspace_path": self.workspace,
                "current_stage": self.stage.name
            }
    
    def check_gromacs_installation(self) -> Dict[str, Any]:
        """
        Check if GROMACS is installed and available
        
        Returns:
            Dictionary with GROMACS installation information
        """
        result = self.run_shell_command("gmx --version", capture_output=True)
        
        if result["success"]:
            version_info = result["stdout"].strip()
            return {
                "success": True,
                "installed": True,
                "version": version_info
            }
        else:
            return {
                "success": False,
                "installed": False,
                "error": "GROMACS is not installed or not in PATH"
            }
    
    def set_protein_file(self, file_path: str) -> Dict[str, Any]:
        """
        Set and prepare the protein file for simulation
        
        Args:
            file_path: Path to the protein structure file (PDB or GRO)
            
        Returns:
            Dictionary with result information
        """
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"Protein file not found: {file_path}"
            }
        
        # Copy the protein file to the workspace if it's not already there
        basename = os.path.basename(file_path)
        self.protein_file = basename
        
        if os.path.abspath(file_path) != os.path.join(self.workspace, basename):
            copy_result = self.run_shell_command(f"cp {file_path} {self.workspace}/")
            if not copy_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to copy protein file to workspace: {copy_result['stderr']}"
                }
        
        # Create directories for topologies
        mkdir_result = self.run_shell_command("mkdir -p topologies")
        
        return {
            "success": True,
            "protein_file": self.protein_file,
            "file_path": os.path.join(self.workspace, self.protein_file)
        }
    
    def generate_topology(self, force_field: str, water_model: str = "spc") -> Dict[str, Any]:
        """
        Generate topology for the protein
        
        Args:
            force_field: Name of the force field to use
            water_model: Water model to use
            
        Returns:
            Dictionary with result information
        """
        if not self.protein_file:
            return {
                "success": False,
                "error": "No protein file has been set"
            }
        
        # Map user-friendly force field names to GROMACS internal names
        ff_map = {
            "AMBER99SB-ILDN": "amber99sb-ildn",
            "CHARMM36": "charmm36-feb2021",
            "GROMOS96 53a6": "gromos53a6",
            "OPLS-AA/L": "oplsaa"
        }
        
        if force_field not in ff_map:
            return {
                "success": False,
                "error": f"Unknown force field: {force_field}. Available options: {list(ff_map.keys())}"
            }
        
        ff_name = ff_map[force_field]
        
        # Generate topology
        cmd = f"gmx pdb2gmx -f {self.protein_file} -o protein.gro -p topology.top -i posre.itp -ff {ff_name} -water {water_model}"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to generate topology: {result['stderr']}"
            }
        
        self.topology_file = "topology.top"
        self.box_file = "protein.gro"
        
        return {
            "success": True,
            "topology_file": self.topology_file,
            "box_file": self.box_file,
            "force_field": force_field,
            "water_model": water_model
        }
    
    def define_simulation_box(self, distance: float = 1.0, box_type: str = "cubic") -> Dict[str, Any]:
        """
        Define the simulation box
        
        Args:
            distance: Minimum distance between protein and box edge (nm)
            box_type: Type of box (cubic, dodecahedron, octahedron)
            
        Returns:
            Dictionary with result information
        """
        if not self.box_file:
            return {
                "success": False,
                "error": "No protein structure file has been processed"
            }
        
        cmd = f"gmx editconf -f {self.box_file} -o box.gro -c -d {distance} -bt {box_type}"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to define simulation box: {result['stderr']}"
            }
        
        self.box_file = "box.gro"
        
        return {
            "success": True,
            "box_file": self.box_file,
            "distance": distance,
            "box_type": box_type
        }
    
    def solvate_system(self) -> Dict[str, Any]:
        """
        Solvate the protein in water
        
        Returns:
            Dictionary with result information
        """
        if not self.box_file or not self.topology_file:
            return {
                "success": False,
                "error": "Box file or topology file not defined"
            }
        
        cmd = f"gmx solvate -cp {self.box_file} -cs spc216.gro -o solvated.gro -p {self.topology_file}"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to solvate the protein: {result['stderr']}"
            }
        
        self.solvated_file = "solvated.gro"
        
        return {
            "success": True,
            "solvated_file": self.solvated_file
        }
    
    def create_mdp_file(self, mdp_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create an MDP parameter file for GROMACS
        
        Args:
            mdp_type: Type of MDP file (ions, em, nvt, npt, md)
            params: Optional override parameters
            
        Returns:
            Dictionary with result information
        """
        default_params = {
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
        
        if mdp_type not in default_params:
            return {
                "success": False,
                "error": f"Unknown MDP type: {mdp_type}. Available types: {list(default_params.keys())}"
            }
        
        # Start with default parameters for the specified type
        mdp_params = default_params[mdp_type].copy()
        
        # Override with user-provided parameters if any
        if params:
            mdp_params.update(params)
        
        # Create MDP file content
        mdp_content = f"; {mdp_type}.mdp - Generated by MD LLM Agent\n"
        for key, value in mdp_params.items():
            mdp_content += f"{key:<20} = {value}\n"
        
        # Write MDP file
        file_path = f"{mdp_type}.mdp"
        try:
            with open(file_path, "w") as f:
                f.write(mdp_content)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to write MDP file: {str(e)}"
            }
        
        return {
            "success": True,
            "file_path": file_path,
            "mdp_type": mdp_type,
            "params": mdp_params
        }
    
    def add_ions(self, concentration: float = .15, neutral: bool = True) -> Dict[str, Any]:
        """
        Add ions to the solvated system
        
        Args:
            concentration: Salt concentration in M
            neutral: Whether to neutralize the system
            
        Returns:
            Dictionary with result information
        """
        if not self.solvated_file or not self.topology_file:
            return {
                "success": False,
                "error": "Solvated file or topology file not defined"
            }
        
        # Create ions.mdp file
        ions_mdp = self.create_mdp_file("ions")
        if not ions_mdp["success"]:
            return ions_mdp
        
        # Prepare for adding ions
        cmd = f"gmx grompp -f ions.mdp -c {self.solvated_file} -p {self.topology_file} -o ions.tpr"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to prepare for adding ions: {result['stderr']}"
            }
        
        # Add ions
        neutral_flag = "-neutral" if neutral else ""
        cmd = f"echo 'SOL' | gmx genion -s ions.tpr -o solvated_ions.gro -p {self.topology_file} -pname NA -nname CL {neutral_flag} -conc {concentration}"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to add ions: {result['stderr']}"
            }
        
        self.solvated_file = "solvated_ions.gro"
        
        return {
            "success": True,
            "solvated_file": self.solvated_file,
            "concentration": concentration,
            "neutral": neutral
        }
    
    def run_energy_minimization(self) -> Dict[str, Any]:
        """
        Run energy minimization
        
        Returns:
            Dictionary with result information
        """
        if not self.solvated_file or not self.topology_file:
            return {
                "success": False,
                "error": "Solvated file or topology file not defined"
            }
        
        # Create em.mdp file
        em_mdp = self.create_mdp_file("em")
        if not em_mdp["success"]:
            return em_mdp
        
        # Generate tpr file for minimization
        cmd = f"gmx grompp -f em.mdp -c {self.solvated_file} -p {self.topology_file} -o em.tpr"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to prepare energy minimization: {result['stderr']}"
            }
        
        # Run energy minimization
        cmd = "gmx mdrun -v -deffnm em"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Energy minimization failed: {result['stderr']}"
            }
        
        self.minimized_file = "em.gro"
        
        return {
            "success": True,
            "minimized_file": self.minimized_file,
            "log_file": "em.log",
            "energy_file": "em.edr"
        }
    
    def run_nvt_equilibration(self) -> Dict[str, Any]:
        """
        Run NVT equilibration
        
        Returns:
            Dictionary with result information
        """
        if not self.minimized_file or not self.topology_file:
            return {
                "success": False,
                "error": "Minimized file or topology file not defined"
            }
        
        # Create nvt.mdp file
        nvt_mdp = self.create_mdp_file("nvt")
        if not nvt_mdp["success"]:
            return nvt_mdp
        
        # Generate tpr file for NVT equilibration
        cmd = f"gmx grompp -f nvt.mdp -c {self.minimized_file} -r {self.minimized_file} -p {self.topology_file} -o nvt.tpr"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to prepare NVT equilibration: {result['stderr']}"
            }
        
        # Run NVT equilibration
        cmd = "gmx mdrun -v -deffnm nvt"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"NVT equilibration failed: {result['stderr']}"
            }
        
        return {
            "success": True,
            "nvt_file": "nvt.gro",
            "nvt_checkpoint": "nvt.cpt",
            "log_file": "nvt.log",
            "energy_file": "nvt.edr"
        }
    
    def run_npt_equilibration(self) -> Dict[str, Any]:
        """
        Run NPT equilibration
        
        Returns:
            Dictionary with result information
        """
        # Create npt.mdp file
        npt_mdp = self.create_mdp_file("npt")
        if not npt_mdp["success"]:
            return npt_mdp
        
        # Generate tpr file for NPT equilibration
        cmd = "gmx grompp -f npt.mdp -c nvt.gro -r nvt.gro -t nvt.cpt -p topology.top -o npt.tpr"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to prepare NPT equilibration: {result['stderr']}"
            }
        
        # Run NPT equilibration
        cmd = "gmx mdrun -v -deffnm npt"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"NPT equilibration failed: {result['stderr']}"
            }
        
        self.equilibrated_file = "npt.gro"
        
        return {
            "success": True,
            "equilibrated_file": self.equilibrated_file,
            "npt_checkpoint": "npt.cpt",
            "log_file": "npt.log",
            "energy_file": "npt.edr"
        }
    
    def run_production_md(self, length_ns: float = 10.0) -> Dict[str, Any]:
        """
        Run production MD
        
        Args:
            length_ns: Length of the simulation in nanoseconds
            
        Returns:
            Dictionary with result information
        """
        if not self.equilibrated_file or not self.topology_file:
            return {
                "success": False,
                "error": "Equilibrated file or topology file not defined"
            }
        
        # Calculate number of steps (2 fs timestep)
        nsteps = int(length_ns * 1000000 / 2)
        
        # Create md.mdp file with custom steps
        md_mdp = self.create_mdp_file("md", {"nsteps": nsteps})
        if not md_mdp["success"]:
            return md_mdp
        
        # Generate tpr file for production MD
        cmd = f"gmx grompp -f md.mdp -c {self.equilibrated_file} -t npt.cpt -p {self.topology_file} -o md.tpr"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to prepare production MD: {result['stderr']}"
            }
        
        # Run production MD
        cmd = "gmx mdrun -v -deffnm md"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Production MD failed: {result['stderr']}"
            }
        
        self.production_file = "md.gro"
        
        return {
            "success": True,
            "production_file": self.production_file,
            "trajectory_file": "md.xtc",
            "log_file": "md.log",
            "energy_file": "md.edr",
            "length_ns": length_ns
        }
    
    def analyze_rmsd(self) -> Dict[str, Any]:
        """
        Perform RMSD analysis
        
        Returns:
            Dictionary with result information
        """
        cmd = "echo 'Protein Protein' | gmx rms -s md.tpr -f md.xtc -o analysis/rmsd.xvg -tu ns"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"RMSD analysis failed: {result['stderr']}"
            }
        
        return {
            "success": True,
            "output_file": "analysis/rmsd.xvg",
            "analysis_type": "RMSD"
        }
    
    def analyze_rmsf(self) -> Dict[str, Any]:
        """
        Perform RMSF analysis
        
        Returns:
            Dictionary with result information
        """
        cmd = "echo 'C-alpha' | gmx rmsf -s md.tpr -f md.xtc -o analysis/rmsf.xvg -res"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"RMSF analysis failed: {result['stderr']}"
            }
        
        return {
            "success": True,
            "output_file": "analysis/rmsf.xvg",
            "analysis_type": "RMSF"
        }
    
    def analyze_gyration(self) -> Dict[str, Any]:
        """
        Perform radius of gyration analysis
        
        Returns:
            Dictionary with result information
        """
        cmd = "echo 'Protein' | gmx gyrate -s md.tpr -f md.xtc -o analysis/gyrate.xvg"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Radius of gyration analysis failed: {result['stderr']}"
            }
        
        return {
            "success": True,
            "output_file": "analysis/gyrate.xvg",
            "analysis_type": "Radius of Gyration"
        }
    
    def analyze_hydrogen_bonds(self) -> Dict[str, Any]:
        """
        Perform hydrogen bond analysis
        
        Returns:
            Dictionary with result information
        """
        cmd = "gmx hbond -s md.tpr -f md.xtc -num hbnum.xvg < <(echo -e '1\n1')"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Hydrogen bond analysis failed: {result['stderr']}"
            }
        
        return {
            "success": True,
            "output_file": "analysis/hbnum.xvg",
            "analysis_type": "Hydrogen Bonds"
        }
    
    def analyze_secondary_structure(self) -> Dict[str, Any]:
        """
        Perform secondary structure analysis
        
        Returns:
            Dictionary with result information
        """
        cmd = "gmx dssp -s md.tpr -f md.xtc -o analysis/dssp.dat"
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Secondary structure analysis failed: {result['stderr']}"
            }
        
        return {
            "success": True,
            "output_file": "analysis/dssp.dat",
            "analysis_type": "Secondary Structure"
        }
 
class MDLLMAgent:
    """LLM-based agent for running molecular dynamics simulations with GROMACS"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o", workspace: str = "./md_workspace", url: str = "https://api.openai.com/v1/chat/completions"):
        """
        Initialize the MD LLM agent
        
        Args:
            api_key: API key for LLM service
            model: Model to use for LLM
            workspace: Directory to use as the working directory
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.url = url
        if not self.api_key:
            raise ValueError("API key is required. Provide as parameter or set OPENAI_API_KEY environment variable")
        
        self.model = model
        self.tools = MolecularDynamicsTools(workspace)
        self.conversation_history = []
        
        logging.info(f"MD LLM Agent initialized with model: {model}")
    
    def get_tool_schema(self) -> List[Dict[str, Any]]:
        """
        Get the schema for the tools available to the LLM
        
        Returns:
            List of tool schema dictionaries
        """
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "run_shell_command",
                    "description": "Run a shell command",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to run"
                            },
                            "capture_output": {
                                "type": "boolean",
                                "description": "Whether to capture stdout/stderr"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_workspace_info",
                    "description": "Get information about the current workspace",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_gromacs_installation",
                    "description": "Check if GROMACS is installed and available",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_protein_file",
                    "description": "Set and prepare the protein file for simulation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the protein structure file (PDB or GRO)"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_topology",
                    "description": "Generate topology for the protein",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "force_field": {
                                "type": "string",
                                "description": "Name of the force field to use",
                                "enum": ["AMBER99SB-ILDN", "CHARMM36", "GROMOS96 53a6", "OPLS-AA/L"]
                            },
                            "water_model": {
                                "type": "string",
                                "description": "Water model to use",
                                "enum": ["spc", "tip3p", "tip4p"]
                            }
                        },
                        "required": ["force_field"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "define_simulation_box",
                    "description": "Define the simulation box",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "distance": {
                                "type": "number",
                                "description": "Minimum distance between protein and box edge (nm)"
                            },
                            "box_type": {
                                "type": "string",
                                "description": "Type of box",
                                "enum": ["cubic", "dodecahedron", "octahedron"]
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "solvate_system",
                    "description": "Solvate the protein in water",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_mdp_file",
                    "description": "Create an MDP parameter file for GROMACS",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mdp_type": {
                                "type": "string",
                                "description": "Type of MDP file",
                                "enum": ["ions", "em", "nvt", "npt", "md"]
                            },
                            "params": {
                                "type": "object",
                                "description": "Optional override parameters"
                            }
                        },
                        "required": ["mdp_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_ions",
                    "description": "Add ions to the solvated system",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "concentration": {
                                "type": "number",
                                "description": "Salt concentration in M, default is 0.15"
                            },
                            "neutral": {
                                "type": "boolean",
                                "description": "Whether to neutralize the system"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_energy_minimization",
                    "description": "Run energy minimization",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_nvt_equilibration",
                    "description": "Run NVT equilibration",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_npt_equilibration",
                    "description": "Run NPT equilibration",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_production_md",
                    "description": "Run production MD",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "length_ns": {
                                "type": "number",
                                "description": "Length of the simulation in nanoseconds"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_rmsd",
                    "description": "Perform RMSD analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_rmsf",
                    "description": "Perform RMSF analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_gyration",
                    "description": "Perform radius of gyration analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_hydrogen_bonds",
                    "description": "Perform hydrogen bond analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_secondary_structure",
                    "description": "Perform secondary structure analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_simulation_stage",
                    "description": "Set the current simulation stage",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "stage": {
                                "type": "string",
                                "description": "Name of the stage to set",
                                "enum": [s.name for s in SimulationStage]
                            }
                        },
                        "required": ["stage"]
                    }
                }
            },
        ]
        
        return tools
    
    def call_llm(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Call the LLM with messages and tools
        
        Args:
            messages: List of message dictionaries
            tools: List of tool schema dictionaries
            
        Returns:
            LLM response
        """
        tools = tools or self.get_tool_schema()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "tools": tools
        }
        
        response = requests.post(
            self.url,
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            logging.error(f"LLM API error: {response.status_code} - {response.text}")
            raise Exception(f"LLM API error: {response.status_code} - {response.text}")
        
        return response.json()
    
    def execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call
        
        Args:
            tool_call: Tool call dictionary
            
        Returns:
            Result of the tool call
        """
        function_name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])
        
        if function_name == "ask_user":
            question = arguments.get("question", "")
            options = arguments.get("options", None)
            
            print("\n" + "="*80)
            print(f"MD AGENT QUESTION: {question}")
            
            if options:
                for i, option in enumerate(options, 1):
                    print(f"  {i}. {option}")
                
                while True:
                    try:
                        response = input("Please select an option (enter number): ")
                        option_idx = int(response) - 1
                        if 0 <= option_idx < len(options):
                            user_response = options[option_idx]
                            break
                        else:
                            print(f"Please enter a number between 1 and {len(options)}")
                    except ValueError:
                        print("Please enter a valid number")
            else:
                user_response = input("Your response: ")
            
            print("="*80 + "\n")
            logging.info(f"User was asked: {question}")
            logging.info(f"User responded: {user_response}")
            
            return {
                "success": True,
                "response": user_response
            }
        
        # Get the method from the tools class
        if hasattr(self.tools, function_name):
            method = getattr(self.tools, function_name)
            result = method(**arguments)
            return result
        else:
            return {
                "success": False,
                "error": f"Unknown function: {function_name}"
            }
    
    def run(self, starting_prompt: str = None) -> None:
        """
        Run the MD LLM agent
        
        Args:
            starting_prompt: Optional starting prompt for the LLM
        """
        # Initialize conversation with system message
        system_message = {
            "role": "system",
            "content": """You are an expert molecular dynamics (MD) assistant that helps run GROMACS simulations.
            
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
        }
        
        self.conversation_history = [system_message]
        
        # Add starting prompt if provided
        if starting_prompt:
            self.conversation_history.append({
                "role": "user",
                "content": starting_prompt
            })
        
        # Get initial response from LLM
        response = self.call_llm(self.conversation_history)
        
        # Main conversation loop
        while True:
            assistant_message = response["choices"][0]["message"]
            self.conversation_history.append(assistant_message)
            
            # Process tool calls if any
            if "tool_calls" in assistant_message:
                for tool_call in assistant_message["tool_calls"]:
                    # Execute the tool call
                    result = self.execute_tool_call(tool_call)
                    
                    # Add the tool call result to the conversation
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_call["function"]["name"],
                        "content": json.dumps(result)
                    })
                
                # Get next response from LLM
                response = self.call_llm(self.conversation_history)
                continue
            
            # Display the assistant's message
            content = assistant_message["content"]
            
            # Check if it's a final answer
            if "This is the final answer at this stage." in content:
                # Split at the final answer marker
                parts = content.split("This is the final answer at this stage.")
                
                # Print the main content normally
                print_message(parts[0].strip(), "info")
                
                # Print the final answer part with special formatting
                final_part = "This is the final answer at this stage." + parts[1]
                print_message(final_part.strip(), "final", style="box")
            else:
                # Regular message
                print_message(content, "info")
            
            # Check if we've reached a stopping point
            if "This is the final answer at this stage." in content:
                # Ask if the user wants to continue
                user_input = input(f"{Colors.BRIGHT_GREEN}Do you want to continue with the next stage? ([YES]/no): {Colors.RESET}")
                if user_input.lower() not in ["yes", "y", "continue", ""]:
                    print_message("Exiting the MD agent. Thank you for using GROMACS Copilot!", "success", style="box")
                    break
                
                # Ask for the next user prompt
                user_input = input(f"{Colors.BRIGHT_CYAN}What would you like to do next? {Colors.RESET}")
            else:
                # Normal user input
                user_input = input(f"{Colors.BRIGHT_CYAN}Your response: {Colors.RESET}")
            
            # Check for exit command
            if user_input.lower() in ["exit", "quit", "bye"]:
                print_message("Exiting the MD agent. Thank you for using GROMACS Copilot!", "success", style="box")
                break
            
            # Add user input to conversation
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Get next response from LLM
            response = self.call_llm(self.conversation_history)


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="GROMACS Copilot")
    parser.add_argument("--api-key", help="API key for LLM service")
    parser.add_argument("--url", help="The url of the LLM service, \ndeepseek: https://api.deepseek.com/chat/completions\nopenai: https://api.openai.com/v1/chat/completions", default="https://api.openai.com/v1/chat/completions")
    parser.add_argument("--model", default="gpt-4o", help="Model to use for LLM")
    parser.add_argument("--workspace", default="./md_workspace", help="Workspace directory")
    parser.add_argument("--prompt", help="Starting prompt for the LLM")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    args = parser.parse_args()
    
    # Disable colors if requested or if not in a terminal
    if args.no_color or not sys.stdout.isatty():
        for attr in dir(Colors):
            if not attr.startswith('__'):
                setattr(Colors, attr, '')
    
    # Display splash screen
    print_message("", style="divider")
    print_message("GROMACS Copilot", "title", style="box")
    print_message("A molecular dynamics simulation assistant powered by AI, created by the ChatMol Team.", "info")
    print_message("", style="divider")
    
    try:
        # Check for API key
        if args.url == "https://api.openai.com/v1/chat/completions":
            api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
        elif args.url == "https://api.deepseek.com/chat/completions":
            api_key = args.api_key or os.environ.get("DEEPSEEK_API_KEY")

        if not api_key:
            print_message("API key not found. Please provide an API key using --api-key or set the OPENAI_API_KEY or DEEPSEEK_API_KEY environment variable.", "error")
            sys.exit(1)
        
        # Create and run MD LLM agent
        print_message(f"Initializing with model: {args.model}", "info")
        print_message(f"Using workspace: {args.workspace}", "info")
        
        agent = MDLLMAgent(api_key=args.api_key, model=args.model, workspace=args.workspace, url=args.url)
        agent.run(starting_prompt=args.prompt)
        
    except KeyboardInterrupt:
        print_message("\nExiting the MD agent. Thank you for using GROMACS Copilot!", "success", style="box")
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error running MD LLM agent: {error_msg}")
        print_message(f"Error running MD LLM agent: {error_msg}", "error", style="box")

if __name__ == "__main__":
    main()