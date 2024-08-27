from pathlib import Path
import subprocess
import threading
import time
import socket
import sys
import requests

# Function to run shell commands with error handling
def run_command(command, description, cwd=None):
    try:
        print(f"{description}...")
        subprocess.run(command, shell=True, check=True, cwd=cwd)
        print(f"{description}...Done")
    except subprocess.CalledProcessError as e:
        print(f"Error during {description}: {e}", file=sys.stderr)
        sys.exit(1)

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

# Define installation options
OPTIONS = {}
UPDATE_COMFY_UI = True  # Option to update ComfyUI
INSTALL_COMFYUI_MANAGER = True  # Option to install ComfyUI Manager
INSTALL_CUSTOM_NODES_DEPENDENCIES = True  # Option to install custom node dependencies
INSTALL_FLUX = True  # Option to install FLUX
INSTALL_FLUX_API = True  # Option to install FLUX API

OPTIONS['UPDATE_COMFY_UI'] = UPDATE_COMFY_UI
OPTIONS['INSTALL_COMFYUI_MANAGER'] = INSTALL_COMFYUI_MANAGER
OPTIONS['INSTALL_FLUX'] = INSTALL_FLUX
OPTIONS['INSTALL_FLUX_API'] = INSTALL_FLUX_API
OPTIONS['INSTALL_CUSTOM_NODES_DEPENDENCIES'] = INSTALL_CUSTOM_NODES_DEPENDENCIES

# Set workspace path
current_dir = subprocess.check_output("pwd", shell=True).decode().strip()
WORKSPACE = f"{current_dir}/ComfyUI"

# Step 1: Create and activate a virtual environment
if not Path("venv").exists():
    run_command("python3 -m venv venv", "Creating virtual environment")

# Activate the virtual environment
activate_venv_command = ". venv/bin/activate"
run_command(activate_venv_command, "Activating virtual environment")

# Step 2: Upgrade pip and install necessary packages
run_command("pip install --upgrade pip", "Upgrading pip")
run_command("pip install modelscope", "Installing modelscope")

# Clone ComfyUI if not already cloned
if not Path(WORKSPACE).exists():
    run_command(f"git clone {GIT_REPO_COMFYUI}", "Step 2/8: Cloning ComfyUI repository")

run_command(f"cd {WORKSPACE}", "Changing directory to ComfyUI")

# Update ComfyUI if the option is selected
if OPTIONS['UPDATE_COMFY_UI']:
    run_command("git pull", "Updating ComfyUI repository")

# Install FLUX-GGUF node if the option is selected
if OPTIONS['INSTALL_FLUX']:
    run_command(f"cd {WORKSPACE}/custom_nodes && git clone {GIT_REPO_GGUF}", "Step 3/8: Installing FLUX-GGUF node")

# Install ComfyUI-Manager if the option is selected
if OPTIONS['INSTALL_COMFYUI_MANAGER']:
    if not Path(f"{WORKSPACE}/custom_nodes/ComfyUI-Manager").exists():
        run_command(f"cd {WORKSPACE}/custom_nodes && git clone {GIT_REPO_MANAGER}", "Step 4/8: Installing ComfyUI-Manager")
    run_command(f"cd {WORKSPACE}/custom_nodes/ComfyUI-Manager && git pull", "Updating ComfyUI-Manager")

# Install FLUX-API node if the option is selected
if OPTIONS['INSTALL_FLUX_API']:
    if not Path(f"{WORKSPACE}/custom_nodes/comfyscope").exists():
        run_command(f"cd {WORKSPACE}/custom_nodes && git clone {GIT_REPO_COMFYSCOPE}", "Step 5/8: Installing FLUX-API node")
    run_command(f"cd {WORKSPACE}/custom_nodes/comfyscope && git pull", "Updating FLUX-API node")

# Install custom nodes dependencies if the option is selected
if OPTIONS['INSTALL_CUSTOM_NODES_DEPENDENCIES']:
    script_path = "custom_nodes/ComfyUI-Manager/scripts/colab-dependencies.py"
    # 确保在 ComfyUI 根目录中执行
    run_command(f"python {script_path}", "Step 6/8: Installing custom nodes dependencies", cwd=WORKSPACE)

# Download models
run_command(f"cd {WORKSPACE}", "Changing directory to ComfyUI")
run_command("modelscope download --model=AI-ModelScope/FLUX.1-dev-gguf --local_dir ./models/unet/ flux1-dev-Q5_1.gguf", "Step 7/8: Downloading FLUX1-DEV model", cwd=WORKSPACE)
run_command("modelscope download --model=AI-ModelScope/flux_text_encoders --local_dir ./models/clip/ t5xxl_fp16.safetensors", "Downloading T5-XXL encoder", cwd=WORKSPACE)
run_command("modelscope download --model=AI-ModelScope/flux_text_encoders --local_dir ./models/clip/ clip_l.safetensors", "Downloading CLIP-L encoder", cwd=WORKSPACE)
run_command("modelscope download --model=AI-ModelScope/flux_text_encoders --local_dir ./models/clip/ t5xxl_fp8_e4m3fn.safetensors", "Downloading T5-XXL FP8 encoder", cwd=WORKSPACE)
run_command("modelscope download --model=AI-ModelScope/FLUX.1-dev --local_dir ./models/vae/ ae.safetensors", "Downloading VAE model", cwd=WORKSPACE)

# Install cloudflared
run_command("wget https://modelscope.oss-cn-beijing.aliyuncs.com/resource/cloudflared-linux-amd64.deb", "Step 8/8: Downloading cloudflared")
run_command("dpkg -i cloudflared-linux-amd64.deb", "Installing cloudflared")

# Function to start ComfyUI and cloudflared
def start_comfyui():
    # 正确的 ComfyUI 目录路径，使用 WORKSPACE 变量
    run_command(f"cd {WORKSPACE}", "Changing directory to ComfyUI")
    
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

    threading.Thread(target=iframe_thread, daemon=True, args=(8188,)).start()

    run_command("python main.py --dont-print-server", "Starting ComfyUI", cwd=WORKSPACE)

# Start ComfyUI and cloudflared
print("Starting ComfyUI...")
start_comfyui()