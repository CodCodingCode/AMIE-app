#!/bin/bash

# Step 1: Add Flutter to PATH permanently (this modifies your .zshrc file)
echo "Adding Flutter to your PATH permanently..."
if ! grep -q "export PATH=\"\$PATH:\$HOME/development/flutter/bin\"" ~/.zshrc; then
  echo 'export PATH="$PATH:$HOME/development/flutter/bin"' >> ~/.zshrc
  echo "Flutter PATH added to ~/.zshrc"
else
  echo "Flutter PATH already exists in ~/.zshrc"
fi

# Make sure Flutter is available for this session
export PATH="$PATH:$HOME/development/flutter/bin"

# Step 2: Install CocoaPods (required for iOS development)
echo "Installing CocoaPods..."
if command -v brew &>/dev/null; then
  echo "Installing CocoaPods via Homebrew (recommended)..."
  brew install cocoapods
  if [ $? -ne 0 ]; then
    echo "Homebrew installation failed, trying with gem..."
    sudo gem install cocoapods
  fi
else
  echo "Homebrew not found, installing CocoaPods via gem..."
  sudo gem install cocoapods
fi

# Step 3: Verify CocoaPods installation
if command -v pod &>/dev/null; then
  echo "CocoaPods installed successfully!"
  pod --version
else
  echo "Error: CocoaPods installation failed. Please try manual installation."
  echo "Visit https://guides.cocoapods.org/using/getting-started.html for more information."
  exit 1
fi

# Step 4: Update Flutter
echo "Updating Flutter to the latest version..."
if command -v flutter &>/dev/null; then
  flutter upgrade
else
  echo "Error: Flutter command not found. Make sure Flutter SDK is properly installed."
  echo "Try running: source ~/.zshrc"
  exit 1
fi

# Step 5: Run flutter doctor to verify setup
echo "Running flutter doctor to verify installation..."
flutter doctor

echo ""
echo "====================================================================="
echo "Setup complete!"
echo ""
echo "To use Flutter in this terminal session, run:"
echo "  source ~/.zshrc"
echo ""
echo "To run your Flutter app:"
echo "  cd \"/Users/owner/Downloads/coding projects/AMIE-app/amie_flutter_app\""
echo "  flutter run"
echo "====================================================================="
