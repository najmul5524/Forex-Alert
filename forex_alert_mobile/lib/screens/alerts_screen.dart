import 'package:flutter/material.dart';
import '../models/alert_model.dart';
import '../services/api_service.dart';
import '../services/firestore_service.dart';
import '../widgets/alert_card.dart';
import 'create_alert_screen.dart';

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen> {
  List<AlertModel> _alerts = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchAlerts();
  }

  Future<void> _fetchAlerts() async {
    final list = await ApiService.getAlerts();
    if (mounted) {
      setState(() {
        _alerts = list;
        _isLoading = false;
      });
    }
  }

  Future<void> _toggleAlert(AlertModel alert) async {
    if (alert.id != null) {
      await ApiService.toggleAlert(alert.id!);
      await FirestoreService.toggleAlert(alert.id.toString(), alert.isActive);
      _fetchAlerts();
    }
  }

  Future<void> _deleteAlert(AlertModel alert) async {
    if (alert.id != null) {
      final confirm = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          backgroundColor: Theme.of(context).colorScheme.surface,
          title: Text('Delete Alert?', style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
          content: Text('Are you sure you want to delete the alert for ${alert.symbol}?', style: TextStyle(color: Colors.blueGrey.shade400)),
          actions: [
            TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('Cancel')),
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(true),
              child: const Text('Delete', style: TextStyle(color: Color(0xFFF43F5E))),
            ),
          ],
        ),
      );

      if (confirm == true) {
        await ApiService.deleteAlert(alert.id!);
        await FirestoreService.deleteAlert(alert.id.toString());
        _fetchAlerts();
      }
    }
  }

  Future<void> _testTrigger(AlertModel alert) async {
    if (alert.id != null) {
      final res = await ApiService.testTriggerAlert(alert.id!);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(res ? 'Test alert dispatched for ${alert.symbol}!' : 'Test dispatch failed'),
            backgroundColor: res ? const Color(0xFF10B981) : const Color(0xFFF43F5E),
          ),
        );
      }
    }
  }

  void _openCreateModal() async {
    final res = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => const CreateAlertScreen(),
    );
    if (res == true) {
      _fetchAlerts();
    }
  }

  @override
  Widget build(BuildContext context) {
    final activeCount = _alerts.where((a) => a.isActive).length;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Row(
          children: [
            Text(
              'Alert Rules',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 17,
                color: Theme.of(context).colorScheme.onSurface,
              ),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '$activeCount Active',
                style: TextStyle(color: Theme.of(context).colorScheme.primary, fontSize: 11, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: Theme.of(context).colorScheme.primary),
            onPressed: _fetchAlerts,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _openCreateModal,
        backgroundColor: Theme.of(context).colorScheme.primary,
        icon: const Icon(Icons.add, color: Colors.white),
        label: const Text('New Alert', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
      ),
      body: RefreshIndicator(
        onRefresh: _fetchAlerts,
        color: Theme.of(context).colorScheme.primary,
        backgroundColor: Theme.of(context).colorScheme.surface,
        child: _isLoading && _alerts.isEmpty
            ? const Center(child: CircularProgressIndicator())
            : _alerts.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Text('🔔', style: TextStyle(fontSize: 48)),
                          const SizedBox(height: 16),
                          Text(
                            'No alerts configured yet',
                            style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            'Tap "New Alert" to configure price or indicator triggers.',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: Colors.blueGrey.shade400, fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 90),
                    itemCount: _alerts.length,
                    itemBuilder: (ctx, i) {
                      final a = _alerts[i];
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: AlertCard(
                          alert: a,
                          onToggle: (_) => _toggleAlert(a),
                          onDelete: () => _deleteAlert(a),
                          onTestTrigger: () => _testTrigger(a),
                        ),
                      );
                    },
                  ),
      ),
    );
  }
}
