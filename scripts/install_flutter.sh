#!/bin/bash

# Create a development directory for Flutter
mkdir -p ~/development

# Check if Flutter is already downloaded
if [ ! -d ~/development/flutter ]; then
    echo "Downloading Flutter SDK..."
    cd ~/Downloads
    # For Apple Silicon (M1/M2) Macs
    curl -O https://storage.googleapis.com/flutter_infra_release/releases/stable/macos/flutter_macos_arm64_3.22.0-stable.zip
    # For Intel Macs, uncomment the below line instead
    # curl -O https://storage.googleapis.com/flutter_infra_release/releases/stable/macos/flutter_macos_3.22.0-stable.zip
    
    echo "Extracting Flutter SDK..."
    unzip -q flutter_macos_arm64_3.22.0-stable.zip -d ~/development
    # For Intel Macs, uncomment the below line instead
    # unzip -q flutter_macos_3.22.0-stable.zip -d ~/development
fi

# Add Flutter to PATH temporarily for this session
export PATH="$PATH:$HOME/development/flutter/bin"

# Run Flutter doctor to check installation
echo "Running flutter doctor..."
flutter doctor

# Create a new Flutter project in AMIE-app directory
echo "Creating a new Flutter project..."
cd "/Users/owner/Downloads/coding projects/AMIE-app"
flutter create amie_flutter_app

echo ""
echo "==================================================================="
echo "Flutter installation complete! To use Flutter in new terminal sessions:"
echo "export PATH=\"\$PATH:\$HOME/development/flutter/bin\""
echo ""
echo "To run your Flutter app:"
echo "cd \"/Users/owner/Downloads/coding projects/AMIE-app/amie_flutter_app\""
echo "flutter run"
echo "==================================================================="
