import os
import json
from pathlib import Path
import subprocess
import sys
import requests

# Load configuration from config.json
def load_config(config_file="config.json"):
    try:
        with open(config_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Configuration file {config_file} not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing {config_file}: {e}", file=sys.stderr)
        sys.exit(1)

config = load_config()

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

# Function to download files to a specified directory
def download_file(url, save_path, description):
    try:
        print(f"{description}...")
        response = requests.get(url)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f"{description}...Done")
    except requests.exceptions.RequestException as e:
        print(f"Error during {description}: {e}", file=sys.stderr)
        sys.exit(1)

# Function to check if a step is already done
def is_step_done(step_name):
    return Path(f"{step_name}.done").exists()

# Function to mark all steps as done
def mark_steps_done(step_names):
    for step_name in step_names:
        Path(f"{step_name}.done").touch()

# Function to check if ComfyUI is installed and can be started directly
def is_comfyui_installed(workspace):
    if Path(workspace).exists() and Path(f"{workspace}/main.py").exists():
        return True
    return False

# Choose the correct Git repository URLs based on location
if is_user_in_china():
    GIT_REPO_COMFYUI = "https://gitee.com/honwee/ComfyUI.git"
    GIT_REPO_GGUF = "https://gitee.com/honwee/ComfyUI-GGUF.git"
    GIT_REPO_MANAGER = "https://gitee.com/honwee/ComfyUI-Manager.git"
    GIT_REPO_COMFYSCOPE = "https://gitee.com/honwee/comfyscope.git"
    GIT_REPO_TRANSLATION_CN = "https://gitee.com/honwee/AIGODLIKE-COMFYUI-TRANSLATION.git"
else:
    GIT_REPO_COMFYUI = "https://github.com/comfyanonymous/ComfyUI.git"
    GIT_REPO_GGUF = "https://github.com/city96/ComfyUI-GGUF.git"
    GIT_REPO_MANAGER = "https://github.com/ltdrdata/ComfyUI-Manager.git"
    GIT_REPO_COMFYSCOPE = "https://github.com/modelscope/comfyscope.git"
    GIT_REPO_TRANSLATION_CN = "https://github.com/AIGODLIKE/AIGODLIKE-COMFYUI-TRANSLATION.git"

# Function to check if ComfyUI exists and its source in the same level as ComfyStart
def check_comfyui_in_same_level(repo_url, comfy_start_dir):
    workspace = os.path.join(comfy_start_dir, "ComfyUI")
    if Path(workspace).exists():
        try:
            result = subprocess.run(["git", "remote", "-v"], cwd=workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            origin_url = result.stdout.decode().split('\n')[0].split()[1]
            if origin_url != repo_url:
                print(f"ComfyUI already exists but from a different source: {origin_url}")
                return False, workspace
            print(f"ComfyUI already exists and matches the source: {repo_url}")
            return True, workspace
        except Exception as e:
            print(f"Error checking ComfyUI source: {e}", file=sys.stderr)
            return False, workspace
    return False, workspace

# Set workspace path based on the current directory level
comfy_start_dir = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.join(comfy_start_dir, "ComfyUI")

# Step 0: Check if ComfyUI is already installed
if is_comfyui_installed(workspace):
    print("ComfyUI is already installed. Skipping installation steps and starting ComfyUI.")
    # Directly start ComfyUI
    run_command("python main.py --dont-print-server", "Starting ComfyUI", cwd=workspace)
else:
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
        exists, workspace = check_comfyui_in_same_level(GIT_REPO_COMFYUI, comfy_start_dir)
        if exists:
            print("ComfyUI already exists and is from the correct source, skipping clone/update.")
            completed_steps.append("comfyui_cloned")
        else:
            if not Path(workspace).exists():
                run_command(f"git clone {GIT_REPO_COMFYUI} {workspace}", "Cloning ComfyUI repository")
            else:
                run_command(f"cd {workspace}", "Changing directory to ComfyUI")
                if not is_step_done("comfyui_updated"):
                    run_command("git pull", "Updating ComfyUI repository", cwd=workspace)
                    completed_steps.append("comfyui_updated")
            completed_steps.append("comfyui_cloned")

    # Step 3: Install FLUX-GGUF node
    if config['INSTALL_FLUX'] and not is_step_done("flux_gguf_installed"):
        flux_gguf_path = f"{workspace}/custom_nodes/ComfyUI-GGUF"
        if not Path(flux_gguf_path).exists():
            run_command(f"git clone {GIT_REPO_GGUF}", "Installing FLUX-GGUF node", cwd=f"{workspace}/custom_nodes")
        else:
            print("FLUX-GGUF node already exists, skipping installation.")
        completed_steps.append("flux_gguf_installed")

    # Step 4: Install ComfyUI-Manager
    if config['INSTALL_COMFYUI_MANAGER'] and not is_step_done("comfyui_manager_installed"):
        if not Path(f"{workspace}/custom_nodes/ComfyUI-Manager").exists():
            run_command(f"git clone {GIT_REPO_MANAGER}", "Installing ComfyUI-Manager", cwd=f"{workspace}/custom_nodes")
        run_command(f"cd {workspace}/custom_nodes/ComfyUI-Manager && git pull", "Updating ComfyUI-Manager")
        completed_steps.append("comfyui_manager_installed")

    # Step 5: Install FLUX-API node
    if config['INSTALL_FLUX_API'] and not is_step_done("flux_api_installed"):
        if not Path(f"{workspace}/custom_nodes/comfyscope").exists():
            run_command(f"git clone {GIT_REPO_COMFYSCOPE}", "Installing FLUX-API node", cwd=f"{workspace}/custom_nodes")
        run_command(f"cd {workspace}/custom_nodes/comfyscope && git pull", "Updating FLUX-API node")
        completed_steps.append("flux_api_installed")

    # Step 6: Install custom nodes dependencies
    if config['INSTALL_CUSTOM_NODES_DEPENDENCIES'] and not is_step_done("custom_nodes_dependencies_installed"):
        script_path = "custom_nodes/ComfyUI-Manager/scripts/colab-dependencies.py"
        run_command(f"python {script_path}", "Installing custom nodes dependencies", cwd=workspace)
        completed_steps.append("custom_nodes_dependencies_installed")

    # Step 7: Install ComfyUI Chinese translation plugins (both Gitee and GitHub)
    if not is_step_done("comfyui_translation_installed"):
        run_command(f"git clone {GIT_REPO_TRANSLATION_CN}", 
                    "Installing ComfyUI Chinese translation plugin from Gitee", 
                    cwd=f"{workspace}/custom_nodes")
        run_command("git clone https://github.com/AIGODLIKE/AIGODLIKE-COMFYUI-TRANSLATION.git", 
                    "Installing ComfyUI Chinese translation plugin from GitHub", 
                    cwd=f"{workspace}/custom_nodes")
        completed_steps.append("comfyui_translation_installed")

    # Step 8: Download workflows to the specified directory
    if not is_step_done("workflows_downloaded"):
        workflows_dir = Path(workspace) / "user" / "default" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        for workflow_key, workflow_info in config['WORKFLOWS'].items():
            download_file(workflow_info['url'], workflows_dir / workflow_info['filename'], f"Downloading {workflow_info['filename']}")
        
        completed_steps.append("workflows_downloaded")

    # Mark all installation steps as done
    mark_steps_done(completed_steps)

    # Step 9: Start ComfyUI and cloudflared
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

        run_command("python main.py --dont-print-server", "Starting ComfyUI", cwd=workspace)

    if not is_step_done("comfyui_started"):
        print("Starting ComfyUI...")
        start_comfyui()
        completed_steps.append("comfyui_started")

    # Mark all completed steps
    mark_steps_done(completed_steps)

    # Ask user if they want to download models after installation
    user_input = input("Installation complete. Do you want to download models based on the current configuration? (y/n): ").strip().lower()
    if user_input == 'y':
        def download_models():
            print("Starting model download based on the current configuration...")
            if config['DOWNLOAD_MODELS']:
                for model_key, model_config in config['MODELS'].items():
                    if model_config['enabled']:  # Check if the model is selected for download
                        step_name = model_config["description"].replace(" ", "_").lower()
                        if not is_step_done(step_name):
                            download_model(
                                command=model_config["command"],
                                description=model_config["description"],
                                file_path=model_config["file_path"],
                                cwd=workspace
                            )
                            completed_steps.append(step_name)
                    else:
                        print(f"Skipping {model_config['description']} as per user configuration.")
            print("Model download complete.")
        
        download_models()
    else:
        print("Skipping model download. You can run `python your_script.py down` to download models later.")

# Check if the script is run to download models only
if len(sys.argv) > 1 and sys.argv[1] == "down":
    download_models()