import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'home_screen.dart';
import 'login_screen.dart';

class Wrapper extends StatelessWidget {
  const Wrapper({super.key});

  @override
  Widget build(BuildContext context) {
    final user = Provider.of<User?>(context);
    
    // Return either Home or Login screen based on auth state
    if (user != null) {
      return const HomeScreen();
    } else {
      return const LoginScreen();
    }
  }
}
