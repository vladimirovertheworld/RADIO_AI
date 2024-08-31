#!/bin/bash

# Interactive GitHub Upload Script for RADIO.AI

# Set color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if we're in a git repository
in_git_repo() {
    git rev-parse --is-inside-work-tree > /dev/null 2>&1
}

# Function to prompt for user input
prompt_user() {
    read -p "$1: " response
    echo $response
}

# Check if git is installed
if ! command_exists git; then
    print_color $RED "Error: git is not installed. Please install git and try again."
    exit 1
fi

# Check if we're in a git repository
if ! in_git_repo; then
    print_color $RED "Error: This directory is not a git repository."
    init_repo=$(prompt_user "Would you like to initialize a git repository here? (y/n)")
    if [[ $init_repo == "y" ]]; then
        git init
        print_color $GREEN "Git repository initialized."
    else
        print_color $YELLOW "Exiting script. Please navigate to a git repository and try again."
        exit 1
    fi
fi

# Prompt for GitHub repository URL
github_url=$(prompt_user "Enter your GitHub repository URL")

# Check if remote origin already exists
if git remote get-url origin >/dev/null 2>&1; then
    print_color $YELLOW "Remote 'origin' already exists."
    change_remote=$(prompt_user "Would you like to change it? (y/n)")
    if [[ $change_remote == "y" ]]; then
        git remote set-url origin $github_url
        print_color $GREEN "Remote 'origin' updated to $github_url"
    fi
else
    git remote add origin $github_url
    print_color $GREEN "Remote 'origin' added: $github_url"
fi

# Check git status
print_color $BLUE "Checking git status..."
git status

# Prompt to add files
add_files=$(prompt_user "Would you like to add all files to git? (y/n)")
if [[ $add_files == "y" ]]; then
    git add .
    print_color $GREEN "All files added to git."
else
    print_color $YELLOW "No files added. You may need to add files manually before committing."
fi

# Prompt for commit message
commit_msg=$(prompt_user "Enter a commit message")

# Commit changes
print_color $BLUE "Committing changes..."
if git commit -m "$commit_msg"; then
    print_color $GREEN "Changes committed successfully."
else
    print_color $RED "Failed to commit changes. Please check your git configuration and try again."
    exit 1
fi

# Push to GitHub
print_color $BLUE "Pushing to GitHub..."
if git push -u origin master; then
    print_color $GREEN "Successfully pushed to GitHub!"
else
    print_color $RED "Failed to push to GitHub. Please check your repository permissions and try again."
    exit 1
fi

# Final message
print_color $GREEN "RADIO.AI project has been successfully uploaded to GitHub!"
print_color $YELLOW "Remember to keep your API keys and sensitive information secure. Make sure they are not uploaded to the public repository."
print_color $BLUE "You can now collaborate on your project through GitHub. Happy coding!"
