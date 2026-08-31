class TradingChart {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.chart = null;
        this.candleSeries = null;
        this.volumeSeries = null;
        this.indicatorSeries = {};
        this.alertPriceLines = [];
        this.currentSymbol = 'EURUSD';
        this.currentTimeframe = '1m';
        this.isDarkMode = true;
        this.activeIndicators = {
            ema20: false,
            ema50: false,
            ema200: false,
            bb: false
        };
        this.init();
    }

    init() {
        if (!this.container || typeof LightweightCharts === 'undefined') {
            console.warn("LightweightCharts library or container not ready yet.");
            return;
        }

        try {
            const isDark = document.documentElement.classList.contains('dark');
            this.isDarkMode = isDark;

            this.chart = LightweightCharts.createChart(this.container, {
                width: this.container.clientWidth || 800,
                height: this.container.clientHeight || 450,
                layout: {
                    background: { color: isDark ? '#0f172a' : '#ffffff' },
                    textColor: isDark ? '#94a3b8' : '#475569',
                },
                grid: {
                    vertLines: { color: isDark ? '#1e293b' : '#f1f5f9' },
                    horzLines: { color: isDark ? '#1e293b' : '#f1f5f9' },
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                    vertLine: {
                        width: 1,
                        color: isDark ? '#64748b' : '#94a3b8',
                        style: LightweightCharts.LineStyle.Dashed,
                    },
                    horzLine: {
                        width: 1,
                        color: isDark ? '#64748b' : '#94a3b8',
                        style: LightweightCharts.LineStyle.Dashed,
                    },
                },
                timeScale: {
                    borderColor: isDark ? '#334155' : '#cbd5e1',
                    timeVisible: true,
                    secondsVisible: false,
                },
                rightPriceScale: {
                    borderColor: isDark ? '#334155' : '#cbd5e1',
                    scaleMargins: {
                        top: 0.1,
                        bottom: 0.15,
                    },
                },
            });

            // Add main candlestick series with TradingView green/red palette
            this.candleSeries = this.chart.addCandlestickSeries({
                upColor: '#10b981',
                downColor: '#f43f5e',
                borderUpColor: '#10b981',
                borderDownColor: '#f43f5e',
                wickUpColor: '#10b981',
                wickDownColor: '#f43f5e',
            });

            // Add volume histogram series
            this.volumeSeries = this.chart.addHistogramSeries({
                color: isDark ? '#38bdf8' : '#0284c7',
                priceFormat: {
                    type: 'volume',
                },
                priceScaleId: '',
                scaleMargins: {
                    top: 0.82,
                    bottom: 0,
                },
            });

            // Resize handler
            window.addEventListener('resize', () => {
                if (this.chart && this.container) {
                    this.chart.applyOptions({ width: this.container.clientWidth });
                }
            });
        } catch(e) {
            console.error("Chart creation error:", e);
        }
    }

    setTheme(isDark) {
        this.isDarkMode = isDark;
        if (!this.chart) return;

        try {
            this.chart.applyOptions({
                layout: {
                    background: { color: isDark ? '#0f172a' : '#ffffff' },
                    textColor: isDark ? '#94a3b8' : '#475569',
                },
                grid: {
                    vertLines: { color: isDark ? '#1e293b' : '#f1f5f9' },
                    horzLines: { color: isDark ? '#1e293b' : '#f1f5f9' },
                },
                crosshair: {
                    vertLine: { color: isDark ? '#64748b' : '#94a3b8' },
                    horzLine: { color: isDark ? '#64748b' : '#94a3b8' },
                },
                timeScale: {
                    borderColor: isDark ? '#334155' : '#cbd5e1',
                },
                rightPriceScale: {
                    borderColor: isDark ? '#334155' : '#cbd5e1',
                },
            });

            if (this.volumeSeries) {
                this.volumeSeries.applyOptions({
                    color: isDark ? '#38bdf8' : '#0284c7',
                });
            }
        } catch(e) {
            console.error("Set theme on chart error:", e);
        }
    }

    async loadCandles(symbol, timeframe) {
        this.currentSymbol = symbol;
        this.currentTimeframe = timeframe;
        if (!this.candleSeries) return;

        try {
            const resp = await fetch(`/api/market/candles?symbol=${symbol}&timeframe=${timeframe}&limit=300`);
            const data = await resp.json();
            if (data && Array.isArray(data) && data.length > 0) {
                const candleData = data.map(c => ({
                    time: c.time,
                    open: c.open,
                    high: c.high,
                    low: c.low,
                    close: c.close,
                }));
                const volData = data.map(c => ({
                    time: c.time,
                    value: c.volume || 1.0,
                    color: c.close >= c.open ? (this.isDarkMode ? '#064e3b88' : '#a7f3d088') : (this.isDarkMode ? '#88133788' : '#fecdd388')
                }));

                if (this.candleSeries) this.candleSeries.setData(candleData);
                if (this.volumeSeries) this.volumeSeries.setData(volData);
                if (this.chart) this.chart.timeScale().fitContent();

                // Refresh active overlays
                await this.refreshIndicators();
            }
        } catch (e) {
            console.error('Failed to load candles:', e);
        }
    }

    updateTick(symbol, tickData) {
        if (symbol !== this.currentSymbol || !this.candleSeries) return;

        try {
            if (tickData.candle_1m && this.currentTimeframe === '1m') {
                const c = tickData.candle_1m;
                this.candleSeries.update({
                    time: c.time,
                    open: c.open,
                    high: c.high,
                    low: c.low,
                    close: c.close,
                });
                if (this.volumeSeries) {
                    this.volumeSeries.update({
                        time: c.time,
                        value: c.volume || 1.0,
                        color: c.close >= c.open ? (this.isDarkMode ? '#064e3b88' : '#a7f3d088') : (this.isDarkMode ? '#88133788' : '#fecdd388')
                    });
                }
            }
        } catch(e) {
            console.error("Tick update error:", e);
        }
    }

    setAlertPriceLines(alerts) {
        if (!this.candleSeries) return;

        for (const line of this.alertPriceLines) {
            try { this.candleSeries.removePriceLine(line); } catch(e) {}
        }
        this.alertPriceLines = [];

        if (!Array.isArray(alerts)) return;

        const relevant = alerts.filter(a => a.symbol === this.currentSymbol && a.is_active);
        for (const a of relevant) {
            let target = null;
            if (a.params && a.params.target_price) target = a.params.target_price;
            else if (a.params && a.params.upper_bound) target = a.params.upper_bound;

            if (target !== null) {
                try {
                    const line = this.candleSeries.createPriceLine({
                        price: parseFloat(target),
                        color: '#f59e0b',
                        lineWidth: 1,
                        lineStyle: LightweightCharts.LineStyle.Dashed,
                        axisLabelVisible: true,
                        title: `ALERT #${a.id} (${(a.condition_type || '').replace('_', ' ')})`,
                    });
                    this.alertPriceLines.push(line);
                } catch(e) {}
            }
        }
    }

    toggleIndicator(name, isEnabled) {
        this.activeIndicators[name] = isEnabled;
        this.refreshIndicators();
    }

    async refreshIndicators() {
        if (!this.chart) return;

        for (const key of Object.keys(this.indicatorSeries)) {
            try { this.chart.removeSeries(this.indicatorSeries[key]); } catch (e) {}
        }
        this.indicatorSeries = {};

        if (this.activeIndicators.ema20) {
            await this._addIndicatorLine('ema', 20, '#38bdf8', 'EMA 20', 'ema20');
        }
        if (this.activeIndicators.ema50) {
            await this._addIndicatorLine('ema', 50, '#fbbf24', 'EMA 50', 'ema50');
        }
        if (this.activeIndicators.ema200) {
            await this._addIndicatorLine('ema', 200, '#f43f5e', 'EMA 200', 'ema200');
        }
        if (this.activeIndicators.bb) {
            await this._addIndicatorLine('bollinger', 20, '#818cf8', 'BB Upper', 'bb_upper', 'upper');
            await this._addIndicatorLine('bollinger', 20, '#94a3b8', 'BB Mid', 'bb_mid', 'middle');
            await this._addIndicatorLine('bollinger', 20, '#818cf8', 'BB Lower', 'bb_lower', 'lower');
        }
    }

    async _addIndicatorLine(type, period, color, title, key, output = null) {
        try {
            let url = `/api/market/indicators?symbol=${this.currentSymbol}&timeframe=${this.currentTimeframe}&ind_type=${type}&period=${period}`;
            if (output) url += `&output=${output}`;
            const resp = await fetch(url);
            const data = await resp.json();
            if (data && Array.isArray(data) && data.length > 0 && this.chart) {
                const lineSeries = this.chart.addLineSeries({
                    color: color,
                    lineWidth: 1.5,
                    title: title,
                    priceLineVisible: false,
                });
                lineSeries.setData(data);
                this.indicatorSeries[key] = lineSeries;
            }
        } catch (e) {
            console.error('Failed to load indicator:', e);
        }
    }
}
