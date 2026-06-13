<x-filament-widgets::widget>
    <div wire:poll.5s class="filament-etl-progress-widget bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm">
        
        <!-- Cabeçalho -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
            <div>
                <h3 class="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                    <span class="relative flex h-3 w-3">
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-3 w-3 bg-indigo-500"></span>
                    </span>
                    Status do Pipeline ETL (Tempo Real)
                </h3>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Processado: <strong>{{ $processados }}</strong> de <strong>{{ $total }}</strong> arquivos analisados
                </p>
            </div>
            
            <div class="text-right">
                <span class="text-2xl font-extrabold text-indigo-600 dark:text-indigo-400">
                    {{ $porcentagem }}%
                </span>
                <span class="text-xs text-gray-400 block">Concluído</span>
            </div>
        </div>

        <!-- Barra de Progresso Principal -->
        <div class="w-full bg-gray-100 dark:bg-gray-800 h-3.5 rounded-full overflow-hidden mb-6 flex">
            <!-- Barra de Progresso Aprovados/Concluídos -->
            @php
                $concluidosCount = $counts['concluido'] + $counts['aprovado_para_movimentacao'];
                $pctConcluido = $total > 0 ? ($concluidosCount / $total) * 100 : 0;
                
                $revisaoCount = $counts['aguardando_auditoria'];
                $pctRevisao = $total > 0 ? ($revisaoCount / $total) * 100 : 0;
                
                $problemasCount = $counts['quarentena'] + $counts['erro'] + $counts['descarte_pendente'];
                $pctProblemas = $total > 0 ? ($problemasCount / $total) * 100 : 0;
            @endphp
            <div style="width: {{ $pctConcluido }}%" class="bg-emerald-500 transition-all duration-500" title="Aprovado / Movido: {{ $concluidosCount }}"></div>
            <div style="width: {{ $pctRevisao }}%" class="bg-indigo-500 transition-all duration-500" title="Aguardando Revisão: {{ $revisaoCount }}"></div>
            <div style="width: {{ $pctProblemas }}%" class="bg-red-500 transition-all duration-500" title="Incidentes / Descarte: {{ $problemasCount }}"></div>
        </div>

        <!-- Cards de Status -->
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
            
            <!-- Pendente Extração -->
            <div class="bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg border border-gray-100 dark:border-gray-800 text-center">
                <span class="block text-xs font-semibold text-amber-600 dark:text-amber-400 mb-1">Extração</span>
                <span class="text-lg font-bold text-gray-900 dark:text-gray-100">{{ $counts['pendente_extracao'] }}</span>
                <span class="block text-[10px] text-gray-400 mt-0.5">Pendentes</span>
            </div>

            <!-- Pendente Inferência -->
            <div class="bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg border border-gray-100 dark:border-gray-800 text-center">
                <span class="block text-xs font-semibold text-blue-600 dark:text-blue-400 mb-1">Inferência</span>
                <span class="text-lg font-bold text-gray-900 dark:text-gray-100">{{ $counts['pendente_inferencia'] }}</span>
                <span class="block text-[10px] text-gray-400 mt-0.5">Pendentes</span>
            </div>

            <!-- Aguardando Auditoria -->
            <div class="bg-indigo-50/50 dark:bg-indigo-950/20 p-3 rounded-lg border border-indigo-100 dark:border-indigo-900/40 text-center">
                <span class="block text-xs font-semibold text-indigo-600 dark:text-indigo-400 mb-1">Auditoria</span>
                <span class="text-lg font-bold text-gray-900 dark:text-gray-100">{{ $counts['aguardando_auditoria'] }}</span>
                <span class="block text-[10px] text-gray-400 mt-0.5">Aguardando</span>
            </div>

            <!-- Aprovado para Movimentação -->
            <div class="bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg border border-gray-100 dark:border-gray-800 text-center">
                <span class="block text-xs font-semibold text-emerald-600 dark:text-emerald-400 mb-1">Aprovados</span>
                <span class="text-lg font-bold text-gray-900 dark:text-gray-100">{{ $counts['aprovado_para_movimentacao'] }}</span>
                <span class="block text-[10px] text-gray-400 mt-0.5">Aguardando Carga</span>
            </div>

            <!-- Quarentena -->
            <div class="bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg border border-gray-100 dark:border-gray-800 text-center">
                <span class="block text-xs font-semibold text-red-600 dark:text-red-400 mb-1">Quarentena</span>
                <span class="text-lg font-bold text-gray-900 dark:text-gray-100">{{ $counts['quarentena'] }}</span>
                <span class="block text-[10px] text-gray-400 mt-0.5">Bloqueados</span>
            </div>

            <!-- Erro -->
            <div class="bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg border border-gray-100 dark:border-gray-800 text-center">
                <span class="block text-xs font-semibold text-red-500 dark:text-red-400 mb-1">Erros</span>
                <span class="text-lg font-bold text-gray-900 dark:text-gray-100">{{ $counts['erro'] }}</span>
                <span class="block text-[10px] text-gray-400 mt-0.5">Falhas</span>
            </div>

            <!-- Descarte Pendente -->
            <div class="bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg border border-gray-100 dark:border-gray-800 text-center">
                <span class="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">Descarte</span>
                <span class="text-lg font-bold text-gray-900 dark:text-gray-100">{{ $counts['descarte_pendente'] }}</span>
                <span class="block text-[10px] text-gray-400 mt-0.5">Para Apagar</span>
            </div>

            <!-- Concluído -->
            <div class="bg-emerald-50/30 dark:bg-emerald-950/10 p-3 rounded-lg border border-emerald-100/50 dark:border-emerald-900/20 text-center">
                <span class="block text-xs font-semibold text-green-600 dark:text-green-400 mb-1">Concluído</span>
                <span class="text-lg font-bold text-gray-900 dark:text-gray-100">{{ $counts['concluido'] }}</span>
                <span class="block text-[10px] text-gray-400 mt-0.5">Finalizados</span>
            </div>

        </div>

    </div>
</x-filament-widgets::widget>
