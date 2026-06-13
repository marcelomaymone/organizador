<x-filament-widgets::widget>
    <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm"
         x-data="treemapWidget({
             rawRecords: {{ $chartData }}
         })"
         x-init="initWidget()">
        
        <!-- Cabeçalho com Seletor -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
                <h3 class="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                    <svg class="h-5 w-5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    Distribuição por Categoria (P.A.R.A. / PCD)
                </h3>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Densidade e distribuição semântica do acervo analisado
                </p>
            </div>

            <!-- Botões de Alternância de Modo -->
            <div class="flex bg-gray-100 dark:bg-gray-800 p-1 rounded-lg self-start sm:self-center">
                <button type="button" 
                        @click="setMode('bytes')" 
                        :class="mode === 'bytes' ? 'bg-white dark:bg-gray-700 shadow-sm text-indigo-600 dark:text-indigo-400' : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'"
                        class="px-3 py-1.5 rounded-md text-xs font-semibold transition-all">
                    Volume em Bytes
                </button>
                <button type="button" 
                        @click="setMode('count')" 
                        :class="mode === 'count' ? 'bg-white dark:bg-gray-700 shadow-sm text-indigo-600 dark:text-indigo-400' : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'"
                        class="px-3 py-1.5 rounded-md text-xs font-semibold transition-all">
                    Quantidade de Arquivos
                </button>
            </div>
        </div>

        <!-- Container do Gráfico -->
        <div class="w-full min-h-[350px] relative">
            <div x-ref="chartContainer" class="w-full h-full"></div>
            
            <!-- Estado Vazio -->
            <div x-show="rawRecords.length === 0" 
                 class="absolute inset-0 flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-800/10 rounded-lg p-6 text-center">
                <svg class="h-12 w-12 text-gray-400 dark:text-gray-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                <h4 class="text-sm font-bold text-gray-700 dark:text-gray-300">Sem dados para exibir</h4>
                <p class="text-xs text-gray-400 mt-1 max-w-[250px]">O motor de inferência precisa processar e classificar os arquivos primeiro.</p>
            </div>
        </div>

    </div>

    <!-- Script Inline Seguro e Declarativo via Alpine.js -->
    @once
        <script src="https://cdn.jsdelivr.net/npm/apexcharts" defer></script>
    @endonce

    <script>
        document.addEventListener('alpine:init', () => {
            Alpine.data('treemapWidget', (config) => ({
                rawRecords: config.rawRecords,
                mode: 'bytes', // 'bytes' | 'count'
                chart: null,

                initWidget() {
                    if (this.rawRecords.length === 0) return;
                    
                    // Aguarda a biblioteca ApexCharts carregar globalmente
                    const checkChartLoaded = setInterval(() => {
                        if (window.ApexCharts) {
                            clearInterval(checkChartLoaded);
                            this.renderChart();
                        }
                    }, 100);
                },

                renderChart() {
                    const options = {
                        series: [{
                            data: this.getChartSeries()
                        }],
                        legend: {
                            show: false
                        },
                        chart: {
                            height: 350,
                            type: 'treemap',
                            toolbar: {
                                show: false
                            },
                            animations: {
                                enabled: true,
                                easing: 'easeinout',
                                speed: 300
                            }
                        },
                        colors: [
                            '#4F46E5', '#06B6D4', '#10B981', '#F59E0B', 
                            '#EF4444', '#8B5CF6', '#EC4899', '#6B7280'
                        ],
                        plotOptions: {
                            treemap: {
                                distributed: true,
                                enableShades: false
                            }
                        },
                        tooltip: {
                            theme: document.documentElement.classList.contains('dark') ? 'dark' : 'light',
                            y: {
                                formatter: (value) => {
                                    if (this.mode === 'bytes') {
                                        return this.formatBytes(value);
                                    }
                                    return value + ' arquivo(s)';
                                }
                            }
                        }
                    };

                    this.chart = new ApexCharts(this.$refs.chartContainer, options);
                    this.chart.render();
                },

                getChartSeries() {
                    return this.rawRecords.map(item => ({
                        x: item.x,
                        y: this.mode === 'bytes' ? item.bytes : item.count
                    }));
                },

                setMode(newMode) {
                    if (this.mode === newMode) return;
                    this.mode = newMode;
                    if (this.chart) {
                        this.chart.updateSeries([{
                            data: this.getChartSeries()
                        }]);
                    }
                },

                formatBytes(bytes) {
                    if (bytes === 0) return '0 Bytes';
                    const k = 1024;
                    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
                    const i = Math.floor(Math.log(bytes) / Math.log(k));
                    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
                }
            }));
        });
    </script>
</x-filament-widgets::widget>
