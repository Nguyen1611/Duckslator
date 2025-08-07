# Project README

## Prerequisites

Ensure that your system meets the following requirements before proceeding:
- Ubuntu or a compatible Linux distribution for window user we can use wsl
For macos we can use as it but remember some commandline here are for linux/ will update late
- Administrative privileges (sudo access)

## Step 1: Install Dependencies

Run the following commands to install the necessary system dependencies:
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

## Step 2: Install pyenv

Install pyenv by running the command below:
curl https://pyenv.run | bash

### Configure pyenv
Edit your ~/.bashrc file to add the following lines:
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"

Apply the changes by running:
source ~/.bashrc

## Step 3: Install Python 3.10.12

Use pyenv to install Python 3.10.12:
pyenv install 3.10.12

## Step 4: Use the .python-version File

Navigate to your project directory:
cd /path/to/your/project

Ensure the .python-version file specifies the correct Python version (3.10.12). To verify, run:
cat .python-version

Activate the specified Python version:
pyenv local 3.10.12

## Step 5: Create a Virtual Environment

Create a virtual environment for your project:
python -m venv venv

## Step 6: Activate the Virtual Environment

Activate the virtual environment using:
source venv/bin/activate

Once activated, you should see the virtual environment name in your terminal prompt.

## Step 7: Install FFmpeg

Make the script executable and run it:
chmod +x install_ffmpeg.sh
./install_ffmpeg.sh

## Step 8: Install Python Dependencies

Install all required Python packages:
pip install -r requirements.txt

## Step9: Spin up front end and backend
frontend: 
cd frontend 
streamlit run Home.py
backend
cd pipeline
