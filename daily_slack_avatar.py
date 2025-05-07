#!/usr/bin/env python3

# DailySlackAvatar - A tool to create and upload random Slack profile photos
# 
# This script takes a random PNG from a foreground folder and layers it on top 
# of a random PNG from a background folder to create unique daily Slack avatars.
# 
# Author: Don-Swanson

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

def save_slack_tokens(tokens, alias=None):
    """Save Slack tokens to the config file."""
    try:
        config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                try:
                    config = json.load(f)
                except json.JSONDecodeError:
                    config = {}
        
        # Initialize profiles if it doesn't exist
        if 'profiles' not in config:
            config['profiles'] = {}
            
        # Adding a single token with alias
        if isinstance(tokens, str) and alias:
            config['profiles'][alias] = {'token': tokens}
            # Set as default if it's the only profile
            if len(config['profiles']) == 1:
                config['default'] = alias
                
        # Adding multiple tokens
        elif isinstance(tokens, dict):
            for alias, token in tokens.items():
                config['profiles'][alias] = {'token': token}
            # Set default if none exists and we have at least one profile
            if 'default' not in config and len(config['profiles']) > 0:
                config['default'] = next(iter(config['profiles'].keys()))
                
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        os.chmod(CONFIG_FILE, 0o600)  # Set permissions to only allow the owner to read/write
        return True
    except Exception as e:
        print(f"Error saving tokens: {e}")
        return False

def get_slack_tokens(profile_aliases=None):
    """Get Slack tokens from environment variables or config file.
    
    Args:
        profile_aliases: List of profile aliases to get tokens for. If None, get all profiles.
        
    Returns:
        Dictionary of {alias: token} pairs
    """
    tokens = {}
    
    # First check environment variable for default token
    env_token = os.environ.get("SLACK_USER_TOKEN")
    if env_token:
        tokens["default"] = env_token
    
    # Then check config file
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                profiles = config.get('profiles', {})
                
                # If specific profiles are requested
                if profile_aliases:
                    for alias in profile_aliases:
                        if alias in profiles:
                            tokens[alias] = profiles[alias]['token']
                # Otherwise, get all profiles
                else:
                    for alias, profile in profiles.items():
                        tokens[alias] = profile['token']
    except Exception as e:
        print(f"Error reading tokens from config file: {e}")
    
    return tokens

def prompt_for_slack_token(add_multiple=False):
    """Prompt the user to enter their Slack token(s)."""
    print("\nTo upload to Slack, you need to provide Slack User OAuth Token(s) with 'users.profile:write' scope.")
    print("Follow these steps to get your token:")
    print("1. Go to https://api.slack.com/apps")
    print("2. Create a new app (or use an existing one)")
    print("3. Go to 'OAuth & Permissions' and add 'users.profile:write' to 'User Token Scopes'")
    print("4. Install the app to your workspace")
    print("5. Copy the 'User OAuth Token' (starts with xoxp-)")
    
    tokens = {}
    
    if add_multiple:
        print("\nYou can add multiple tokens for different Slack workspaces/accounts.")
        print("For each token, you'll be asked to provide an alias to identify it.")
        print("Enter an empty alias when you're done adding tokens.")
        
        while True:
            alias = input("\nEnter an alias for this Slack profile (or empty to finish): ").strip()
            if not alias:
                break
                
            token = getpass.getpass(f"Enter Slack User OAuth Token for '{alias}': ")
            if not token:
                print("No token provided. Skipping this profile.")
                continue
                
            tokens[alias] = token
            print(f"Added token for '{alias}'")
            
        if not tokens:
            print("No tokens provided. Aborting setup.")
            return None
    else:
        alias = input("\nEnter an alias for this Slack profile (default: 'default'): ").strip() or "default"
        token = getpass.getpass(f"Enter Slack User OAuth Token for '{alias}': ")
        
        if not token:
            print("No token provided. Aborting setup.")
            return None
            
        tokens[alias] = token
    
    save_tokens = input("Would you like to save these token(s) for future use? (y/n): ").lower().strip() == 'y'
    
    if save_tokens:
        if save_slack_tokens(tokens):
            print("Token(s) saved successfully!")
        else:
            print("Failed to save token(s). You'll need to enter them again next time.")
    
    return tokens

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

def upload_to_slack(image_path, profile_aliases=None):
    """Upload the image to one or more Slack profiles.
    
    Args:
        image_path: Path to the image file
        profile_aliases: List of profile aliases to upload to. If None, upload to all profiles.
        
    Returns:
        List of successful uploads as (alias, success) tuples
    """
    # Check for Slack tokens in env or config file
    slack_tokens = get_slack_tokens(profile_aliases)
    
    # If no tokens found or specific profiles not found, prompt the user
    if not slack_tokens:
        if profile_aliases:
            print(f"No tokens found for the specified profiles: {', '.join(profile_aliases)}")
        slack_tokens = prompt_for_slack_token(add_multiple=True)
        
    if not slack_tokens:
        print("No Slack tokens available. Upload canceled.")
        return []
    
    results = []
    
    # Upload to each profile
    for alias, token in slack_tokens.items():
        print(f"\nUploading to Slack profile: {alias}")
        client = WebClient(token=token)
        
        try:
            # Upload the image
            with open(image_path, "rb") as image_file:
                response = client.users_setPhoto(
                    image=image_file.read()
                )
            
            if response["ok"]:
                print(f"Successfully uploaded image to Slack profile: {alias}")
                results.append((alias, True))
            else:
                print(f"Failed to upload image to Slack profile '{alias}': {response.get('error', 'Unknown error')}")
                results.append((alias, False))
                
        except SlackApiError as e:
            error_message = e.response["error"]
            print(f"Failed to upload image to Slack profile '{alias}': {error_message}")
            
            if error_message in ["invalid_auth", "not_authed", "token_revoked", "missing_scope"]:
                print(f"Token issue for profile '{alias}': {error_message}")
                if error_message == "invalid_auth" or error_message == "not_authed":
                    print("Your Slack token appears to be invalid or expired.")
                elif error_message == "token_revoked":
                    print("Your Slack token has been revoked.")
                elif error_message == "missing_scope":
                    print("Your token doesn't have the required scope. Make sure it has 'users.profile:write' scope.")
                
                # Remove the invalid token from the config
                try:
                    if os.path.exists(CONFIG_FILE):
                        with open(CONFIG_FILE, 'r') as f:
                            config = json.load(f)
                        if 'profiles' in config and alias in config['profiles']:
                            del config['profiles'][alias]
                            with open(CONFIG_FILE, 'w') as f:
                                json.dump(config, f, indent=2)
                            print(f"Removed invalid token for profile '{alias}' from config file.")
                except Exception as ex:
                    print(f"Error updating config file: {ex}")
            
            results.append((alias, False))
        except Exception as e:
            print(f"An error occurred while uploading to Slack profile '{alias}': {e}")
            results.append((alias, False))
    
    # Summarize results
    successful = [alias for alias, success in results if success]
    failed = [alias for alias, success in results if not success]
    
    if successful:
        print(f"\nSuccessfully uploaded to {len(successful)} profile(s): {', '.join(successful)}")
    if failed:
        print(f"\nFailed to upload to {len(failed)} profile(s): {', '.join(failed)}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Layer random foreground image on random background image')
    parser.add_argument('--foreground', '-f', default='foreground', help='Folder containing foreground PNG images')
    parser.add_argument('--background', '-b', default='background', help='Folder containing background PNG images')
    parser.add_argument('--output', '-o', default='output', help='Output folder for layered images')
    parser.add_argument('--name', '-n', default=None, help='Output filename (default: random name)')
    parser.add_argument('--slack', '-s', action='store_true', help='Optimize output for Slack profile photo')
    parser.add_argument('--upload', '-u', action='store_true', help='Upload the result directly to Slack as a profile photo')
    parser.add_argument('--profiles', '-p', nargs='+', help='Specific Slack profile aliases to upload to (requires --upload)')
    parser.add_argument('--setup-slack', action='store_true', help='Set up Slack tokens for uploading profile photos')
    parser.add_argument('--add-profiles', action='store_true', help='Add multiple Slack profiles')
    parser.add_argument('--list-profiles', action='store_true', help='List all configured Slack profiles')
    
    args = parser.parse_args()
    
    # Handle Slack token/profile management
    if args.setup_slack:
        tokens = prompt_for_slack_token()
        if tokens:
            print("Slack token setup completed successfully.")
        sys.exit(0)
    
    if args.add_profiles:
        tokens = prompt_for_slack_token(add_multiple=True)
        if tokens:
            print("Slack profiles added successfully.")
        sys.exit(0)
    
    if args.list_profiles:
        tokens = get_slack_tokens()
        if tokens:
            print("\nConfigured Slack profiles:")
            for alias in tokens.keys():
                print(f"- {alias}")
            
            # Show default profile if available
            try:
                if os.path.exists(CONFIG_FILE):
                    with open(CONFIG_FILE, 'r') as f:
                        config = json.load(f)
                        if 'default' in config:
                            print(f"\nDefault profile: {config['default']}")
            except Exception as e:
                print(f"Error reading config file: {e}")
        else:
            print("No Slack profiles configured.")
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
            print("\nAttempting to upload the image to Slack profile(s)...")
            upload_to_slack(result_path, args.profiles)
        
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