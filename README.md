# PROMFUZZ




## Overview

PROMFUZZ is an automated and scalable system that leverages LLM-driven, bug-oriented composite analysis to effectively identify functional bugs in smart contracts.

Its core design is based on three key insights:

1. **LLM-Driven Multi-Perspective Analysis**
2. **Dual-Stage Invariant Checker Generation**
3. **Bug-Oriented Fuzzing Engine**

---



## Install

### 0. Setup Requirements

- Docker
- Python 3.7+
- Pip



### 1. Build the fuzzing engine (Docker)

- See: [Build Instructions](./Engine/README.md)

- This step must be completed first since you need the container ID.


### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```


### 3. Configure your LLM API key

- Linux / macOS:

```bash
export OPENAI_API_KEY="your_api_key"
```

- Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "your_api_key"
```

- Get your API key from: https://platform.openai.com/account/api-keys


## Usage


- To run PROMFUZZ, use the following command:

```bash
python promfuzz.py \
    --input=<SOLIDITY_FILE_PATH> \
    --containerid=<ENGINE_CONTAINER_ID> \
    --enginetimeout=<ENGINE_TIMEOUT_IN_SECONDS>
```

- Example:

```bash
python promfuzz.py \
    --input=MyContract.sol \
    --containerid=ab12cd34ef56 \
    --enginetimeout=180

```


## Citation 
If you use PROMFUZZ in your research, please cite the following paper:

```
@inproceedings{promfuzz,  
  author = {Xingshuang Lin and Qinge Xie and Binbin Zhao and Yuan Tian and Saman Zonouz and Na Ruan and Jiliang Li and Raheem Beyah and Shouling Ji}, 
  title = {PROMFUZZ: Leveraging LLM-Driven and Bug-Oriented Composite Analysis for Detecting Functional Bugs in Smart Contracts},  
  booktitle = { {IEEE/ACM} International Conference on Automated Software Engineering ({ASE}) },  
  year = {2025},  
}
```
