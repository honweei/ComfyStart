

# ComfyUI Installation and Configuration Script

This script automates the installation and configuration of ComfyUI, including various plugins, models, and workflows. It is designed to streamline the setup process, especially for users who frequently need to set up new environments.

## Features

- Install and update ComfyUI
- Install and configure FLUX, FLUX-API, and ComfyUI Manager
- Install Chinese translation plugins for ComfyUI
- Download models and workflows based on configuration
- Flexible configuration through `config.json`

## Prerequisites

- Python 3.8 or higher
- Git
- Virtualenv

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.dev/honweei/ComfyStart.git
   cd ComfyStart
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the installation by editing `config.json`:
   - `UPDATE_COMFY_UI`: Whether to update ComfyUI.
   - `INSTALL_COMFYUI_MANAGER`: Whether to install ComfyUI Manager.
   - `INSTALL_CUSTOM_NODES_DEPENDENCIES`: Whether to install custom node dependencies.
   - `INSTALL_FLUX`: Whether to install the FLUX-GGUF node.
   - `INSTALL_FLUX_API`: Whether to install the FLUX-API node.
   - `DOWNLOAD_MODELS`: Whether to download models.
   - `MODELS`: List of models to download.
   - `WORKFLOWS`: List of workflows to download.

4. Run the script:
   ```bash
   python comfy_start.py
   ```

5. To download models later, run:
   ```bash
   python comfy_start.py down
   ```

## Configuration

- **config.json**: This file contains all the configurations needed for installation, including models and workflows to download. Make sure to update this file according to your requirements.

## Requirements

Refer to the `requirements.txt` file for all the necessary Python packages.

## Notes

- The script supports both GitHub and Gitee for downloading repositories, depending on the user's location.
- The script will automatically detect if ComfyUI is already installed and skip the installation steps if so.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
```

