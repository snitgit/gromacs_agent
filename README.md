# GROMACS Copilot
Let LLM run your MDs.  
**The good news: You now have time to hang out with your cat. The bad news: You'll miss out on GROMACS' famous quotes.**

## Introduction  
This agent automates **MD simulations** for proteins in water using **GROMACS**. It sets up the system, runs simulations, and analyzes **RMSD, RMSF, Rg, H-bonds**, etc.  

[A demo of output report](./assets/report.pdf)

## How to Run  

### Before using a LLM
1. Install teh package
```bash
pip install git+https://github.com/ChatMol/gromacs_copilot.git
```
2. Prepare a working dir and a input pdb
```bash
mkdir md_workspace && cd md_workspace
wget https://files.rcsb.org/download/1PGA.pdb
grep -v HOH 1PGA.pdb > 1pga_protein.pdb
cd ..
```

### Using DeepSeek  
```bash
gmx_copilot --workspace md_workspace/ \
--prompt "setup simulation system for 1pga_protein.pdb in the workspace" \
--api-key $DEEPSEEK_API_KEY \
--model deepseek-chat \
--url https://api.deepseek.com/chat/completions
```  

### Using OpenAI  
```bash
gmx_copilot --workspace md_workspace/ \
--prompt "setup simulation system for 1pga_protein.pdb in the workspace" \
--api-key $OPENAI_API_KEY \
--model gpt-4o \
--url https://api.openai.com/v1/chat/completions
```  

The agent handles **system setup, simulation execution, and result analysis** automatically. 🚀


## License
This project is dual-licensed under:
- **GPLv3** (Open Source License)
- **Commercial License** (For proprietary use)

For commercial licensing, contact **jinyuansun_at_chatmol.org**.
