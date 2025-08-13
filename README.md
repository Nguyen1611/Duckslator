# Duckslator Setup Guide

This step-by-step guide will help you set up the Duckslator project with Python, FFmpeg, and all necessary dependencies on macOS, Linux, or Windows (via WSL).

## Overview

Duckslator requires:
- Python 3.10.12 (managed with pyenv)
- FFmpeg for audio/video processing
- Virtual environment for Python dependencies
- Streamlit for the frontend
- Backend services for processing

---

## Step 1: Check System Requirements

### What You'll Need
- **Operating System**: macOS, Linux (Ubuntu/Debian), or Windows with WSL2
- **Admin Access**: sudo privileges on Linux/WSL, standard user on macOS
- **Git**: Must be installed on your system
- **Internet Connection**: For downloading packages

### macOS Users
Ensure Xcode Command Line Tools are installed:
```bash
xcode-select --install
```

### Windows Users
Use WSL2 with Ubuntu for best compatibility.

### Linux/WSL Users
Make sure your system is up to date:
```bash
sudo apt update && sudo apt upgrade -y
```

---

## Step 2: Install System Dependencies

### For macOS Users

First, install Homebrew if you don't have it:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then install the required packages:
```bash
brew update
brew install openssl readline sqlite3 xz zlib bzip2 git
```

### For Linux/WSL Users

Install build tools and development libraries:
```bash
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
  libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
  libffi-dev liblzma-dev ca-certificates git
```

**✅ Checkpoint**: You should now have all the basic build tools installed.

---

## Step 3: Install pyenv (Python Version Manager)

### Why pyenv?
pyenv allows you to easily install and switch between different Python versions. This project requires Python 3.10.12 specifically.

### Installation Options

#### Option A: Universal Installer (Recommended)
This works on all supported systems:
```bash
curl https://pyenv.run | bash
```

#### Option B: macOS with Homebrew
If you prefer using Homebrew on macOS:
```bash
brew install pyenv
brew install pyenv-virtualenv  # Optional but recommended
```

**✅ Checkpoint**: pyenv is now installed but not yet configured.

---

## Step 4: Configure Your Shell for pyenv

### What This Does
This step adds pyenv to your shell's PATH and enables automatic Python version switching.

### For macOS Users (zsh shell)

Add pyenv to your PATH in both login and interactive shells:

**Step 4a**: Configure login shell PATH:
```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >>~/.zprofile
echo '[[ -d "$PYENV_ROOT/bin" ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >>~/.zprofile
```

**Step 4b**: Configure interactive shell:
```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >>~/.zshrc
echo '[[ -d "$PYENV_ROOT/bin" ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >>~/.zshrc
echo 'eval "$(pyenv init - zsh)"' >>~/.zshrc
echo 'eval "$(pyenv virtualenv-init -)"' >>~/.zshrc
```

**Step 4c**: Apply the changes:
```bash
source ~/.zprofile 2>/dev/null || true
source ~/.zshrc
```

### For Linux/WSL Users (bash shell)

**Step 4a**: Configure bash:
```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >>~/.bashrc
echo 'if [ -d "$PYENV_ROOT/bin" ]; then export PATH="$PYENV_ROOT/bin:$PATH"; fi' >>~/.bashrc
echo 'eval "$(pyenv init - bash)"' >>~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >>~/.bashrc
```

**Step 4b**: Apply the changes:
```bash
source ~/.bashrc
```

### Verify Installation
Check that pyenv is working:
```bash
command -v pyenv
pyenv --version
```

**✅ Checkpoint**: You should see the pyenv path and version number.

---

## Step 5: Install Python 3.10.12

### Why This Version?
Duckslator is specifically designed to work with Python 3.10.12 for compatibility with all dependencies.

### Installation Process

### For Linux/WSL Users
Set build flags for proper library linking:
```bash
export CPPFLAGS="-I/usr/include"
export LDFLAGS="-L/usr/lib"
pyenv install 3.10.12
```

### For macOS Users
Set build flags for Homebrew libraries:
```bash
export LDFLAGS="-L$(brew --prefix openssl@3)/lib -L$(brew --prefix zlib)/lib -L$(brew --prefix bzip2)/lib -L$(brew --prefix readline)/lib"
export CPPFLAGS="-I$(brew --prefix openssl@3)/include -I$(brew --prefix zlib)/include -I$(brew --prefix bzip2)/include -I$(brew --prefix readline)/include"
pyenv install 3.10.12
```

### Set Project Python Version
Navigate to the Duckslator project and set the Python version:
```bash
cd /Users/vietbui/Desktop/Projects/QHacks_2025/Duckslator
pyenv local 3.10.12
```

### Verify Installation
```bash
python3 --version
```
You should see: `Python 3.10.12`

**✅ Checkpoint**: Python 3.10.12 is now installed and active in your project directory.

---

## Step 6: Create and Activate Virtual Environment

### Why Virtual Environment?
A virtual environment isolates your project's Python packages from your system Python, preventing conflicts.

### Create the Virtual Environment
In the Duckslator project directory (replace `your-project-path` with your actual path):
```bash
cd /path/to/your/project/Duckslator
python -m venv .venv
```

### Activate the Virtual Environment
```bash
source .venv/bin/activate
```

### Verify Activation
Your terminal prompt should now show `(.venv)` at the beginning, indicating the virtual environment is active.

### For Future Sessions
Remember to activate the virtual environment every time you work on the project:
```bash
source .venv/bin/activate
```

To deactivate when you're done:
```bash
deactivate
```

**✅ Checkpoint**: Your virtual environment is created and activated.

---

## Step 7: Install FFmpeg

### What is FFmpeg?
FFmpeg is required for audio and video processing in Duckslator.

### For Linux/WSL Users
```bash
sudo apt update
sudo apt install -y ffmpeg
```

### For macOS Users
```bash
brew install ffmpeg
```

### Alternative Method
If the above doesn't work, you can use the provided installation script:
```bash
chmod +x install_ffmpeg.sh
./install_ffmpeg.sh
```

### Verify Installation
```bash
ffmpeg -version
```
You should see FFmpeg version information.

**✅ Checkpoint**: FFmpeg is now installed and ready for use.

---

## Step 8: Install Python Dependencies

### Install Project Requirements
With your virtual environment activated:

**Step 8a**: Upgrade pip (recommended):
```bash
pip install --upgrade pip
```

**Step 8b**: Install all project dependencies:
```bash
pip install -r requirements.txt
```

This will install all the Python packages that Duckslator needs to run.

### Troubleshooting
If a package fails to install, make sure you have all the system dependencies from Step 2 installed, then try again.

**✅ Checkpoint**: All Python dependencies are installed in your virtual environment.

---

## Step 9: Configure Environment Variables (Optional)

### Why Environment Variables?
Some features might require API keys or configuration settings.

### Check for Environment File
Look for a `.env.example` file in the project:
```bash
ls -la | grep env
```

### Create Your Environment File
If there's a `.env.example` file:
```bash
cp .env.example .env
```

Then edit `.env` with your specific values:
```bash
nano .env  # or use your preferred text editor
```

### Note
If there's no `.env.example` file, you can skip this step for now. The project will let you know if any environment variables are needed when you run it.

**✅ Checkpoint**: Environment configuration is ready (if needed).

---

## Step 10: Run Duckslator

### Overview
Duckslator has two main components that need to run:
1. **Frontend**: A Streamlit web interface
2. **Backend**: Processing services

### Start the Frontend

**Step 10a**: Open a terminal and navigate to the frontend directory:
```bash
cd /path/to/your/project/Duckslator/frontend
```

**Step 10b**: Make sure your virtual environment is activated:
```bash
source ../.venv/bin/activate
```

**Step 10c**: Start the Streamlit frontend:
```bash
streamlit run Home.py
```

The frontend should open in your web browser at `http://localhost:8501`.

### Start the Backend (Optional)

If you need the backend services running:

**Step 10d**: Open a **new terminal** and navigate to the pipeline directory:
```bash
cd /path/to/your/project/Duckslator/pipeline
```

**Step 10e**: Activate the virtual environment in this terminal too:
```bash
source ../.venv/bin/activate
```

**Step 10f**: Start the backend (adjust the command based on your specific backend):
```bash
python backend.py
# or if you have a different main file:
# python main.py
# or if using uvicorn:
# uvicorn main:app --reload --port 8000
```

**✅ Checkpoint**: Duckslator is now running! You should be able to access the web interface.

---

## Step 11: Daily Development Workflow

### Starting Your Work Session

**Every time you work on Duckslator:**

1. **Navigate to the project**:
   ```bash
   cd /path/to/your/project/Duckslator
   ```

2. **Activate the virtual environment**:
   ```bash
   source .venv/bin/activate
   ```

3. **Start the frontend** (in one terminal):
   ```bash
   cd frontend
   streamlit run Home.py
   ```

4. **Start the backend** (in another terminal if needed):
   ```bash
   cd pipeline
   python backend.py
   ```

### Ending Your Work Session

1. **Stop the running services**: Press `Ctrl+C` in each terminal
2. **Deactivate the virtual environment**: 
   ```bash
   deactivate
   ```

### Adding New Dependencies

If you need to install new Python packages:
```bash
pip install package-name
pip freeze > requirements.txt  # Update the requirements file
```

**✅ Checkpoint**: You now know how to start and stop Duckslator for daily development.

---

## Step 12: Troubleshooting Common Issues

### Problem: "pyenv command not found"
**Solution**: 
1. Make sure you followed Step 4 completely
2. Open a new terminal window
3. Or manually run: `source ~/.zshrc` (macOS) or `source ~/.bashrc` (Linux)

### Problem: Wrong Python version showing
**Solution**:
1. Run `pyenv local 3.10.12` in the project directory
2. Make sure `~/.pyenv/shims` is early in your PATH
3. Open a new terminal

### Problem: "streamlit command not found"
**Solution**:
1. Make sure your virtual environment is activated: `source .venv/bin/activate`
2. If still not working, reinstall: `pip install streamlit`

### Problem: FFmpeg not found
**Solution**:
1. Reinstall FFmpeg using your package manager (Step 7)
2. Open a new terminal to refresh PATH
3. Verify with: `ffmpeg -version`

### Problem: pip installation errors
**Solution**:
1. Make sure you have all system dependencies from Step 2
2. Try upgrading pip: `pip install --upgrade pip`
3. On macOS, ensure Xcode Command Line Tools: `xcode-select --install`

### Problem: Virtual environment issues
**Solution**:
1. Delete the old environment: `rm -rf .venv`
2. Create a new one: `python -m venv .venv`
3. Activate it: `source .venv/bin/activate`
4. Reinstall dependencies: `pip install -r requirements.txt`

### Getting Help
If you're still having issues:
1. Check that you followed each step in order
2. Make sure all ✅ checkpoints passed
3. Try the setup process in a fresh terminal window

---

## Step 13: Project Maintenance

### Keep Your Project Organized

**Add to .gitignore**:
Create or update your `.gitignore` file to exclude:
```
.venv/
__pycache__/
*.pyc
.env
.streamlit/
*.log
```

### Lock Your Dependencies
After successfully installing everything, save the exact versions:
```bash
pip freeze > requirements-lock.txt
```

This creates a backup of your exact working environment.

### Backup Your Work
Regularly commit your changes to git:
```bash
git add .
git commit -m "Your commit message"
git push origin your-branch-name
```

**✅ Checkpoint**: Your project is properly maintained and organized.

---

## Quick Reference Commands

### Start Duckslator (Daily Use)
```bash
cd /path/to/your/project/Duckslator
source .venv/bin/activate
cd frontend && streamlit run Home.py
```

### Install New Package
```bash
source .venv/bin/activate
pip install package-name
pip freeze > requirements.txt
```

### Full Reset (If Something Goes Wrong)
```bash
cd /path/to/your/project/Duckslator
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🎉 You're All Set!

Duckslator should now be running successfully. If you followed all the steps and see the ✅ checkpoints, you're ready to start using the application!

**What's Next?**
- Open your web browser to `http://localhost:8501` to use Duckslator
- Explore the frontend interface
- Try uploading a video or audio file to test the translation features

**Need Help?**
- Review the troubleshooting section (Step 12)
- Make sure all previous steps completed successfully
- Check that both your virtual environment is active and all services are running

