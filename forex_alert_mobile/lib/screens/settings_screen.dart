import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/notification_service.dart';
import '../services/theme_manager.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final TextEditingController _urlController = TextEditingController();
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final url = await ApiService.getBaseUrl();
    setState(() {
      _urlController.text = url;
      _isLoading = false;
    });
  }

  Future<void> _saveUrl() async {
    final url = _urlController.text.trim();
    if (url.isNotEmpty) {
      await ApiService.setBaseUrl(url);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Server connection address saved!'),
            backgroundColor: Color(0xFF10B981),
          ),
        );
      }
    }
  }

  Future<void> _testLocalPush() async {
    await NotificationService.showLocalNotification(
      id: 999,
      title: '🚨 EURUSD Alert (1m)',
      body: 'EURUSD crossed ABOVE 1.08550! (Test Mobile Alert)',
    );
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Test notification dispatched with sound & vibration!'),
          backgroundColor: Theme.of(context).colorScheme.primary,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final surfaceColor = Theme.of(context).colorScheme.surface;
    final dividerColor = Theme.of(context).dividerColor;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text(
          'Settings & Appearance',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 17,
            color: Theme.of(context).colorScheme.onSurface,
          ),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // Theme Mode Selector Card
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: surfaceColor,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: dividerColor),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.palette_outlined, color: Theme.of(context).colorScheme.primary, size: 20),
                          const SizedBox(width: 8),
                          Text(
                            'Appearance & Theme Mode',
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.onSurface,
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Choose your preferred visual theme for day or night trading:',
                        style: TextStyle(color: isDark ? Colors.blueGrey.shade400 : Colors.blueGrey.shade600, fontSize: 12),
                      ),
                      const SizedBox(height: 14),
                      ValueListenableBuilder<ThemeMode>(
                        valueListenable: ThemeManager.themeModeNotifier,
                        builder: (ctx, currentMode, _) {
                          return SegmentedButton<ThemeMode>(
                            segments: const [
                              ButtonSegment(
                                value: ThemeMode.system,
                                icon: Icon(Icons.brightness_auto, size: 16),
                                label: Text('Auto'),
                              ),
                              ButtonSegment(
                                value: ThemeMode.light,
                                icon: Icon(Icons.light_mode, size: 16),
                                label: Text('Light'),
                              ),
                              ButtonSegment(
                                value: ThemeMode.dark,
                                icon: Icon(Icons.dark_mode, size: 16),
                                label: Text('Dark'),
                              ),
                            ],
                            selected: {currentMode},
                            onSelectionChanged: (newSelection) {
                              ThemeManager.setThemeMode(newSelection.first);
                            },
                            style: const ButtonStyle(
                              visualDensity: VisualDensity.compact,
                            ),
                          );
                        },
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // Server Connection Card
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: surfaceColor,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: dividerColor),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.dns, color: Theme.of(context).colorScheme.primary, size: 18),
                          const SizedBox(width: 8),
                          Text(
                            'Alert Engine Backend Host',
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.onSurface,
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Enter your live Render cloud URL or local network IP:',
                        style: TextStyle(color: isDark ? Colors.blueGrey.shade400 : Colors.blueGrey.shade600, fontSize: 12),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _urlController,
                        style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontFamily: 'monospace', fontSize: 13),
                        decoration: InputDecoration(
                          hintText: 'https://forex-alert-wta1.onrender.com',
                          hintStyle: TextStyle(color: Colors.blueGrey.shade400),
                          filled: true,
                          fillColor: isDark ? const Color(0xFF0F172A) : const Color(0xFFF1F5F9),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: dividerColor)),
                          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: dividerColor)),
                        ),
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: _saveUrl,
                          icon: const Icon(Icons.check, size: 16),
                          label: const Text('Save Server Address', style: TextStyle(fontWeight: FontWeight.bold)),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Theme.of(context).colorScheme.primary,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // Test Notification Card
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: surfaceColor,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: dividerColor),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.notifications_active, color: isDark ? Colors.amberAccent : Colors.orange.shade800, size: 18),
                          const SizedBox(width: 8),
                          Text(
                            'Test Mobile Alerts',
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.onSurface,
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Send a test notification to verify that high-priority sound, vibration, and lock-screen alerts work on your phone.',
                        style: TextStyle(color: isDark ? Colors.blueGrey.shade400 : Colors.blueGrey.shade600, fontSize: 12),
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: _testLocalPush,
                          icon: const Icon(Icons.bolt, size: 16),
                          label: const Text('Send Test Alert to Phone', style: TextStyle(fontWeight: FontWeight.bold)),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF6366F1),
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}
