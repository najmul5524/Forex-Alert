import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'services/notification_service.dart';
import 'services/theme_manager.dart';
import 'screens/home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  await ThemeManager.init();

  // Safe Firebase Initialization
  try {
    await Firebase.initializeApp();
  } catch (e) {
    debugPrint('Firebase init notice: $e');
  }

  // Initialize Local Notifications and FCM
  try {
    await NotificationService.init();
  } catch (e) {
    debugPrint('Notification init notice: $e');
  }

  runApp(const ForexAlertApp());
}

class ForexAlertApp extends StatelessWidget {
  const ForexAlertApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ThemeMode>(
      valueListenable: ThemeManager.themeModeNotifier,
      builder: (context, currentMode, _) {
        return MaterialApp(
          title: 'Forex Alert Live',
          debugShowCheckedModeBanner: false,
          theme: ThemeManager.lightTheme,
          darkTheme: ThemeManager.darkTheme,
          themeMode: currentMode,
          home: const HomeScreen(),
        );
      },
    );
  }
}
