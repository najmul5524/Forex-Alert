class TradingChart {
    constructor(containerOrId, symbol = 'EURUSD', timeframe = '1m') {
        this.container = typeof containerOrId === 'string' ? document.getElementById(containerOrId) : containerOrId;
        this.chart = null;
        this.candleSeries = null;
        this.volumeSeries = null;
        this.alertPriceLines = [];
        this.currentSymbol = symbol;
        this.currentTimeframe = timeframe;
        this.isDarkMode = true;
        this.candlesData = [];

        this.chartType = 'candle'; // candle, bar, line, area, heikin_ashi, baseline
        this.timezoneOffsetSeconds = 0; // UTC default
        this.rawCandles = [];

        // Active dynamic indicators: Array of { id, type, name, params, color, visible, seriesList: [] }
        this.indicators = [];
        this.indicatorCounter = 0;

        // Drawing state
        this.activeTool = 'cursor'; // cursor, horizontal_ray, trendline, fibonacci, measure
        this.drawings = []; // Array of drawing objects
        this.currentDrawing = null;
        this.overlayCanvas = null;
        this.overlayCtx = null;
        this._resizeObserver = null;

        // Callbacks
        this.onLegendUpdate = null;
        this.onPriceScaleAlertClick = null;
        this.onCrosshairMoveCallback = null;

        this.init();
    }

    destroy() {
        if (this._resizeObserver) {
            this._resizeObserver.disconnect();
            this._resizeObserver = null;
        }
        if (this.chart) {
            try { this.chart.remove(); } catch(e) {}
            this.chart = null;
        }
        if (this.overlayCanvas) {
            try { this.overlayCanvas.remove(); } catch(e) {}
            this.overlayCanvas = null;
        }
    }

    init() {
        if (!this.container || typeof LightweightCharts === 'undefined') {
            console.warn("Chart container or LightweightCharts not ready.");
            return;
        }

        try {
            const isDark = document.documentElement.classList.contains('dark');
            this.isDarkMode = isDark;

            // Make sure container has position relative for overlay canvas
            this.container.style.position = 'relative';
            this.container.style.overflow = 'hidden';

            const w = this.container.clientWidth || 400;
            const h = this.container.clientHeight || 300;

            this.chart = LightweightCharts.createChart(this.container, {
                width: w,
                height: h,
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
                    rightOffset: 6,
                    barSpacing: 6,
                    minBarSpacing: 0.5,
                },
                rightPriceScale: {
                    borderColor: isDark ? '#334155' : '#cbd5e1',
                    scaleMargins: {
                        top: 0.12,
                        bottom: 0.12,
                    },
                    autoScale: true,
                },
            });

            this.createMainSeries(this.chartType);

            // Setup crosshair move for OHLCV tracking with timezone formatting
            this.chart.subscribeCrosshairMove((param) => {
                if (!param || !param.time || !param.seriesPrices) {
                    if (this.onCrosshairMoveCallback) this.onCrosshairMoveCallback(null);
                    return;
                }
                const candle = param.seriesPrices.get(this.candleSeries);
                if (candle && this.onCrosshairMoveCallback) {
                    this.onCrosshairMoveCallback({
                        time: param.time,
                        open: candle.open !== undefined ? candle.open : candle.value,
                        high: candle.high !== undefined ? candle.high : candle.value,
                        low: candle.low !== undefined ? candle.low : candle.value,
                        close: candle.close !== undefined ? candle.close : candle.value,
                        volume: 0
                    });
                }
            });

            this.setupDrawingCanvas();

            // TradingView-style on-demand historical data loading when scrolling left
            this.isLoadingOlder = false;
            this.hasMoreOlder = true;
            this.chart.timeScale().subscribeVisibleLogicalRangeChange(async (newRange) => {
                if (!newRange || this.isLoadingOlder || !this.hasMoreOlder || !this.rawCandles || this.rawCandles.length === 0) return;
                if (newRange.from < 25) {
                    await this.loadMoreOlderCandles();
                }
            });

            // Resize Observer to handle grid layout splits dynamically
            if (window.ResizeObserver) {
                this._resizeObserver = new ResizeObserver(entries => {
                    for (const entry of entries) {
                        const { width, height } = entry.contentRect;
                        if (width > 0 && height > 0 && this.chart) {
                            this.chart.applyOptions({ width: width, height: height });
                            this.resizeDrawingCanvas();
                        }
                    }
                });
                this._resizeObserver.observe(this.container);
            }

            // Window resize fallback
            window.addEventListener('resize', () => {
                if (this.chart && this.container) {
                    this.chart.applyOptions({ 
                        width: this.container.clientWidth, 
                        height: this.container.clientHeight 
                    });
                    this.resizeDrawingCanvas();
                }
            });
        } catch (e) {
            console.error("TradingChart init failed:", e);
        }
    }

    createMainSeries(type = 'candle') {
        if (!this.chart) return;
        if (this.candleSeries) {
            try { this.chart.removeSeries(this.candleSeries); } catch(e) {}
            this.candleSeries = null;
        }

        const sym = (this.currentSymbol || '').toUpperCase();
        let precision = 2;
        if (['EURUSD', 'GBPUSD', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD', 'EURGBP'].includes(sym)) {
            precision = 5;
        } else if (['USDJPY', 'EURJPY', 'GBPJPY'].includes(sym)) {
            precision = 3;
        } else if (['XRPUSDT', 'XAGUSD'].includes(sym)) {
            precision = 4;
        } else if (['XAUUSD', 'USOIL', 'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'SPX500', 'NAS100', 'US30'].includes(sym)) {
            precision = 2;
        }
        const minMove = 1 / Math.pow(10, precision);

        const seriesOpts = {
            priceFormat: {
                type: 'price',
                precision: precision,
                minMove: minMove,
            },
        };

        const isDark = this.isDarkMode;
        if (type === 'bar') {
            this.candleSeries = this.chart.addBarSeries({
                ...seriesOpts,
                upColor: '#089981',
                downColor: '#f23645',
            });
        } else if (type === 'line') {
            this.candleSeries = this.chart.addLineSeries({
                ...seriesOpts,
                color: '#2962ff',
                lineWidth: 2,
            });
        } else if (type === 'area') {
            this.candleSeries = this.chart.addAreaSeries({
                ...seriesOpts,
                topColor: 'rgba(41, 98, 255, 0.35)',
                bottomColor: 'rgba(41, 98, 255, 0.0)',
                lineColor: '#2962ff',
                lineWidth: 2,
            });
        } else if (type === 'baseline') {
            this.candleSeries = this.chart.addBaselineSeries({
                ...seriesOpts,
                topLineColor: '#089981',
                topFillColor1: 'rgba(8, 153, 129, 0.28)',
                topFillColor2: 'rgba(8, 153, 129, 0.05)',
                bottomLineColor: '#f23645',
                bottomFillColor1: 'rgba(242, 54, 69, 0.05)',
                bottomFillColor2: 'rgba(242, 54, 69, 0.28)',
            });
        } else {
            // Standard Candlestick or Heikin-Ashi (TradingView styling)
            this.candleSeries = this.chart.addCandlestickSeries({
                ...seriesOpts,
                upColor: '#089981',
                downColor: '#f23645',
                borderUpColor: '#089981',
                borderDownColor: '#f23645',
                wickUpColor: '#089981',
                wickDownColor: '#f23645',
            });
        }
    }

    setChartType(type) {
        this.chartType = type;
        this.createMainSeries(type);
        if (this.rawCandles && this.rawCandles.length > 0) {
            this.renderCandlesData(this.rawCandles);
        }
    }

    setTimezone(offsetHours) {
        this.timezoneOffsetSeconds = offsetHours * 3600;
        if (this.rawCandles && this.rawCandles.length > 0) {
            this.renderCandlesData(this.rawCandles);
        }
    }

    resize() {
        if (!this.chart || !this.container) return;
        const w = this.container.clientWidth;
        const h = this.container.clientHeight;
        if (w > 0 && h > 0) {
            this.chart.applyOptions({ width: w, height: h });
            this.resizeDrawingCanvas();
        }
    }

    resetView() {
        if (!this.chart) return;
        try {
            this.chart.timeScale().scrollToRealTime();
            this.chart.timeScale().fitContent();
            this.chart.applyOptions({
                rightPriceScale: {
                    autoScale: true
                }
            });
            this.redrawDrawings();
        } catch (e) {
            console.error("Error resetting chart view:", e);
        }
    }

    zoomIn() {
        if (!this.chart) return;
        try {
            const range = this.chart.timeScale().getVisibleLogicalRange();
            if (!range) return;
            const span = range.to - range.from;
            const delta = Math.max(1, span * 0.2);
            this.chart.timeScale().setVisibleLogicalRange({
                from: range.from + delta,
                to: range.to - delta
            });
            this.redrawDrawings();
        } catch(e) {}
    }

    zoomOut() {
        if (!this.chart) return;
        try {
            const range = this.chart.timeScale().getVisibleLogicalRange();
            if (!range) return;
            const span = range.to - range.from;
            const delta = Math.max(1, span * 0.2);
            this.chart.timeScale().setVisibleLogicalRange({
                from: range.from - delta,
                to: range.to + delta
            });
            this.redrawDrawings();
        } catch(e) {}
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

            this.redrawDrawings();
        } catch(e) {
            console.error("setTheme error:", e);
        }
    }

    async loadCandles(symbol, timeframe) {
        this.currentSymbol = symbol;
        this.currentTimeframe = timeframe;
        this.createMainSeries(this.chartType);
        if (!this.candleSeries) return;

        try {
            const resp = await fetch(`/api/market/candles?symbol=${symbol}&timeframe=${timeframe}&limit=1500`);
            const data = await resp.json();
            if (data && Array.isArray(data) && data.length > 0) {
                this.rawCandles = data;
                this.renderCandlesData(data);
                if (this.chart) {
                    this.chart.timeScale().fitContent();
                    this.chart.applyOptions({
                        rightPriceScale: { autoScale: true }
                    });
                }

                // Refresh all active indicators
                await this.refreshAllIndicators();
                this.redrawDrawings();
            }
        } catch (e) {
            console.error('Failed to load candles:', e);
        }
    }

    async loadMoreOlderCandles() {
        if (this.isLoadingOlder || !this.hasMoreOlder || !this.rawCandles || this.rawCandles.length === 0) return;
        this.isLoadingOlder = true;

        const oldestTime = this.rawCandles[0].time;
        try {
            const resp = await fetch(`/api/market/candles?symbol=${this.currentSymbol}&timeframe=${this.currentTimeframe}&to_time=${oldestTime}&limit=1000`);
            const olderData = await resp.json();
            if (olderData && Array.isArray(olderData) && olderData.length > 0) {
                const merged = [...olderData, ...this.rawCandles];
                this.rawCandles = merged;
                this.renderCandlesData(merged);
            } else {
                this.hasMoreOlder = false;
            }
        } catch(e) {
            console.warn("Could not fetch older candles:", e);
        } finally {
            this.isLoadingOlder = false;
        }
    }

    renderCandlesData(data) {
        if (!data || data.length === 0 || !this.candleSeries) return;

        const tzOffset = this.timezoneOffsetSeconds || 0;
        const sorted = [...data].sort((a, b) => a.time - b.time);
        
        // Strict deduplication by final adjusted integer timestamp
        const cleanMap = new Map();
        for (const item of sorted) {
            if (!item || item.time === undefined || item.time === null) continue;
            const t = Math.floor(Number(item.time) + tzOffset);
            const o = Number(item.open);
            const cl = Number(item.close);
            let h = Number(item.high);
            let l = Number(item.low);
            if (isNaN(o) || isNaN(cl)) continue;
            if (isNaN(h) || h < Math.max(o, cl)) h = Math.max(o, cl);
            if (isNaN(l) || l > Math.min(o, cl)) l = Math.min(o, cl);
            const v = Number(item.volume) || 1.0;
            cleanMap.set(t, { time: t, open: o, high: h, low: l, close: cl, volume: v, rawTime: item.time });
        }

        const uniqueData = Array.from(cleanMap.values()).sort((a, b) => a.time - b.time);
        if (uniqueData.length === 0) return;

        let formattedData = [];
        if (this.chartType === 'heikin_ashi') {
            let haOpen = (uniqueData[0].open + uniqueData[0].close) / 2.0;
            formattedData = uniqueData.map((c, idx) => {
                const haClose = (c.open + c.high + c.low + c.close) / 4.0;
                if (idx > 0) {
                    haOpen = (haOpen + formattedData[idx - 1].close) / 2.0;
                }
                const haHigh = Math.max(c.high, haOpen, haClose);
                const haLow = Math.min(c.low, haOpen, haClose);
                return {
                    time: c.time,
                    open: haOpen,
                    high: haHigh,
                    low: haLow,
                    close: haClose
                };
            });
        } else if (['line', 'area', 'baseline'].includes(this.chartType)) {
            formattedData = uniqueData.map(c => ({
                time: c.time,
                value: c.close
            }));
        } else {
            // Standard Candlestick or OHLC Bars
            formattedData = uniqueData.map(c => ({
                time: c.time,
                open: c.open,
                high: c.high,
                low: c.low,
                close: c.close
            }));
        }

        try {
            this.candleSeries.setData(formattedData);
        } catch (err) {
            console.warn("Candle series setData warning:", err);
        }

        // Track last forming candle
        const last = uniqueData[uniqueData.length - 1];
        this.currentCandle = {
            time: last.rawTime,
            open: last.open,
            high: last.high,
            low: last.low,
            close: last.close,
            volume: last.volume
        };
    }

    parseTfSeconds(tfStr) {
        if (!tfStr) return 60;
        const tf = String(tfStr).toLowerCase().trim();
        const map = {
            "1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800, "45m": 2700,
            "1h": 3600, "2h": 7200, "4h": 14400, "1d": 86400, "1w": 604800
        };
        if (map[tf]) return map[tf];
        const match = tf.match(/^(\d+)([mhdwd])$/);
        if (match) {
            const val = parseInt(match[1]);
            const unit = match[2];
            if (unit === 'm') return val * 60;
            if (unit === 'h') return val * 3600;
            if (unit === 'd') return val * 86400;
            if (unit === 'w') return val * 604800;
        }
        return 60;
    }

    updateTick(symbol, tickData) {
        if (symbol !== this.currentSymbol || !this.candleSeries) return;

        try {
            const price = typeof tickData.price === 'number' ? tickData.price : parseFloat(tickData.price);
            if (isNaN(price)) return;

            const tfSec = this.parseTfSeconds(this.currentTimeframe);
            const nowTs = tickData.timestamp || Math.floor(Date.now() / 1000);
            const bucket = Math.floor(nowTs / tfSec) * tfSec;
            const volume = tickData.volume || 1.0;
            const tzOffset = this.timezoneOffsetSeconds || 0;

            if (!this.currentCandle || bucket > this.currentCandle.time) {
                // New bar for the active timeframe has opened
                this.currentCandle = {
                    time: bucket,
                    open: price,
                    high: price,
                    low: price,
                    close: price,
                    volume: volume
                };
            } else {
                // Update currently forming candle
                this.currentCandle.high = Math.max(this.currentCandle.high, price);
                this.currentCandle.low = Math.min(this.currentCandle.low, price);
                this.currentCandle.close = price;
                this.currentCandle.volume = (this.currentCandle.volume || 0) + volume;
            }

            if (['line', 'area', 'baseline'].includes(this.chartType)) {
                this.candleSeries.update({
                    time: this.currentCandle.time + tzOffset,
                    value: price
                });
            } else {
                this.candleSeries.update({
                    time: this.currentCandle.time + tzOffset,
                    open: this.currentCandle.open,
                    high: this.currentCandle.high,
                    low: this.currentCandle.low,
                    close: this.currentCandle.close,
                });
            }

            if (this.volumeSeries) {
                this.volumeSeries.update({
                    time: this.currentCandle.time + tzOffset,
                    value: this.currentCandle.volume,
                    color: this.currentCandle.close >= this.currentCandle.open 
                        ? (this.isDarkMode ? '#064e3b88' : '#a7f3d088') 
                        : (this.isDarkMode ? '#88133788' : '#fecdd388')
                });
            }
        } catch(e) {
            console.error("Tick update error on timeframe", this.currentTimeframe, e);
        }
    }

    // ==========================================
    // DYNAMIC INDICATOR MANAGEMENT (TradingView style)
    // ==========================================
    async addIndicator(type, params = {}, color = '#38bdf8') {
        const id = `ind_${++this.indicatorCounter}`;
        const indType = type.toLowerCase();
        let name = indType.toUpperCase();
        if (params.period) name += ` ${params.period}`;
        if (params.source) name += ` ${params.source}`;

        const indObj = {
            id: id,
            type: indType,
            name: name,
            params: { period: 20, source: 'close', std_dev: 2.0, fast: 12, slow: 26, signal: 9, ...params },
            color: color,
            visible: true,
            currentValue: null,
            seriesList: []
        };

        this.indicators.push(indObj);
        await this._renderIndicator(indObj);
        this._notifyLegendUpdate();
        return indObj;
    }

    async removeIndicator(id) {
        const idx = this.indicators.findIndex(i => i.id === id);
        if (idx === -1) return;

        const ind = this.indicators[idx];
        for (const s of ind.seriesList) {
            try { this.chart.removeSeries(s); } catch (e) {}
        }
        this.indicators.splice(idx, 1);
        this._notifyLegendUpdate();
    }

    async toggleIndicatorVisibility(id) {
        const ind = this.indicators.find(i => i.id === id);
        if (!ind) return;

        ind.visible = !ind.visible;
        if (!ind.visible) {
            for (const s of ind.seriesList) {
                try { this.chart.removeSeries(s); } catch (e) {}
            }
            ind.seriesList = [];
        } else {
            await this._renderIndicator(ind);
        }
        this._notifyLegendUpdate();
    }

    async updateIndicatorParams(id, newParams, newColor) {
        const ind = this.indicators.find(i => i.id === id);
        if (!ind) return;

        ind.params = { ...ind.params, ...newParams };
        if (newColor) ind.color = newColor;

        let name = ind.type.toUpperCase();
        if (ind.params.period) name += ` ${ind.params.period}`;
        if (ind.params.source) name += ` ${ind.params.source}`;
        ind.name = name;

        // Clear existing series & rerender
        for (const s of ind.seriesList) {
            try { this.chart.removeSeries(s); } catch (e) {}
        }
        ind.seriesList = [];

        if (ind.visible) {
            await this._renderIndicator(ind);
        }
        this._notifyLegendUpdate();
    }

    async refreshAllIndicators() {
        for (const ind of this.indicators) {
            for (const s of ind.seriesList) {
                try { this.chart.removeSeries(s); } catch (e) {}
            }
            ind.seriesList = [];
            if (ind.visible) {
                await this._renderIndicator(ind);
            }
        }
        this._notifyLegendUpdate();
    }

    async _renderIndicator(ind) {
        if (!this.chart) return;

        const p = ind.params;
        try {
            if (ind.type in { ema: 1, sma: 1, wma: 1, rsi: 1, atr: 1, hma: 1, vwap: 1, supertrend: 1 }) {
                let url = `/api/market/indicators?symbol=${this.currentSymbol}&timeframe=${this.currentTimeframe}&ind_type=${ind.type}&period=${p.period || 14}&source=${p.source || 'close'}`;
                const resp = await fetch(url);
                const data = await resp.json();
                if (data && Array.isArray(data) && data.length > 0) {
                    const lineSeries = this.chart.addLineSeries({
                        color: ind.color,
                        lineWidth: ind.type === 'supertrend' ? 2 : 1.5,
                        title: ind.name,
                        priceLineVisible: false,
                    });
                    lineSeries.setData(data);
                    ind.seriesList.push(lineSeries);
                    ind.currentValue = data[data.length - 1].value;
                }
            } else if (ind.type in { stochastic: 1, stoch: 1 }) {
                for (const out of ['k', 'd']) {
                    let url = `/api/market/indicators?symbol=${this.currentSymbol}&timeframe=${this.currentTimeframe}&ind_type=stochastic&k_period=${p.k_period || 14}&d_period=${p.d_period || 3}&smooth_k=${p.smooth_k || 3}&output=${out}`;
                    const resp = await fetch(url);
                    const data = await resp.json();
                    if (data && Array.isArray(data) && data.length > 0) {
                        const lineSeries = this.chart.addLineSeries({
                            color: out === 'k' ? ind.color : '#f43f5e',
                            lineWidth: 1.5,
                            title: `Stoch ${out.toUpperCase()}`,
                            priceLineVisible: false,
                        });
                        lineSeries.setData(data);
                        ind.seriesList.push(lineSeries);
                        if (out === 'k') ind.currentValue = data[data.length - 1].value;
                    }
                }
            } else if (ind.type in { bollinger: 1, bb: 1 }) {
                // Fetch Upper, Middle, Lower
                for (const band of ['upper', 'middle', 'lower']) {
                    let url = `/api/market/indicators?symbol=${this.currentSymbol}&timeframe=${this.currentTimeframe}&ind_type=bollinger&period=${p.period || 20}&std_dev=${p.std_dev || 2.0}&source=${p.source || 'close'}&output=${band}`;
                    const resp = await fetch(url);
                    const data = await resp.json();
                    if (data && Array.isArray(data) && data.length > 0) {
                        const lineSeries = this.chart.addLineSeries({
                            color: band === 'middle' ? '#94a3b8' : ind.color,
                            lineWidth: band === 'middle' ? 1 : 1.5,
                            lineStyle: band === 'middle' ? LightweightCharts.LineStyle.Dotted : LightweightCharts.LineStyle.Solid,
                            title: `BB ${band.toUpperCase()}`,
                            priceLineVisible: false,
                        });
                        lineSeries.setData(data);
                        ind.seriesList.push(lineSeries);
                        if (band === 'upper') ind.currentValue = data[data.length - 1].value;
                    }
                }
            } else if (ind.type === 'macd') {
                // Fetch MACD and Signal
                for (const out of ['macd', 'signal']) {
                    let url = `/api/market/indicators?symbol=${this.currentSymbol}&timeframe=${this.currentTimeframe}&ind_type=macd&fast=${p.fast || 12}&slow=${p.slow || 26}&signal=${p.signal || 9}&output=${out}`;
                    const resp = await fetch(url);
                    const data = await resp.json();
                    if (data && Array.isArray(data) && data.length > 0) {
                        const lineSeries = this.chart.addLineSeries({
                            color: out === 'macd' ? ind.color : '#f43f5e',
                            lineWidth: 1.5,
                            title: `MACD ${out.toUpperCase()}`,
                            priceLineVisible: false,
                        });
                        lineSeries.setData(data);
                        ind.seriesList.push(lineSeries);
                        if (out === 'macd') ind.currentValue = data[data.length - 1].value;
                    }
                }
            }
        } catch (e) {
            console.error(`Error rendering indicator ${ind.name}:`, e);
        }
    }

    _notifyLegendUpdate() {
        if (this.onLegendUpdate) {
            this.onLegendUpdate([...this.indicators]);
        }
    }

    // ==========================================
    // DRAWING TOOLS (TradingView Canvas Overlay)
    // ==========================================
    setupDrawingCanvas() {
        this.overlayCanvas = document.createElement('canvas');
        this.overlayCanvas.className = 'absolute inset-0 pointer-events-none z-10';
        this.overlayCanvas.style.width = '100%';
        this.overlayCanvas.style.height = '100%';
        this.container.appendChild(this.overlayCanvas);
        this.overlayCtx = this.overlayCanvas.getContext('2d');
        this.resizeDrawingCanvas();

        // Mouse drawing events on container
        this.container.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.container.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.container.addEventListener('mouseup', (e) => this.handleMouseUp(e));

        // Keyboard Delete listener
        window.addEventListener('keydown', (e) => {
            if ((e.key === 'Delete' || e.key === 'Backspace') && this.selectedDrawingId) {
                // Do not delete if typing in an input
                if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)) return;
                this.removeDrawing(this.selectedDrawingId);
            }
        });
    }

    resizeDrawingCanvas() {
        if (!this.overlayCanvas || !this.container) return;
        const rect = this.container.getBoundingClientRect();
        this.overlayCanvas.width = rect.width;
        this.overlayCanvas.height = rect.height;
        this.redrawDrawings();
    }

    setDrawingTool(tool) {
        this.activeTool = tool;
        this.selectedDrawingId = null;
        this.hideDrawingToolbar();
        if (tool === 'cursor') {
            this.container.style.cursor = 'default';
        } else if (tool === 'clear') {
            this.drawings = [];
            this.redrawDrawings();
            this.activeTool = 'cursor';
            this.container.style.cursor = 'default';
        } else {
            this.container.style.cursor = 'crosshair';
        }
    }

    removeDrawing(id) {
        this.drawings = this.drawings.filter(d => d.id !== id);
        if (this.selectedDrawingId === id) {
            this.selectedDrawingId = null;
            this.hideDrawingToolbar();
        }
        this.redrawDrawings();
    }

    updateDrawing(id, updates) {
        const d = this.drawings.find(dr => dr.id === id);
        if (d) {
            Object.assign(d, updates);
            this.redrawDrawings();
        }
    }

    showDrawingToolbar(drawing, clientX, clientY) {
        let tb = this.container.querySelector('.floating-drawing-toolbar');
        if (!tb) {
            tb = document.createElement('div');
            tb.className = 'floating-drawing-toolbar absolute z-30 flex items-center gap-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 shadow-xl rounded-lg px-2 py-1 select-none text-xs';
            this.container.appendChild(tb);
        }

        const colors = ['#38bdf8', '#10b981', '#f43f5e', '#f59e0b', '#a855f7', '#ffffff'];
        const colorBtns = colors.map(c => 
            `<button class="w-3.5 h-3.5 rounded-full border border-slate-300 dark:border-slate-600 transition-transform active:scale-90" style="background-color: ${c}" data-color="${c}" title="Change Color"></button>`
        ).join('');

        tb.innerHTML = `
            <div class="flex items-center gap-1 mr-1">
                ${colorBtns}
            </div>
            <div class="h-3 w-px bg-slate-200 dark:bg-slate-700"></div>
            <select class="draw-width-select bg-transparent text-[11px] font-bold text-slate-700 dark:text-slate-300 focus:outline-none cursor-pointer">
                <option value="1" ${drawing.lineWidth === 1 ? 'selected' : ''}>1px</option>
                <option value="2" ${drawing.lineWidth === 2 || !drawing.lineWidth ? 'selected' : ''}>2px</option>
                <option value="3" ${drawing.lineWidth === 3 ? 'selected' : ''}>3px</option>
                <option value="4" ${drawing.lineWidth === 4 ? 'selected' : ''}>4px</option>
            </select>
            <div class="h-3 w-px bg-slate-200 dark:bg-slate-700"></div>
            <button class="draw-delete-btn text-rose-500 hover:text-rose-600 font-bold px-1.5 py-0.5 rounded hover:bg-rose-50 dark:hover:bg-rose-950 transition-colors" title="Delete Drawing (Del)">
                ✕
            </button>
        `;

        tb.querySelectorAll('[data-color]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.updateDrawing(drawing.id, { color: btn.dataset.color });
            });
        });

        const widthSelect = tb.querySelector('.draw-width-select');
        if (widthSelect) {
            widthSelect.addEventListener('change', (e) => {
                e.stopPropagation();
                this.updateDrawing(drawing.id, { lineWidth: parseInt(e.target.value) });
            });
        }

        const delBtn = tb.querySelector('.draw-delete-btn');
        if (delBtn) {
            delBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeDrawing(drawing.id);
            });
        }

        const rect = this.container.getBoundingClientRect();
        const top = Math.max(10, (clientY - rect.top) - 45);
        const left = Math.max(10, Math.min(rect.width - 240, (clientX - rect.left) - 100));

        tb.style.top = `${top}px`;
        tb.style.left = `${left}px`;
        tb.style.display = 'flex';
    }

    hideDrawingToolbar() {
        const tb = this.container.querySelector('.floating-drawing-toolbar');
        if (tb) tb.style.display = 'none';
    }

    handleMouseDown(e) {
        if (!this.overlayCtx) return;

        const rect = this.container.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        if (this.activeTool === 'cursor') {
            // Hit test drawings for selection / editing / deletion
            let hit = null;
            for (let i = this.drawings.length - 1; i >= 0; i--) {
                const d = this.drawings[i];
                if (d.type === 'horizontal_ray') {
                    if (Math.abs(y - d.y) <= 8) { hit = d; break; }
                } else if (d.type === 'trendline') {
                    const A = x - d.startX;
                    const B = y - d.startY;
                    const C = d.endX - d.startX;
                    const D = d.endY - d.startY;
                    const dot = A * C + B * D;
                    const len_sq = C * C + D * D;
                    let param = -1;
                    if (len_sq !== 0) param = dot / len_sq;
                    let xx, yy;
                    if (param < 0) { xx = d.startX; yy = d.startY; }
                    else if (param > 1) { xx = d.endX; yy = d.endY; }
                    else { xx = d.startX + param * C; yy = d.startY + param * D; }
                    const dist = Math.hypot(x - xx, y - yy);
                    if (dist <= 8) { hit = d; break; }
                } else if (d.type in { fibonacci: 1, measure: 1 }) {
                    const minX = Math.min(d.startX, d.endX);
                    const maxX = Math.max(d.startX, d.endX);
                    const minY = Math.min(d.startY, d.endY);
                    const maxY = Math.max(d.startY, d.endY);
                    if (x >= minX - 6 && x <= maxX + 6 && y >= minY - 6 && y <= maxY + 6) {
                        hit = d; break;
                    }
                }
            }

            if (hit) {
                this.selectedDrawingId = hit.id;
                this.showDrawingToolbar(hit, e.clientX, e.clientY);
                this.redrawDrawings();
            } else {
                this.selectedDrawingId = null;
                this.hideDrawingToolbar();
                this.redrawDrawings();
            }
            return;
        }

        if (this.activeTool === 'horizontal_ray') {
            const price = this.candleSeries.coordinateToPrice(y);
            const id = `dr_${Date.now()}_${Math.floor(Math.random()*1000)}`;
            const newDr = {
                id: id,
                type: 'horizontal_ray',
                y: y,
                price: price,
                color: '#f59e0b',
                lineWidth: 2
            };
            this.drawings.push(newDr);
            this.selectedDrawingId = id;
            this.showDrawingToolbar(newDr, e.clientX, e.clientY);
            this.redrawDrawings();
            this.activeTool = 'cursor';
            this.container.style.cursor = 'default';
        } else if (this.activeTool in { trendline: 1, fibonacci: 1, measure: 1 }) {
            this.currentDrawing = {
                id: `dr_${Date.now()}_${Math.floor(Math.random()*1000)}`,
                type: this.activeTool,
                startX: x,
                startY: y,
                endX: x,
                endY: y,
                color: '#38bdf8',
                lineWidth: 2
            };
        }
    }

    handleMouseMove(e) {
        if (!this.currentDrawing) return;

        const rect = this.container.getBoundingClientRect();
        this.currentDrawing.endX = e.clientX - rect.left;
        this.currentDrawing.endY = e.clientY - rect.top;
        this.redrawDrawings();
    }

    handleMouseUp(e) {
        if (this.currentDrawing) {
            this.drawings.push(this.currentDrawing);
            this.selectedDrawingId = this.currentDrawing.id;
            this.showDrawingToolbar(this.currentDrawing, e.clientX, e.clientY);
            this.currentDrawing = null;
            this.redrawDrawings();
            this.activeTool = 'cursor';
            this.container.style.cursor = 'default';
        }
    }

    redrawDrawings() {
        if (!this.overlayCtx || !this.overlayCanvas) return;

        const ctx = this.overlayCtx;
        ctx.clearRect(0, 0, this.overlayCanvas.width, this.overlayCanvas.height);

        const all = [...this.drawings];
        if (this.currentDrawing) all.push(this.currentDrawing);

        for (const d of all) {
            const isSelected = d.id === this.selectedDrawingId;
            const lWidth = d.lineWidth || 2;

            if (d.type === 'horizontal_ray') {
                ctx.save();
                ctx.strokeStyle = d.color || '#f59e0b';
                ctx.lineWidth = isSelected ? lWidth + 1.5 : lWidth;
                ctx.setLineDash(isSelected ? [] : [4, 4]);
                ctx.beginPath();
                ctx.moveTo(0, d.y);
                ctx.lineTo(this.overlayCanvas.width, d.y);
                ctx.stroke();

                // Price label tag
                if (d.price) {
                    ctx.fillStyle = d.color || '#f59e0b';
                    ctx.fillRect(this.overlayCanvas.width - 75, d.y - 10, 70, 20);
                    ctx.fillStyle = '#000000';
                    ctx.font = 'bold 10px monospace';
                    ctx.fillText(d.price.toFixed(2), this.overlayCanvas.width - 70, d.y + 4);
                }

                if (isSelected) {
                    ctx.fillStyle = '#ffffff';
                    ctx.strokeStyle = d.color || '#f59e0b';
                    ctx.lineWidth = 2;
                    ctx.beginPath(); ctx.arc(40, d.y, 4, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
                }
                ctx.restore();
            } else if (d.type === 'trendline') {
                ctx.save();
                ctx.strokeStyle = d.color || '#38bdf8';
                ctx.lineWidth = isSelected ? lWidth + 1.5 : lWidth;
                ctx.beginPath();
                ctx.moveTo(d.startX, d.startY);
                ctx.lineTo(d.endX, d.endY);
                ctx.stroke();

                // Endpoint handles
                ctx.fillStyle = isSelected ? '#ffffff' : (d.color || '#38bdf8');
                ctx.strokeStyle = d.color || '#38bdf8';
                ctx.lineWidth = 2;
                ctx.beginPath(); ctx.arc(d.startX, d.startY, isSelected ? 5 : 3.5, 0, Math.PI * 2); ctx.fill(); if (isSelected) ctx.stroke();
                ctx.beginPath(); ctx.arc(d.endX, d.endY, isSelected ? 5 : 3.5, 0, Math.PI * 2); ctx.fill(); if (isSelected) ctx.stroke();
                ctx.restore();
            } else if (d.type === 'fibonacci') {
                ctx.save();
                const fibLevels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0];
                const dy = d.endY - d.startY;
                const colors = ['#f43f5e', '#fb923c', '#fbbf24', '#34d399', '#38bdf8', '#818cf8', '#a855f7'];

                fibLevels.forEach((level, idx) => {
                    const y = d.startY + (dy * level);
                    ctx.strokeStyle = colors[idx % colors.length];
                    ctx.lineWidth = isSelected ? 1.5 : 1;
                    ctx.beginPath();
                    ctx.moveTo(Math.min(d.startX, d.endX), y);
                    ctx.lineTo(this.overlayCanvas.width, y);
                    ctx.stroke();

                    ctx.fillStyle = colors[idx % colors.length];
                    ctx.font = '10px sans-serif';
                    ctx.fillText(`Fib ${(level * 100).toFixed(1)}%`, Math.min(d.startX, d.endX) + 5, y - 3);
                });
                ctx.restore();
            } else if (d.type === 'measure') {
                ctx.save();
                const minX = Math.min(d.startX, d.endX);
                const maxX = Math.max(d.startX, d.endX);
                const minY = Math.min(d.startY, d.endY);
                const maxY = Math.max(d.startY, d.endY);

                ctx.fillStyle = 'rgba(56, 189, 248, 0.15)';
                ctx.strokeStyle = d.color || '#38bdf8';
                ctx.lineWidth = isSelected ? 2 : 1.5;
                ctx.strokeRect(minX, minY, maxX - minX, maxY - minY);
                ctx.fillRect(minX, minY, maxX - minX, maxY - minY);

                ctx.fillStyle = '#ffffff';
                ctx.font = 'bold 11px sans-serif';
                ctx.fillText(`Δ Range`, minX + 8, minY + 18);
                ctx.restore();
            }
        }

        // Render TradingView-style price scale countdown badge
        if (this.currentCandle && this.candleSeries) {
            try {
                const y = this.candleSeries.priceToCoordinate(this.currentCandle.close);
                if (y !== null && y !== undefined && y > 15 && y < this.overlayCanvas.height - 25) {
                    const tfSec = this.parseTfSeconds(this.currentTimeframe);
                    const now = Math.floor(Date.now() / 1000);
                    const elapsed = now % tfSec;
                    const remaining = Math.max(0, tfSec - elapsed);
                    const hrs = Math.floor(remaining / 3600);
                    const mins = Math.floor((remaining % 3600) / 60);
                    const secs = remaining % 60;
                    const timeStr = hrs > 0 
                        ? `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
                        : `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

                    ctx.save();
                    ctx.fillStyle = this.isDarkMode ? '#0f172a' : '#ffffff';
                    ctx.strokeStyle = '#f59e0b';
                    ctx.lineWidth = 1;
                    const badgeW = 54;
                    const badgeH = 16;
                    const badgeX = this.overlayCanvas.width - badgeW - 3;
                    const badgeY = y + 14;

                    ctx.beginPath();
                    if (ctx.roundRect) {
                        ctx.roundRect(badgeX, badgeY, badgeW, badgeH, 4);
                    } else {
                        ctx.rect(badgeX, badgeY, badgeW, badgeH);
                    }
                    ctx.fill();
                    ctx.stroke();

                    ctx.fillStyle = '#f59e0b';
                    ctx.font = 'bold 10px monospace';
                    ctx.textAlign = 'center';
                    ctx.fillText(timeStr, badgeX + (badgeW / 2), badgeY + 12);
                    ctx.restore();
                }
            } catch (err) {}
        }
    }

    // ==========================================
    // ALERTS & PRICE SCALE INTEGRATION
    // ==========================================
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
                        lineWidth: 1.5,
                        lineStyle: LightweightCharts.LineStyle.Dashed,
                        axisLabelVisible: true,
                        title: `🔔 ALERT #${a.id} (${(a.condition_type || '').replace('_', ' ')})`,
                    });
                    this.alertPriceLines.push(line);
                } catch(e) {}
            }
        }
    }
}
