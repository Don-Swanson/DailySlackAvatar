# Daily Slack Avatar

Automatically create and update unique Slack profile photos by layering random images. Perfect for adding variety to your Slack presence or scheduling daily profile picture changes.

![Example Slack Avatar](example_images/example_avatar.png)

## Features

- **Image Layering**: Takes a random foreground PNG and layers it on top of a random background
- **Slack Integration**: Automatically uploads images to your Slack profile
- **Scheduling**: Can be used with cron or scheduled tasks for daily updates
- **Secure Authentication**: Safely stores your Slack token with proper permissions

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/Don-Swanson/DailySlackAvatar.git
   cd daily-slack-avatar
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Place your images in the appropriate folders:
   - Add background PNG images to the `background` folder
   - Add foreground PNG images to the `foreground` folder

> **Note:** The script will automatically create the folders if they don't exist, but you'll need to add PNG images to them before the script can run successfully.

## Usage

### Basic Usage

Run the script with default settings to create a layered image:
```bash
python daily_slack_avatar.py
```

This will:
- Select a random PNG from the `foreground` folder
- Select a random PNG from the `background` folder
- Layer the foreground on top of the background
- Save the result to the `output` folder with an auto-generated name

### Creating a Slack Profile Photo

To create an optimized image for a Slack profile photo:
```bash
python daily_slack_avatar.py --slack
```

This will ensure the image is properly sized and formatted for Slack.

### Automatically Upload to Slack

Upload a generated image directly to your Slack profile:
```bash
python daily_slack_avatar.py --upload
```

### Daily Updates with Cron

To update your Slack avatar daily, add the included script to your crontab:

```bash
# Edit your crontab
crontab -e

# Add this line to run daily at 9 AM
0 9 * * * /path/to/daily-slack-avatar/update_avatar.sh
```

## Setting up Slack Authentication

To set up Slack authentication once and store it permanently:
```bash
python daily_slack_avatar.py --setup-slack
```

This will guide you through:
1. Creating a Slack app
2. Adding the required permissions
3. Getting your token
4. Securely storing it for future use

Alternatively, the script will prompt you for a token the first time you use the `--upload` option and ask if you want to save it.

You can also set it manually as an environment variable:
```bash
export SLACK_USER_TOKEN=xoxp-your-token
```

> **Note:** Your token is stored securely in a `.slack_config.json` file with permissions that only allow you to access it.

## Command Line Options

```
python daily_slack_avatar.py [options]

options:
  -h, --help            Show help message
  --foreground FOLDER, -f FOLDER
                        Folder containing foreground PNG images (default: foreground)
  --background FOLDER, -b FOLDER
                        Folder containing background PNG images (default: background)
  --output FOLDER, -o FOLDER
                        Output folder for layered images (default: output)
  --name NAME, -n NAME  Custom output filename without extension (default: auto-generated)
  --slack, -s           Optimize output for Slack profile photo
  --upload, -u          Upload the result directly to Slack as a profile photo
  --setup-slack         Set up Slack token for uploading profile photos
```

## Examples

Custom folders:
```bash
python daily_slack_avatar.py --foreground my_characters --background my_scenes --output finished_images
```

Specific output filename:
```bash
python daily_slack_avatar.py --name my_layered_image
```

Create and upload in one step:
```bash
python daily_slack_avatar.py --upload
```

## Troubleshooting

### No PNG Files Found
If you get an error like "No PNG files found in 'foreground'", make sure you've added PNG images to both the foreground and background folders.

### Slack Upload Issues
If you're having trouble with Slack uploads, check that:
- Your token has the `users.profile:write` scope
- Your token is still valid and hasn't been revoked

To reset your token:
```bash
python daily_slack_avatar.py --setup-slack
```

### Running from Automation Tools (Cron, Keyboard Maestro, etc.)
When running `update_avatar.sh` or `daily_slack_avatar.py` from an automated environment like cron, launchd, or Keyboard Maestro, you might encounter issues related to environment variables (like `PATH`) and the script's working directory.

- **"python: command not found" or "python3: command not found"**: The automation tool's environment might not know where your Python executable is. 
    - **Solution**: Find the full path to your Python 3 executable by running `which python3` in your terminal. Then, use that full path in the `update_avatar.sh` script (e.g., replace `python` or `python3` with `/opt/homebrew/bin/python3`).
- **"No such file or directory: daily_slack_avatar.py"**: The script is being run from a different directory than where `daily_slack_avatar.py` is located.
    - **Solution**: Modify `update_avatar.sh` to explicitly change to the script's directory before executing the Python script. Add these lines near the top of `update_avatar.sh`:
      ```sh
      SCRIPT_DIR=$(dirname "$0")
      cd "$SCRIPT_DIR" || exit 1
      ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is released into the public domain using the Unlicense - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Created with assistance from Claude AI
- Inspired by the need to keep Slack profiles interesting 