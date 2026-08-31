class TradingChart {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.chart = null;
        this.candleSeries = null;
        this.volumeSeries = null;
        this.indicatorSeries = {};
        this.alertPriceLines = [];
        this.currentSymbol = EURUSD;
        this.currentTimeframe = 1m;
        this.activeIndicators = {
            ema20: false,
            ema50: false,
            ema200: false,
            bb: false
        };
        this.init();
    }

    init() {
        if (!this.container || typeof LightweightCharts === 'undefined') return;

        this.chart = LightweightCharts.createChart(this.container, {
            width: this.container.clientWidth,
            height: this.container.clientHeight || 450,
            layout: {
                background: { color: '#0f172a' },
                textColor: '#94a3b8',
            },
            grid: {
                vertLines: { color: '#1e293b' },
                horzLines: { color: '#1e293b' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
                vertLine: {
                    width: 1,
                    color: '#64748b',
                    style: LightweightCharts.LineStyle.Dashed,
                },
                horzLine: {
                    width: 1,
                    color: '#64748b',
                    style: LightweightCharts.LineStyle.Dashed,
                },
            },
            timeScale: {
                borderColor: '#334155',
                timeVisible: true,
                secondsVisible: false,
            },
            rightPriceScale: {
                borderColor: '#334155',
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.15,
                },
            },
        });

        this.candleSeries = this.chart.addCandlestickSeries({
            upColor: '#22c55e',
            downColor: '#ef4444',
            borderVisible: false,
            wickUpColor: '#22c55e',
            wickDownColor: '#ef4444',
        });

        this.volumeSeries = this.chart.addHistogramSeries({
            color: '#334155',
            priceFormat: { type: 'volume' },
            priceScaleId: '',
            scaleMargins: {
                top: 0.8,
                bottom: 0,
            },
        });

        window.addEventListener('resize', () => {
            if (this.chart && this.container) {
                this.chart.applyOptions({
                    width: this.container.clientWidth,
                    height: this.container.clientHeight || 450
                });
            }
        });
    }

    async loadSymbolData(symbol, timeframe) {
        this.currentSymbol = symbol;
        this.currentTimeframe = timeframe;

        try {
            const resp = await fetch(/api/market/candles?symbol=&timeframe=&limit=300);
            const data = await resp.json();
            if (data && data.length > 0) {
                const formattedCandles = data.map(d => ({
                    time: d.time,
                    open: d.open,
                    high: d.high,
                    low: d.low,
                    close: d.close,
                }));
                const formattedVolumes = data.map(d => ({
                    time: d.time,
                    value: d.volume,
                    color: d.close >= d.open ? 'rgba(34, 197, 94, 0.25)' : 'rgba(239, 68, 68, 0.25)'
                }));

                this.candleSeries.setData(formattedCandles);
                this.volumeSeries.setData(formattedVolumes);
                this.chart.timeScale().fitContent();

                await this.refreshActiveIndicators();
            }
        } catch (e) {
            console.error(Error loading candles:, e);
        }
    }

    updateTick(candle) {
        if (!this.candleSeries || !candle) return;
        this.candleSeries.update({
            time: candle.time,
            open: candle.open,
            high: candle.high,
            low: candle.low,
            close: candle.close,
        });
    }

    setAlertLines(alerts) {
        // Clear previous lines
        for (const line of this.alertPriceLines) {
            try {
                this.candleSeries.removePriceLine(line);
            } catch (e) {}
        }
        this.alertPriceLines = [];

        for (const alert of alerts) {
            if (alert.symbol === this.currentSymbol && alert.is_active && alert.params && alert.params.target_price) {
                const price = parseFloat(alert.params.target_price);
                const line = this.candleSeries.createPriceLine({
                    price: price,
                    color: alert.condition_type.includes('up') ? '#38bdf8' : '#fb7185',
                    lineWidth: 2,
                    lineStyle: LightweightCharts.LineStyle.Dashed,
                    axisLabelVisible: true,
                    title: ALERT # (),
                });
                this.alertPriceLines.push(line);
            }
        }
    }

    async toggleIndicator(name, active) {
        this.activeIndicators[name] = active;
        await this.refreshActiveIndicators();
    }

    async refreshActiveIndicators() {
        // Remove existing series
        for (const key in this.indicatorSeries) {
            if (this.indicatorSeries[key]) {
                this.chart.removeSeries(this.indicatorSeries[key]);
                delete this.indicatorSeries[key];
            }
        }

        // EMA 20
        if (this.activeIndicators.ema20) {
            await this._addIndicatorLine(ema, 20, #38bdf8, EMA 20, ema20);
        }
        // EMA 50
        if (this.activeIndicators.ema50) {
            await this._addIndicatorLine(ema, 50, #fbbf24, EMA 50, ema50);
        }
        // EMA 200
        if (this.activeIndicators.ema200) {
            await this._addIndicatorLine(ema, 200, #f43f5e, EMA 200, ema200);
        }
        // Bollinger Bands
        if (this.activeIndicators.bb) {
            await this._addIndicatorLine(bollinger, 20, #818cf8, BB Upper, bb_upper, upper);
            await this._addIndicatorLine(bollinger, 20, #94a3b8, BB Mid, bb_mid, middle);
            await this._addIndicatorLine(bollinger, 20, #818cf8, BB Lower, bb_lower, lower);
        }
    }

    async _addIndicatorLine(type, period, color, title, key, output = null) {
        try {
            let url = /api/market/indicators?symbol=&timeframe=&ind_type=&period=;
            if (output) url += &output=;
            const resp = await fetch(url);
            const data = await resp.json();
            if (data && data.length > 0) {
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
            console.error(Failed to load indicator :, e);
        }
    }
}
