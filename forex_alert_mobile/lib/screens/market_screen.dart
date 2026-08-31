import 'dart:async';
import 'package:flutter/material.dart';
import '../models/symbol_rate.dart';
import '../services/api_service.dart';
import '../services/theme_manager.dart';
import '../widgets/price_card.dart';
import 'create_alert_screen.dart';

class MarketScreen extends StatefulWidget {
  const MarketScreen({super.key});

  @override
  State<MarketScreen> createState() => _MarketScreenState();
}

class _MarketScreenState extends State<MarketScreen> {
  List<SymbolRate> _rates = [];
  bool _isLoading = true;
  Timer? _pollingTimer;

  final TextEditingController _simPriceController = TextEditingController();
  String _simSelectedSymbol = 'EURUSD';

  @override
  void initState() {
    super.initState();
    _fetchRates();
    _pollingTimer = Timer.periodic(const Duration(seconds: 2), (_) => _fetchRates());
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    _simPriceController.dispose();
    super.dispose();
  }

  Future<void> _fetchRates() async {
    final list = await ApiService.getSymbols();
    if (mounted && list.isNotEmpty) {
      setState(() {
        _rates = list;
        _isLoading = false;
      });
    }
  }

  void _openCreateAlert(SymbolRate rate) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => CreateAlertScreen(
        initialSymbol: rate.symbol,
        initialPrice: rate.currentPrice,
      ),
    );
  }

  Future<void> _injectSimulatedPrice() async {
    final price = double.tryParse(_simPriceController.text);
    if (price == null) return;

    final success = await ApiService.overrideTick(_simSelectedSymbol, price);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? 'Injected $price for $_simSelectedSymbol!' : 'Failed to reach server'),
          backgroundColor: success ? Theme.of(context).colorScheme.primary : const Color(0xFFF43F5E),
        ),
      );
      _fetchRates();
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Text('⚡', style: TextStyle(fontSize: 16)),
            ),
            const SizedBox(width: 10),
            Text(
              'Live Market Watch',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 17,
                color: Theme.of(context).colorScheme.onSurface,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(isDark ? Icons.light_mode_outlined : Icons.dark_mode_outlined),
            tooltip: isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode',
            onPressed: () => ThemeManager.toggleTheme(context),
          ),
          IconButton(
            icon: Icon(Icons.refresh, color: Theme.of(context).colorScheme.primary),
            onPressed: _fetchRates,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _fetchRates,
        color: Theme.of(context).colorScheme.primary,
        backgroundColor: Theme.of(context).colorScheme.surface,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Quick Simulation Bar
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Theme.of(context).dividerColor),
                boxShadow: [
                  BoxShadow(
                    color: isDark ? Colors.black.withValues(alpha: 0.2) : Colors.black.withValues(alpha: 0.04),
                    blurRadius: 6,
                    offset: const Offset(0, 3),
                  )
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.flash_on, color: isDark ? Colors.amberAccent : Colors.amber.shade700, size: 16),
                      const SizedBox(width: 6),
                      Text(
                        'TEST PRICE CROSS TRIGGER',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 0.5,
                          color: isDark ? Colors.blueGrey.shade300 : Colors.blueGrey.shade700,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10),
                        decoration: BoxDecoration(
                          color: isDark ? const Color(0xFF0F172A) : const Color(0xFFF1F5F9),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: Theme.of(context).dividerColor),
                        ),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<String>(
                            value: _simSelectedSymbol,
                            dropdownColor: Theme.of(context).colorScheme.surface,
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.onSurface,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                            items: _rates.map((r) => DropdownMenuItem(value: r.symbol, child: Text(r.symbol))).toList(),
                            onChanged: (v) => setState(() => _simSelectedSymbol = v!),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: TextField(
                          controller: _simPriceController,
                          keyboardType: const TextInputType.numberWithOptions(decimal: true),
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.onSurface,
                            fontFamily: 'monospace',
                            fontSize: 13,
                          ),
                          decoration: InputDecoration(
                            hintText: 'e.g. 1.08600',
                            hintStyle: TextStyle(
                              color: isDark ? Colors.blueGrey.shade600 : Colors.blueGrey.shade400,
                              fontSize: 12,
                            ),
                            filled: true,
                            fillColor: isDark ? const Color(0xFF0F172A) : const Color(0xFFF1F5F9),
                            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(10),
                              borderSide: BorderSide(color: Theme.of(context).dividerColor),
                            ),
                            enabledBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(10),
                              borderSide: BorderSide(color: Theme.of(context).dividerColor),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      ElevatedButton(
                        onPressed: _injectSimulatedPrice,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Theme.of(context).colorScheme.primary,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        child: const Text('Inject', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            Text(
              'INSTRUMENTS (TAP TO SET ALERT)',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.bold,
                letterSpacing: 0.5,
                color: isDark ? Colors.blueGrey.shade400 : Colors.blueGrey.shade600,
              ),
            ),
            const SizedBox(height: 10),

            if (_isLoading && _rates.isEmpty)
              const Center(child: Padding(padding: EdgeInsets.all(32), child: CircularProgressIndicator()))
            else
              ..._rates.map((rate) => Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: PriceCard(
                      rate: rate,
                      onTap: () => _openCreateAlert(rate),
                    ),
                  )),
          ],
        ),
      ),
    );
  }
}
