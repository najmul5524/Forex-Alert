import 'package:flutter/material.dart';
import '../models/trigger_log_model.dart';
import '../services/api_service.dart';
import '../widgets/log_card.dart';

class LogsScreen extends StatefulWidget {
  const LogsScreen({super.key});

  @override
  State<LogsScreen> createState() => _LogsScreenState();
}

class _LogsScreenState extends State<LogsScreen> {
  List<TriggerLogModel> _logs = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchLogs();
  }

  Future<void> _fetchLogs() async {
    final list = await ApiService.getTriggerLogs();
    if (mounted) {
      setState(() {
        _logs = list;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text(
          'Trigger History',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 17,
            color: Theme.of(context).colorScheme.onSurface,
          ),
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: Theme.of(context).colorScheme.primary),
            onPressed: _fetchLogs,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _fetchLogs,
        color: Theme.of(context).colorScheme.primary,
        backgroundColor: Theme.of(context).colorScheme.surface,
        child: _isLoading && _logs.isEmpty
            ? const Center(child: CircularProgressIndicator())
            : _logs.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Text('📋', style: TextStyle(fontSize: 48)),
                          const SizedBox(height: 16),
                          Text(
                            'No triggered alerts yet',
                            style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            'When market price crosses an active rule, the event will appear here.',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: Colors.blueGrey.shade400, fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _logs.length,
                    itemBuilder: (ctx, i) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: LogCard(log: _logs[i]),
                    ),
                  ),
      ),
    );
  }
}
