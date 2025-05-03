#!/bin/bash

# Add Flutter to PATH without changing .zshrc
export PATH="$PATH:$HOME/development/flutter/bin"

# Navigate to Flutter app directory
cd "/Users/owner/Downloads/coding projects/AMIE-app/amie_flutter_app"

# Step 1: Clean up pods and lock files
echo "=== Cleaning up pods ==="
rm -rf ios/Pods ios/Podfile.lock ios/.symlinks

# Step 2: Update the Podfile with proper iOS version and dependency fixes
echo "=== Creating compatible Podfile ==="
cat > "ios/Podfile" << 'EOL'
platform :ios, '12.0'

# This fixes the xcfilelist issue
install! 'cocoapods', :disable_input_output_paths => true

project 'Runner', {
  'Debug' => :debug,
  'Profile' => :release,
  'Release' => :release,
}

def flutter_root
  generated_xcode_build_settings_path = File.expand_path(File.join('..', 'Flutter', 'Generated.xcconfig'), __FILE__)
  unless File.exist?(generated_xcode_build_settings_path)
    raise "#{generated_xcode_build_settings_path} must exist. If you're running pod install manually, make sure flutter pub get is executed first"
  end

  File.foreach(generated_xcode_build_settings_path) do |line|
    matches = line.match(/FLUTTER_ROOT\=(.*)/)
    return matches[1].strip if matches
  end
  raise "FLUTTER_ROOT not found in #{generated_xcode_build_settings_path}"
end

require File.expand_path(File.join('packages', 'flutter_tools', 'bin', 'podhelper'), flutter_root)

flutter_ios_podfile_setup

target 'Runner' do
  use_frameworks!
  use_modular_headers!
  
  # Force specific versions for Firebase dependencies to avoid conflicts
  pod 'Firebase/Core', '~> 10.3.0'
  pod 'Firebase/Auth', '~> 10.3.0'
  pod 'GoogleUtilities', '~> 7.11.0'

  flutter_install_all_ios_pods File.dirname(File.realpath(__FILE__))
end

post_install do |installer|
  installer.pods_project.targets.each do |target|
    flutter_additional_ios_build_settings(target)
    
    target.build_configurations.each do |config|
      config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '12.0'
      
      # Fix common Xcode warnings
      config.build_settings['EXPANDED_CODE_SIGN_IDENTITY'] = ""
      config.build_settings['CODE_SIGNING_REQUIRED'] = "NO"
      config.build_settings['CODE_SIGNING_ALLOWED'] = "NO"
    end
  end
end
EOL

# Step 3: Run flutter pub get
echo "=== Running flutter pub get ==="
flutter clean
flutter pub get

# Step 4: Install pods with specific command based on system architecture
echo "=== Installing pods ==="
cd ios
if [[ $(uname -m) == 'arm64' ]]; then
  # For M1/M2 Macs
  echo "Using special command for M1/M2 Mac..."
  arch -x86_64 pod install --repo-update
else
  # For Intel Macs
  pod install --repo-update
fi
cd ..

# Step 5: Launch simulator and app
echo "=== Launching simulator ==="
open -a Simulator
sleep 5  # Wait for simulator to boot

# Specific iPhone 16 Pro simulator ID
IPHONE_16_PRO="F0ECEC9F-CB58-4460-B3AE-6C3AFD27FE49"

echo "=== Launching app ==="
flutter run -d $IPHONE_16_PRO

# If the specific simulator fails
if [ $? -ne 0 ]; then
  echo ""
  echo "===================================================================="
  echo "Error running the app on iPhone 16 Pro simulator."
  echo ""
  echo "Make sure the simulator is available by running:"
  echo "   open -a Simulator"
  echo ""
  echo "Available devices:"
  flutter devices
  echo "===================================================================="
fi
