```markdown
# ComfySetup

A one-click setup tool for deploying and managing ComfyUI with FLUX support.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Model Downloads](#model-downloads)
- [Error Handling](#error-handling)
- [Contribution](#contribution)
- [License](#license)

## Introduction

ComfySetup is an automated tool designed to simplify the deployment and management of ComfyUI, a popular interface for machine learning tasks. This tool integrates FLUX nodes, handles model downloads, and includes error handling and progress tracking to ensure a smooth setup experience.

## Features

- **Automated Setup**: One-click setup for ComfyUI, including FLUX node installation.
- **Error Handling**: Built-in error detection and reporting to ensure reliable deployment.
- **Progress Tracking**: Step-by-step progress updates during installation and setup.
- **Model Management**: Automatically download and organize essential models for ComfyUI.
- **Cloudflare Integration**: Seamless integration with cloudflared for easy web access.

## Requirements

- Python 3.10 or higher
- Docker (optional for containerized deployment)
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/ComfySetup.git
   cd ComfySetup
   ```

2. **Install necessary dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the setup script**:
   ```bash
   python3 comfy_start.py
   ```

## Usage

After running the setup script, ComfyUI will be fully deployed with the necessary FLUX nodes and models.

- To start ComfyUI:
  ```bash
  python3 main.py --dont-print-server
  ```

- To access the UI via Cloudflare:
  - The script will provide a URL after launching the UI. Simply copy and paste it into your browser.

## Model Downloads

This tool automatically downloads and organizes the following models:

- **FLUX1-DEV**: FLUX.1-dev-gguf
- **T5-XXL Encoder**: t5xxl_fp16.safetensors
- **CLIP-L Encoder**: clip_l.safetensors
- **VAE Model**: ae.safetensors

You can modify the script to include additional models or adjust the download paths as needed.

## Error Handling

The setup script includes error handling to ensure that any issues encountered during installation or setup are clearly reported. If an error occurs, the script will terminate and print a detailed message to help diagnose the problem.

## Contribution

We welcome contributions! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed explanation of your changes.

Please make sure to follow the project's coding standards and include tests for new features.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
```
