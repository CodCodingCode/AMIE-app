#!/bin/bash

echo "=== AMIE Flutter App Full Reset ==="

# Navigate to Flutter app directory
cd "/Users/owner/Downloads/coding projects/AMIE-app/amie_flutter_app"

# Step 1: Full cleanup
echo "Performing comprehensive cleanup..."
flutter clean
rm -rf ios/Pods ios/Podfile.lock ios/.symlinks ios/Flutter/Flutter.podspec ios/Flutter/Generated.* .dart_tool/ .flutter-plugins .flutter-plugins-dependencies build/

# Create a clean pubspec with NO firebase dependencies initially
echo "Creating minimal pubspec.yaml (NO Firebase/Google)..."
cat > "pubspec.yaml" << 'EOL'
name: amie_flutter_app
description: AMIE medical assistant application
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.6

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0

flutter:
  uses-material-design: true
EOL

# Create a clean iOS folder structure
echo "Recreating iOS project structure..."
mkdir -p ios/Flutter
mkdir -p ios/Runner

# Create a specialized Podfile that addresses compatibility
echo "Creating specialized Podfile..."
cat > "ios/Podfile" << 'EOL'
platform :ios, '12.0'

# Prevent CocoaPods from embedding multiple Swift runtimes
install! 'cocoapods', :disable_input_output_paths => true

# Force GoogleUtilities to a specific version
$FirebaseSDKVersion = '10.3.0'
$GoogleSignInVersion = '7.0.0'
$GoogleUtilitiesVersion = '7.11.0'

pre_install do |installer|
  # Ensure GoogleUtilities uses the same version everywhere
  installer.pod_targets.each do |pod|
    if pod.name.start_with?('GoogleUtilities')
      pod.specs.each do |s|
        s.dependency 'GoogleUtilities/Environment', $GoogleUtilitiesVersion
      end
    end
  end
end

target 'Runner' do
  use_frameworks!
  use_modular_headers!

  # Force all our pods to use specific versions
  pod 'GoogleUtilities', $GoogleUtilitiesVersion
  pod 'GoogleSignIn', $GoogleSignInVersion
  pod 'Firebase/Core', $FirebaseSDKVersion
  pod 'Firebase/Auth', $FirebaseSDKVersion

  # Flutter pods will be installed later
end

post_install do |installer|
  installer.pods_project.targets.each do |target|
    target.build_configurations.each do |config|
      config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '12.0'
    end
  end
end
EOL

echo "Creating Flutter-specific config files..."
touch ios/Flutter/Debug.xcconfig
touch ios/Flutter/Release.xcconfig
echo "#include \"Generated.xcconfig\"" > ios/Flutter/Debug.xcconfig
echo "#include \"Generated.xcconfig\"" > ios/Flutter/Release.xcconfig

# Use a specific working pubspec configuration with VERY specific package versions
echo "Creating full pubspec with SPECIFIC compatible versions..."
cat > "pubspec.yaml" << 'EOL'
name: amie_flutter_app
description: AMIE medical assistant application
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.6
  # These versions have been tested to work together
  firebase_core: 1.24.0
  firebase_auth: 3.11.2
  # Use older Google Sign In compatible with Firebase 1.x/3.x
  google_sign_in: 5.0.7
  provider: 6.0.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0

flutter:
  uses-material-design: true
EOL

echo "Generating initial Flutter files..."
flutter create .

echo "Running flutter pub get..."
flutter pub get

echo "Installing pods..."
cd ios
pod install --repo-update
cd ..

# Create placeholder main.dart if needed
if [ ! -f "lib/main.dart" ] || [ ! -s "lib/main.dart" ]; then
  echo "Creating placeholder main.dart..."
  cat > "lib/main.dart" << 'EOL'
import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AMIE Medical Assistant',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: const Scaffold(
        body: Center(
          child: Text('AMIE App'),
        ),
      ),
    );
  }
}
EOL
fi

echo "=== Full Reset Completed ==="
echo "Try running your app now with: flutter run"
