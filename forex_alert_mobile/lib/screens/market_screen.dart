import 'dart:async';
import 'package:flutter/material.dart';
import '../models/symbol_rate.dart';
import '../services/api_service.dart';
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
          backgroundColor: success ? const Color(0xFF0EA5E9) : const Color(0xFFF43F5E),
        ),
      );
      _fetchRates();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF080D1A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0F172A),
        elevation: 0,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: const Color(0xFF0EA5E9).withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Text('⚡', style: TextStyle(fontSize: 16)),
            ),
            const SizedBox(width: 10),
            const Text(
              'Live Market Watch',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 17, color: Colors.white),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Color(0xFF38BDF8)),
            onPressed: _fetchRates,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _fetchRates,
        color: const Color(0xFF38BDF8),
        backgroundColor: const Color(0xFF131D31),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Quick Simulation Bar
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFF131D31),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF1E293B)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.flash_on, color: Colors.amberAccent, size: 16),
                      const SizedBox(width: 6),
                      Text(
                        'TEST PRICE CROSS TRIGGER',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 0.5,
                          color: Colors.blueGrey.shade300,
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
                          color: const Color(0xFF0F172A),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: const Color(0xFF334155)),
                        ),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<String>(
                            value: _simSelectedSymbol,
                            dropdownColor: const Color(0xFF0F172A),
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
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
                          style: const TextStyle(color: Colors.white, fontFamily: 'monospace', fontSize: 13),
                          decoration: InputDecoration(
                            hintText: 'e.g. 1.08600',
                            hintStyle: TextStyle(color: Colors.blueGrey.shade600, fontSize: 12),
                            filled: true,
                            fillColor: const Color(0xFF0F172A),
                            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      ElevatedButton(
                        onPressed: _injectSimulatedPrice,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF0EA5E9),
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
                color: Colors.blueGrey.shade400,
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
