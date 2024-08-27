import os
from pathlib import Path
import subprocess
import sys
import requests
import threading
import time
import socket

# Function to run shell commands with error handling
def run_command(command, description, cwd=None):
    try:
        print(f"{description}...")
        subprocess.run(command, shell=True, check=True, cwd=cwd)
        print(f"{description}...Done")
    except subprocess.CalledProcessError as e:
        print(f"Error during {description}: {e}", file=sys.stderr)
        sys.exit(1)

# Define installation options
OPTIONS = {
    'UPDATE_COMFY_UI': True,
    'INSTALL_COMFYUI_MANAGER': True,
    'INSTALL_CUSTOM_NODES_DEPENDENCIES': True,
    'INSTALL_FLUX': True,
    'INSTALL_FLUX_API': True,
}

# Function to determine if the user is in China based on IP
def is_user_in_china():
    try:
        response = requests.get("http://ip-api.com/json/")
        data = response.json()
        if data['countryCode'] == 'CN':
            return True
    except Exception as e:
        print(f"Could not determine location: {e}", file=sys.stderr)
    return False

# Function to check if a virtual environment is valid
def is_venv_valid():
    if not Path("venv").exists():
        return False
    try:
        result = subprocess.run(["venv/bin/python", "-m", "pip", "show", "modelscope"], stdout=subprocess.PIPE)
        return result.returncode == 0
    except Exception:
        return False

# Function to download a model with retries
def download_model(command, description, file_path, cwd=None, retries=3):
    attempt = 0
    while attempt < retries:
        if Path(file_path).exists():
            print(f"{description} skipped, already exists.")
            return
        else:
            print(f"{description}... (Attempt {attempt + 1}/{retries})")
            try:
                subprocess.run(command, shell=True, check=True, cwd=cwd)
                print(f"{description}...Done")
                return
            except subprocess.CalledProcessError as e:
                print(f"Error during {description}: {e}", file=sys.stderr)
                attempt += 1

    print(f"Failed to download {file_path} after {retries} attempts.")
    sys.exit(1)

# Function to check if a step is already done
def is_step_done(step_name):
    return Path(f"{step_name}.done").exists()

# Function to mark all steps as done
def mark_steps_done(step_names):
    for step_name in step_names:
        Path(f"{step_name}.done").touch()

# Choose the correct Git repository URLs based on location
if is_user_in_china():
    GIT_REPO_COMFYUI = "https://gitee.com/honwee/ComfyUI.git"
    GIT_REPO_GGUF = "https://gitee.com/honwee/ComfyUI-GGUF.git"
    GIT_REPO_MANAGER = "https://gitee.com/honwee/ComfyUI-Manager.git"
    GIT_REPO_COMFYSCOPE = "https://gitee.com/honwee/comfyscope.git"
else:
    GIT_REPO_COMFYUI = "https://github.com/comfyanonymous/ComfyUI.git"
    GIT_REPO_GGUF = "https://github.com/city96/ComfyUI-GGUF.git"
    GIT_REPO_MANAGER = "https://github.com/ltdrdata/ComfyUI-Manager.git"
    GIT_REPO_COMFYSCOPE = "https://github.com/modelscope/comfyscope.git"

# Set workspace path
current_dir = subprocess.check_output("pwd", shell=True).decode().strip()
WORKSPACE = f"{current_dir}/ComfyUI"

# Define steps
completed_steps = []

# Step 1: Create and activate a virtual environment
if not is_step_done("venv_created"):
    if not is_venv_valid():
        run_command("python3 -m venv venv", "Creating virtual environment")
    run_command(". venv/bin/activate", "Activating virtual environment")
    run_command("pip install --upgrade pip", "Upgrading pip")
    run_command("pip install -r requirements.txt", "Installing dependencies from requirements.txt")
    completed_steps.append("venv_created")

# Step 2: Clone and update ComfyUI
if not is_step_done("comfyui_cloned"):
    if not Path(WORKSPACE).exists():
        run_command(f"git clone {GIT_REPO_COMFYUI}", "Cloning ComfyUI repository")
    else:
        run_command(f"cd {WORKSPACE}", "Changing directory to ComfyUI")
        if not is_step_done("comfyui_updated"):
            run_command("git pull", "Updating ComfyUI repository", cwd=WORKSPACE)
            completed_steps.append("comfyui_updated")
    completed_steps.append("comfyui_cloned")

# Step 3: Install FLUX-GGUF node
if OPTIONS['INSTALL_FLUX'] and not is_step_done("flux_gguf_installed"):
    flux_gguf_path = f"{WORKSPACE}/custom_nodes/ComfyUI-GGUF"
    if not Path(flux_gguf_path).exists():
        run_command(f"git clone {GIT_REPO_GGUF}", "Installing FLUX-GGUF node", cwd=f"{WORKSPACE}/custom_nodes")
    else:
        print("FLUX-GGUF node already exists, skipping installation.")
    completed_steps.append("flux_gguf_installed")

# Step 4: Install ComfyUI-Manager
if OPTIONS['INSTALL_COMFYUI_MANAGER'] and not is_step_done("comfyui_manager_installed"):
    if not Path(f"{WORKSPACE}/custom_nodes/ComfyUI-Manager").exists():
        run_command(f"git clone {GIT_REPO_MANAGER}", "Installing ComfyUI-Manager", cwd=f"{WORKSPACE}/custom_nodes")
    run_command(f"cd {WORKSPACE}/custom_nodes/ComfyUI-Manager && git pull", "Updating ComfyUI-Manager")
    completed_steps.append("comfyui_manager_installed")

# Step 5: Install FLUX-API node
if OPTIONS['INSTALL_FLUX_API'] and not is_step_done("flux_api_installed"):
    if not Path(f"{WORKSPACE}/custom_nodes/comfyscope").exists():
        run_command(f"git clone {GIT_REPO_COMFYSCOPE}", "Installing FLUX-API node", cwd=f"{WORKSPACE}/custom_nodes")
    run_command(f"cd {WORKSPACE}/custom_nodes/comfyscope && git pull", "Updating FLUX-API node")
    completed_steps.append("flux_api_installed")

# Step 6: Install custom nodes dependencies
if OPTIONS['INSTALL_CUSTOM_NODES_DEPENDENCIES'] and not is_step_done("custom_nodes_dependencies_installed"):
    script_path = "custom_nodes/ComfyUI-Manager/scripts/colab-dependencies.py"
    run_command(f"python {script_path}", "Installing custom nodes dependencies", cwd=WORKSPACE)
    completed_steps.append("custom_nodes_dependencies_installed")

# Step 7: Download models
models_to_download = [
    {
        "command": "modelscope download --model=AI-ModelScope/flux-fp8 --local_dir ./models/unet/ flux1-dev-fp8.safetensors",
        "description": "Downloading FLUX1-DEV FP8 model",
        "file_path": "./models/unet/flux1-dev-fp8.safetensors",
    },
    {
        "command": "modelscope download --model=AI-ModelScope/flux_text_encoders --local_dir ./models/clip/ clip_l.safetensors",
        "description": "Downloading CLIP-L encoder",
        "file_path": "./models/clip/clip_l.safetensors",
    },
    {
        "command": "modelscope download --model=AI-ModelScope/flux_text_encoders --local_dir ./models/clip/ t5xxl_fp8_e4m3fn.safetensors",
        "description": "Downloading T5-XXL FP8 encoder",
        "file_path": "./models/clip/t5xxl_fp8_e4m3fn.safetensors",
    },
    {
        "command": "modelscope download --model=AI-ModelScope/FLUX.1-dev --local_dir ./models/vae/ ae.safetensors",
        "description": "Downloading VAE model",
        "file_path": "./models/vae/ae.safetensors",
    },
    {
        "command": "modelscope download --model=FluxLora/flux-koda --local_dir ./models/loras/ araminta_k_flux_koda.safetensors",
        "description": "Downloading Araminta K Flux Koda LoRA",
        "file_path": "./models/loras/araminta_k_flux_koda.safetensors",
    },
    {
        "command": "modelscope download --model=FluxLora/Black-Myth-Wukong-FLUX-LoRA --local_dir ./models/loras/ pytorch_lora_weights.safetensors",
        "description": "Downloading Black Myth Wukong LoRA",
        "file_path": "./models/loras/pytorch_lora_weights.safetensors",
    },
    {
        "command": "modelscope download --model=FluxLora/FLUX1_wukong_lora --local_dir ./models/loras/ FLUX1_wukong_lora.safetensors",
        "description": "Downloading FLUX1 Wukong LoRA",
        "file_path": "./models/loras/FLUX1_wukong_lora.safetensors",
    },
    {
        "command": "modelscope download --model=FluxLora/flux-ip-adapter --local_dir ./models/xlabs/ipadapters/ flux-ip-adapter.safetensors",
        "description": "Downloading Flux IP Adapter",
        "file_path": "./models/xlabs/ipadapters/flux-ip-adapter.safetensors",
    },
    # {
    #     "command": "modelscope download --model=FluxLora/flux-ip-adapter --local_dir ./models/clip_vision/ clip_vision_l.safetensors",
    #     "description": "Downloading CLIP Vision Large",
    #     "file_path": "./models/clip_vision/clip_vision_l.safetensors",
    # },
]

for model in models_to_download:
    step_name = model["description"].replace(" ", "_").lower()
    if not is_step_done(step_name):
        download_model(
            command=model["command"],
            description=model["description"],
            file_path=model["file_path"],
            cwd=WORKSPACE
        )
        completed_steps.append(step_name)

# Step 8: Install cloudflared
if not is_step_done("cloudflared_installed"):
    run_command("wget https://modelscope.oss-cn-beijing.aliyuncs.com/resource/cloudflared-linux-amd64.deb", "Downloading cloudflared")
    run_command("dpkg -i cloudflared-linux-amd64.deb", "Installing cloudflared")
    completed_steps.append("cloudflared_installed")

# Function to start ComfyUI and cloudflared
def start_comfyui():
    print("Starting ComfyUI, this may take a few moments...")

    def iframe_thread(port):
        while True:
            time.sleep(0.5)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            if result == 0:
                break
            sock.close()
        print("\nComfyUI finished loading, trying to launch cloudflared (if it gets stuck here cloudflared is having issues)\n")

        p = subprocess.Popen(["cloudflared", "tunnel", "--url", "http://127.0.0.1:{}".format(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for line in p.stderr:
            l = line.decode()
            if "trycloudflare.com " in l:
                print("This is the URL to access ComfyUI:", l[l.find("http"):], end='')

    print("Launching ComfyUI... Please wait.")
    threading.Thread(target=iframe_thread, daemon=True, args=(8188,)).start()

    run_command("python main.py --dont-print-server", "Starting ComfyUI", cwd=WORKSPACE)

# Start ComfyUI and cloudflared
if not is_step_done("comfyui_started"):
    print("Starting ComfyUI...")
    start_comfyui()
    completed_steps.append("comfyui_started")

# Mark all completed steps
mark_steps_done(completed_steps)