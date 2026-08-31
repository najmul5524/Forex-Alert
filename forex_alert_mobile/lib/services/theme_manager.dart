import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ThemeManager {
  static const String _keyThemeMode = 'app_theme_mode';
  static final ValueNotifier<ThemeMode> themeModeNotifier = ValueNotifier<ThemeMode>(ThemeMode.system);

  static Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    final savedMode = prefs.getString(_keyThemeMode);
    if (savedMode == 'light') {
      themeModeNotifier.value = ThemeMode.light;
    } else if (savedMode == 'dark') {
      themeModeNotifier.value = ThemeMode.dark;
    } else {
      themeModeNotifier.value = ThemeMode.system;
    }
  }

  static Future<void> setThemeMode(ThemeMode mode) async {
    themeModeNotifier.value = mode;
    final prefs = await SharedPreferences.getInstance();
    if (mode == ThemeMode.light) {
      await prefs.setString(_keyThemeMode, 'light');
    } else if (mode == ThemeMode.dark) {
      await prefs.setString(_keyThemeMode, 'dark');
    } else {
      await prefs.setString(_keyThemeMode, 'system');
    }
  }

  static void toggleTheme(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    setThemeMode(isDark ? ThemeMode.light : ThemeMode.dark);
  }

  // Light Theme Definition
  static final ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    scaffoldBackgroundColor: const Color(0xFFF1F5F9), // Slate 100
    colorScheme: const ColorScheme.light(
      primary: Color(0xFF0284C7), // Sky 600
      secondary: Color(0xFF0369A1), // Sky 700
      surface: Color(0xFFFFFFFF),
      onSurface: Color(0xFF0F172A),
      surfaceContainerHighest: Color(0xFFE2E8F0),
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: Color(0xFFFFFFFF),
      elevation: 0,
      scrolledUnderElevation: 1,
      titleTextStyle: TextStyle(
        color: Color(0xFF0F172A),
        fontWeight: FontWeight.bold,
        fontSize: 17,
      ),
      iconTheme: IconThemeData(color: Color(0xFF0F172A)),
    ),
    cardTheme: CardThemeData(
      color: const Color(0xFFFFFFFF),
      elevation: 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: Color(0xFFE2E8F0)),
      ),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: Color(0xFFFFFFFF),
      selectedItemColor: Color(0xFF0284C7),
      unselectedItemColor: Color(0xFF64748B),
    ),
    dividerColor: const Color(0xFFE2E8F0),
  );

  // Dark Theme Definition
  static final ThemeData darkTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    scaffoldBackgroundColor: const Color(0xFF080D1A), // Dark Slate
    colorScheme: const ColorScheme.dark(
      primary: Color(0xFF0EA5E9), // Sky 500
      secondary: Color(0xFF38BDF8), // Sky 400
      surface: Color(0xFF131D31),
      onSurface: Color(0xFFF8FAFC),
      surfaceContainerHighest: Color(0xFF1E293B),
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: Color(0xFF0F172A),
      elevation: 0,
      scrolledUnderElevation: 0,
      titleTextStyle: TextStyle(
        color: Color(0xFFFFFFFF),
        fontWeight: FontWeight.bold,
        fontSize: 17,
      ),
      iconTheme: IconThemeData(color: Color(0xFFFFFFFF)),
    ),
    cardTheme: CardThemeData(
      color: const Color(0xFF131D31),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: Color(0xFF1E293B)),
      ),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: Color(0xFF0F172A),
      selectedItemColor: Color(0xFF38BDF8),
      unselectedItemColor: Color(0xFF94A3B8),
    ),
    dividerColor: const Color(0xFF1E293B),
  );
}
