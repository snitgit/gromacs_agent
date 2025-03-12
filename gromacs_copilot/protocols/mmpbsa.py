"""
MM-PBSA/GBSA binding free energy calculation protocol for GROMACS Copilot
"""

import os
import logging
from typing import Dict, Any, Optional, List

from gromacs_copilot.protocols.base import BaseProtocol
from gromacs_copilot.utils.shell import check_command_exists, run_shell_command


class MMPBSAProtocol(BaseProtocol):
    """Protocol for MM-PBSA/GBSA binding free energy calculations"""
    
    def __init__(self, workspace: str = "./md_workspace"):
        """
        Initialize the MM-PBSA protocol
        
        Args:
            workspace: Directory to use as the working directory
        """
        super().__init__(workspace)
        
        # Initialize MM-PBSA specific attributes
        self.trajectory_file = None
        self.topology_file = None
        self.index_file = None
        self.protein_group = None
        self.ligand_group = None
        self.complex_group = None
        self.mmpbsa_dir = os.path.join(workspace, "mmpbsa")
        
        # Create MM-PBSA directory if it doesn't exist
        if not os.path.exists(self.mmpbsa_dir):
            os.makedirs(self.mmpbsa_dir)
        
        logging.info(f"MM-PBSA protocol initialized with workspace: {self.workspace}")
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the protocol
        
        Returns:
            Dictionary with protocol state information
        """
        try:
            mmpbsa_files = []
            if os.path.exists(self.mmpbsa_dir):
                mmpbsa_files = os.listdir(self.mmpbsa_dir)
            
            return {
                "success": True,
                "workspace_path": self.workspace,
                "mmpbsa_directory": self.mmpbsa_dir,
                "trajectory_file": self.trajectory_file,
                "topology_file": self.topology_file,
                "index_file": self.index_file,
                "protein_group": self.protein_group,
                "ligand_group": self.ligand_group,
                "complex_group": self.complex_group,
                "mmpbsa_files": mmpbsa_files
            }
        except Exception as e:
            logging.error(f"Error getting MM-PBSA state: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "workspace_path": self.workspace
            }
    
    def check_mmpbsa_prerequisites(self) -> Dict[str, Any]:
        """
        Check if prerequisites for MM-PBSA analysis are met
        
        Returns:
            Dictionary with prerequisite check information
        """
        # Check GROMACS installation
        gromacs_result = run_shell_command("gmx --version", capture_output=True)
        gromacs_installed = gromacs_result["success"]
        
        # Check gmx_MMPBSA installation
        gmx_mmpbsa_installed = check_command_exists("gmx_MMPBSA")
        
        # Check for required files
        required_files = ["md.tpr", "md.xtc"]
        missing_files = [file for file in required_files if not os.path.exists(os.path.join(self.workspace, file))]
        
        if missing_files:
            return {
                "success": False,
                "installed": {
                    "gromacs": gromacs_installed,
                    "gmx_mmpbsa": gmx_mmpbsa_installed
                },
                "missing_files": missing_files,
                "error": f"Missing required files: {', '.join(missing_files)}"
            }
        
        # Set file paths if all required files exist
        self.trajectory_file = "md.xtc"
        self.topology_file = "md.tpr"
        
        return {
            "success": True,
            "installed": {
                "gromacs": gromacs_installed,
                "gmx_mmpbsa": gmx_mmpbsa_installed
            }
        }
    
    def create_mmpbsa_index_file(self, protein_selection: str = "Protein", 
                         ligand_selection: str = "LIG") -> Dict[str, Any]:
        """
        Create index file for MM-PBSA analysis
        
        Args:
            protein_selection: Selection for protein group
            ligand_selection: Selection for ligand group
            
        Returns:
            Dictionary with result information
        """
        if not os.path.exists(os.path.join(self.workspace, "md.tpr")):
            return {
                "success": False,
                "error": "Topology file not found"
            }
        
        # Create index file with protein and ligand groups
        cmd = f"""echo -e "name {protein_selection}\\nname {ligand_selection}\\n\\nq" | gmx make_ndx -f md.tpr -o mmpbsa/mmpbsa.ndx"""
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to create index file: {result['stderr']}"
            }
        
        # Get group numbers from the index file
        groups_cmd = "grep '\\[' mmpbsa/mmpbsa.ndx | grep -n '\\[' | awk '{print $1, $2, $3}'"
        groups_result = self.run_shell_command(groups_cmd)
        
        if not groups_result["success"]:
            return {
                "success": False,
                "error": f"Failed to extract group numbers: {groups_result['stderr']}"
            }
        
        # Parse the group numbers from output
        try:
            lines = groups_result["stdout"].strip().split('\n')
            group_dict = {}
            
            for line in lines:
                if ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        group_num = int(parts[0]) - 1  # Adjust for 0-based indexing
                        group_name = parts[1].strip()
                        group_dict[group_name] = group_num
            
            # Find protein and ligand groups
            # protein_group = None
            # ligand_group = None
            # complex_group = None
            
            # for group_name, group_num in group_dict.items():
            #     if protein_selection in group_name:
            #         protein_group = group_num
            #     if ligand_selection in group_name:
            #         ligand_group = group_num
            #     if f"{protein_selection} | {ligand_selection}" in group_name:
            #         complex_group = group_num
            
            # if protein_group is None or ligand_group is None or complex_group is None:
            #     return {
            #         "success": False,
            #         "error": f"Could not identify protein, ligand, or complex groups in index file"
            #     }
            
            # self.index_file = "mmpbsa/mmpbsa.ndx"
            # self.protein_group = protein_group
            # self.ligand_group = ligand_group
            # self.complex_group = complex_group
            group_dict["success"] = True
            return group_dict
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error parsing group numbers: {str(e)}"
            }
    
    def create_mmpbsa_input(self, method: str = "pb", 
                           startframe: int = 1, 
                           endframe: int = 1000, 
                           interval: int = 10,
                           ionic_strength: float = 0.15,
                           with_entropy: bool = False) -> Dict[str, Any]:
        """
        Create input file for MM-PBSA/GBSA calculation
        
        Args:
            method: Method to use (pb or gb)
            startframe: First frame to analyze
            endframe: Last frame to analyze
            interval: Interval between frames
            ionic_strength: Ionic strength for PB calculation
            with_entropy: Whether to include entropy calculation
            
        Returns:
            Dictionary with result information
        """
        try:
            mmpbsa_input = "&general\n"
            mmpbsa_input += f"  sys_name = Protein_Ligand\n"
            mmpbsa_input += f"  startframe = {startframe}\n"
            mmpbsa_input += f"  endframe = {endframe}\n"
            mmpbsa_input += f"  interval = {interval}\n"
            
            if with_entropy:
                mmpbsa_input += "  entropy = 1\n"
                mmpbsa_input += "  entropy_seg = 25\n"  # Number of frames for entropy calculation
            
            mmpbsa_input += "/\n\n"
            
            if method.lower() == "pb":
                mmpbsa_input += "&pb\n"
                mmpbsa_input += f"  istrng = {ionic_strength}\n"
                mmpbsa_input += "  fillratio = 4.0\n"
                mmpbsa_input += "  inp = 2\n"
                mmpbsa_input += "  radiopt = 0\n"
                mmpbsa_input += "/\n"
            elif method.lower() == "gb":
                mmpbsa_input += "&gb\n"
                mmpbsa_input += f"  saltcon = {ionic_strength}\n"
                mmpbsa_input += "  igb = 5\n"  # GB model (5 = OBC2)
                mmpbsa_input += "/\n"
            
            input_file_path = os.path.join(self.mmpbsa_dir, "mmpbsa.in")
            with open(input_file_path, "w") as f:
                f.write(mmpbsa_input)
            
            return {
                "success": True,
                "input_file": input_file_path,
                "method": method,
                "startframe": startframe,
                "endframe": endframe,
                "interval": interval,
                "with_entropy": with_entropy
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating MM-PBSA input file: {str(e)}"
            }
    
    def run_mmpbsa_calculation(self, 
                               ligand_mol_file: str, 
                               index_file: str,
                               topology_file: str,
                               protein_group: str,
                               ligand_group: str,
                               trajectory_file: str,
                               overwrite: bool = True, 
                               verbose: bool = True) -> Dict[str, Any]:
        """
        Run MM-PBSA/GBSA calculation
        
        Args:
            overwrite: Whether to overwrite existing output files
            verbose: Whether to print verbose output
            
        Returns:
            Dictionary with result information
        """
        if not index_file or not os.path.exists(os.path.join(self.workspace, index_file)):
            return {
                "success": False,
                "error": "Index file not found"
            }
        
        input_file = os.path.join(self.mmpbsa_dir, "mmpbsa.in")
        if not os.path.exists(input_file):
            return {
                "success": False,
                "error": "MM-PBSA input file not found. Run create_mmpbsa_input() first."
            }
        
        # Run gmx_MMPBSA
        overwrite_flag = "-O" if overwrite else ""
        # verbose_flag = "--verbose" if verbose else ""
        
        cmd = f"cd {self.workspace} && gmx_MMPBSA {overwrite_flag} -i {input_file} -cs {topology_file} -ci {index_file} -cg {protein_group} {ligand_group} -ct {trajectory_file} -lm {ligand_mol_file} -o {self.mmpbsa_dir}/FINAL_RESULTS_MMPBSA.dat -nogui"
        
        result = self.run_shell_command(cmd)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"MM-PBSA calculation failed: {result['stderr']}"
            }
        
        # Check if output file exists
        final_results = os.path.join(self.mmpbsa_dir, "FINAL_RESULTS_MMPBSA.dat")
        if not os.path.exists(final_results):
            return {
                "success": False,
                "error": "MM-PBSA calculation did not produce expected output file"
            }
        
        return {
            "success": True,
            "results_file": final_results,
            "output_dir": self.mmpbsa_dir
        }
    
    def check_prerequisites(self):
        pass
    
    def parse_mmpbsa_results(self) -> Dict[str, Any]:
        """
        Parse MM-PBSA/GBSA results
        
        Returns:
            Dictionary with parsed results
        """
        final_results = os.path.join(self.mmpbsa_dir, "results_FINAL_RESULTS_MMPBSA.dat")
        if not os.path.exists(final_results):
            return {
                "success": False,
                "error": "MM-PBSA results file not found"
            }
        
        try:
            # Read results file
            with open(final_results, "r") as f:
                lines = f.readlines()
            
            # Parse results
            results = {}
            data_block = False
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines and headers
                if not line or line.startswith("***") or line.startswith("==="):
                    continue
                
                # Start data block
                if line.startswith("DELTA TOTAL"):
                    data_block = True
                    continue
                
                if data_block and ":" in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        key = parts[0].strip()
                        value_parts = parts[1].strip().split()
                        
                        if len(value_parts) >= 3:
                            mean = float(value_parts[0])
                            std = float(value_parts[1])
                            std_err = float(value_parts[2])
                            
                            results[key] = {
                                "mean": mean,
                                "std": std,
                                "std_err": std_err
                            }
            
            # Extract binding energy components
            binding_energy = results.get("DELTA TOTAL", {}).get("mean", 0)
            van_der_waals = results.get("VDWAALS", {}).get("mean", 0)
            electrostatic = results.get("EEL", {}).get("mean", 0)
            polar_solvation = results.get("EGB/EPB", {}).get("mean", 0)
            non_polar_solvation = results.get("ESURF", {}).get("mean", 0)
            
            return {
                "success": True,
                "binding_energy": binding_energy,
                "components": {
                    "van_der_waals": van_der_waals,
                    "electrostatic": electrostatic,
                    "polar_solvation": polar_solvation,
                    "non_polar_solvation": non_polar_solvation
                },
                "detailed_results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error parsing MM-PBSA results: {str(e)}"
            }
    
    # def run_full_mmpbsa_analysis(self, 
    #                            protein_selection: str = "Protein", 
    #                            ligand_selection: str = "LIG",
    #                            method: str = "pb",
    #                            startframe: int = 1, 
    #                            endframe: int = 1000, 
    #                            interval: int = 10,
    #                            ionic_strength: float = 0.15,
    #                            with_entropy: bool = False) -> Dict[str, Any]:
    #     """
    #     Run full MM-PBSA/GBSA analysis workflow
        
    #     Args:
    #         protein_selection: Selection for protein group
    #         ligand_selection: Selection for ligand group
    #         method: Method to use (pb or gb)
    #         startframe: First frame to analyze
    #         endframe: Last frame to analyze
    #         interval: Interval between frames
    #         ionic_strength: Ionic strength for calculation
    #         with_entropy: Whether to include entropy calculation
            
    #     Returns:
    #         Dictionary with result information
    #     """
    #     # Check prerequisites
    #     prereq_result = self.check_prerequisites()
    #     if not prereq_result["success"]:
    #         return prereq_result
        
    #     if not prereq_result["installed"]["gmx_mmpbsa"]:
    #         return {
    #             "success": False,
    #             "error": "gmx_MMPBSA is not installed. Please install it with: conda install -c conda-forge gmx_mmpbsa"
    #         }
        
    #     # Create index file
    #     index_result = self.create_index_file(protein_selection, ligand_selection)
    #     if not index_result["success"]:
    #         return index_result
        
    #     # Create MM-PBSA input file
    #     input_result = self.create_mmpbsa_input(
    #         method=method,
    #         startframe=startframe,
    #         endframe=endframe,
    #         interval=interval,
    #         ionic_strength=ionic_strength,
    #         with_entropy=with_entropy
    #     )
    #     if not input_result["success"]:
    #         return input_result
        
    #     # Run MM-PBSA calculation
    #     calc_result = self.run_mmpbsa_calculation()
    #     if not calc_result["success"]:
    #         return calc_result
        
    #     # Parse results
    #     parse_result = self.parse_results()
    #     if not parse_result["success"]:
    #         return parse_result
        
    #     return {
    #         "success": True,
    #         "binding_energy": parse_result["binding_energy"],
    #         "components": parse_result["components"],
    #         "detailed_results": parse_result["detailed_results"],
    #         "results_file": calc_result["results_file"],
    #         "method": method,
    #         "with_entropy": with_entropy
    #     }