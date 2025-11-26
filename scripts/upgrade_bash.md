# Update Bash Version on Mac

To update the Bash version on macOS, the recommended approach is to install a newer version via Homebrew, as Apple ships with an outdated version of Bash (3.2) due to licensing restrictions under GPLv3  This version lacks modern features such as associative arrays and improved completion 

First, install Homebrew if it is not already installed by running the following command in the terminal:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Once Homebrew is installed, update the package list and install the latest version of Bash:
```bash
brew update
brew install bash
```

After installation, verify the new version by running:
```bash
/opt/homebrew/bin/bash --version
```
This will display the updated version, such as Bash 5.2.15, which is significantly newer than the default version 

To set the new Bash version as your default shell, add it to the list of allowed shells:
```bash
sudo sh -c 'echo /opt/homebrew/bin/bash >> /etc/shells'
```

Then, change your login shell using the `chsh` command:
```bash
chsh -s /opt/homebrew/bin/bash
```

After restarting your terminal, the new Bash version will be active. You can confirm this by running:
```bash
echo $BASH_VERSION
```

For users of VS Code, the integrated terminal may still use the default shell. To update it, modify the `settings.json` file by adding a new terminal profile:
```json
"terminal.integrated.profiles.osx": {
    "new bash": {
        "path": "/opt/homebrew/bin/bash",
        "args": ["-l"]
    }
},
"terminal.integrated.defaultProfile.osx": "new bash"
```

This ensures that VS Code’s terminal uses the updated Bash version 

Note that scripts using the shebang `#!/bin/bash` will still invoke the outdated system Bash. To ensure scripts use the updated version, update the shebang to `#!/usr/bin/env bash` or explicitly use the full path to the new Bash installation 