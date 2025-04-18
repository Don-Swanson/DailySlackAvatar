#!/usr/bin/env python3

# DailySlackAvatar - A tool to create and upload random Slack profile photos
# 
# This script takes a random PNG from a foreground folder and layers it on top 
# of a random PNG from a background folder to create unique daily Slack avatars.
# 
# Author: Created with assistance from Claude AI

import os
import random
from pathlib import Path
from PIL import Image
import argparse
import sys
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
import getpass

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, '.slack_config.json')

def save_slack_token(token):
    """Save the Slack token to a config file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'token': token}, f)
        os.chmod(CONFIG_FILE, 0o600)  # Set permissions to only allow the owner to read/write
        return True
    except Exception as e:
        print(f"Error saving token: {e}")
        return False

def get_slack_token():
    """Get the Slack token from environment variable or config file."""
    # First check environment variable
    token = os.environ.get("SLACK_USER_TOKEN")
    if token:
        return token
    
    # Then check config file
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('token')
    except Exception as e:
        print(f"Error reading token from config file: {e}")
    
    return None

def prompt_for_slack_token():
    """Prompt the user to enter their Slack token."""
    print("\nTo upload to Slack, you need to provide a Slack User OAuth Token with 'users.profile:write' scope.")
    print("Follow these steps to get your token:")
    print("1. Go to https://api.slack.com/apps")
    print("2. Create a new app (or use an existing one)")
    print("3. Go to 'OAuth & Permissions' and add 'users.profile:write' to 'User Token Scopes'")
    print("4. Install the app to your workspace")
    print("5. Copy the 'User OAuth Token' (starts with xoxp-)")
    
    token = getpass.getpass("\nEnter your Slack User OAuth Token: ")
    
    if not token:
        print("No token provided. Aborting upload.")
        return None
    
    save_token = input("Would you like to save this token for future use? (y/n): ").lower().strip() == 'y'
    
    if save_token:
        if save_slack_token(token):
            print("Token saved successfully!")
        else:
            print("Failed to save token. You'll need to enter it again next time.")
    
    return token

def get_random_image(folder_path):
    """Get a random PNG image from the specified folder."""
    # Convert relative path to absolute path based on script location
    abs_folder_path = os.path.join(SCRIPT_DIR, folder_path) if not os.path.isabs(folder_path) else folder_path
    
    # Ensure the directory exists
    if not os.path.exists(abs_folder_path):
        os.makedirs(abs_folder_path)
        raise FileNotFoundError(f"Created directory '{abs_folder_path}', but it's empty. Please add PNG images to this folder.")
    
    image_files = [f for f in os.listdir(abs_folder_path) if f.lower().endswith('.png')]
    
    if not image_files:
        raise FileNotFoundError(f"No PNG files found in '{abs_folder_path}'. Please add some PNG images to this folder.")
    
    random_image_path = os.path.join(abs_folder_path, random.choice(image_files))
    return random_image_path

def layer_images(foreground_path, background_path, output_path, slack_profile=False):
    """Layer the foreground image on top of the background image."""
    foreground = Image.open(foreground_path).convert("RGBA")
    background = Image.open(background_path).convert("RGBA")
    
    # Resize foreground to match background if they have different dimensions
    if foreground.size != background.size:
        foreground = foreground.resize(background.size, Image.LANCZOS)
    
    # Layer the images
    composite = Image.alpha_composite(background, foreground)
    
    # Process for Slack profile if requested
    if slack_profile:
        # Make sure the image is square
        width, height = composite.size
        size = max(width, height)
        
        # Create a new square image with transparent background
        square_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        
        # Paste the composite in the center
        paste_x = (size - width) // 2
        paste_y = (size - height) // 2
        square_img.paste(composite, (paste_x, paste_y))
        
        # Resize to Slack's recommended size (512x512 is a good size that works well)
        slack_size = 512
        square_img = square_img.resize((slack_size, slack_size), Image.LANCZOS)
        
        # Use the square image as our final composite
        composite = square_img
        
        print(f"Optimized image for Slack profile photo ({slack_size}x{slack_size})")
    
    # Save the result
    composite.save(output_path)
    
    return output_path

def upload_to_slack(image_path):
    """Upload the image to Slack as a profile photo."""
    # Check for Slack token in env or config file
    slack_token = get_slack_token()
    
    # If not found, prompt the user
    if not slack_token:
        slack_token = prompt_for_slack_token()
        
    if not slack_token:
        print("No Slack token available. Upload canceled.")
        return False
    
    client = WebClient(token=slack_token)
    
    try:
        # Upload the image
        with open(image_path, "rb") as image_file:
            response = client.users_setPhoto(
                image=image_file.read()
            )
        
        if response["ok"]:
            print("\nSuccessfully uploaded image to Slack as your profile photo!")
            return True
        else:
            print(f"\nFailed to upload image to Slack: {response.get('error', 'Unknown error')}")
            return False
            
    except SlackApiError as e:
        error_message = e.response["error"]
        print(f"\nFailed to upload image to Slack: {error_message}")
        
        if error_message == "invalid_auth" or error_message == "not_authed":
            print("Your Slack token appears to be invalid or expired.")
            print("Please try again with a new token.")
            # Remove the invalid token from the config file
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
                print("Removed invalid token from config file.")
        elif error_message == "token_revoked":
            print("Your Slack token has been revoked. Please generate a new one.")
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
        elif error_message == "missing_scope":
            print("Your token doesn't have the required scope. Make sure it has 'users.profile:write' scope.")
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
        
        return False
    except Exception as e:
        print(f"\nAn error occurred while uploading to Slack: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Layer random foreground image on random background image')
    parser.add_argument('--foreground', '-f', default='foreground', help='Folder containing foreground PNG images')
    parser.add_argument('--background', '-b', default='background', help='Folder containing background PNG images')
    parser.add_argument('--output', '-o', default='output', help='Output folder for layered images')
    parser.add_argument('--name', '-n', default=None, help='Output filename (default: random name)')
    parser.add_argument('--slack', '-s', action='store_true', help='Optimize output for Slack profile photo')
    parser.add_argument('--upload', '-u', action='store_true', help='Upload the result directly to Slack as a profile photo')
    parser.add_argument('--setup-slack', action='store_true', help='Set up Slack token for uploading profile photos')
    
    args = parser.parse_args()
    
    # Handle Slack token setup
    if args.setup_slack:
        token = prompt_for_slack_token()
        if token:
            print("Slack token setup completed successfully.")
        sys.exit(0)
    
    # Convert relative paths to absolute paths based on script location
    foreground_dir = os.path.join(SCRIPT_DIR, args.foreground) if not os.path.isabs(args.foreground) else args.foreground
    background_dir = os.path.join(SCRIPT_DIR, args.background) if not os.path.isabs(args.background) else args.background
    output_dir = os.path.join(SCRIPT_DIR, args.output) if not os.path.isabs(args.output) else args.output
    
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        print(f"Looking for foreground images in: {foreground_dir}")
        print(f"Looking for background images in: {background_dir}")
        
        # Get random images
        foreground_image = get_random_image(args.foreground)
        background_image = get_random_image(args.background)
        
        # Generate output filename if not provided
        if args.name:
            output_filename = f"{args.name}.png"
        else:
            fg_name = Path(foreground_image).stem
            bg_name = Path(background_image).stem
            output_filename = f"{bg_name}_{fg_name}.png"
            if args.slack or args.upload:
                output_filename = f"slack_profile_{output_filename}"
        
        output_path = os.path.join(output_dir, output_filename)
        
        # If uploading to Slack, make sure we're optimizing for Slack
        slack_profile = args.slack or args.upload
        
        # Layer the images
        result_path = layer_images(foreground_image, background_image, output_path, slack_profile=slack_profile)
        
        print(f"Created layered image: {result_path}")
        print(f"Using foreground: {foreground_image}")
        print(f"Using background: {background_image}")
        
        if args.slack:
            print("\nThis image is optimized for Slack. You can upload it as your profile photo!")
        
        # Upload to Slack if requested
        if args.upload:
            print("\nAttempting to upload the image to Slack as your profile photo...")
            upload_to_slack(result_path)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nPlease ensure you have PNG images in both the foreground and background folders.")
        print("You can add sample images by running:")
        print(f"  - Copy PNG files to the '{foreground_dir}' folder")
        print(f"  - Copy PNG files to the '{background_dir}' folder")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 