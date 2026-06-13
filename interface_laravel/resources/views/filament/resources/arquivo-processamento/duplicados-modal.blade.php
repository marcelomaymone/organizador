<div class="space-y-4 py-2">
    <div class="text-sm text-gray-500 dark:text-gray-400">
        Este arquivo possui <strong>{{ $duplicados->count() }}</strong> duplicata(s) lógica(s) (mesmo hash sha256). Gerencie cada uma individualmente abaixo.
    </div>

    <div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-left text-xs">
            <thead class="bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 uppercase font-semibold">
                <tr>
                    <th class="px-4 py-3">Caminho de Origem</th>
                    <th class="px-4 py-3">Destino Sugerido / Aprovado</th>
                    <th class="px-4 py-3">Status</th>
                    <th class="px-4 py-3 text-right">Ações</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
                @foreach ($duplicados as $dup)
                    <tr class="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                        <td class="px-4 py-3 max-w-xs truncate" title="{{ $dup->caminho_origem }}">
                            {{ $dup->caminho_origem }}
                        </td>
                        <td class="px-4 py-3 max-w-xs">
                            <div id="dest-view-{{ $dup->uuid }}" class="truncate" title="{{ $dup->caminho_aprovado ?? $dup->caminho_proposto }}">
                                {{ $dup->caminho_aprovado ?? $dup->caminho_proposto ?? 'Não definido' }}
                            </div>
                            <!-- Form de reclassificação oculto -->
                            <div id="dest-edit-{{ $dup->uuid }}" class="hidden space-y-1 mt-1">
                                <input type="text" id="input-dest-{{ $dup->uuid }}" 
                                       value="{{ $dup->caminho_aprovado ?? $dup->caminho_proposto }}" 
                                       class="w-full text-xs rounded border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-indigo-500 focus:border-indigo-500">
                                <div class="flex space-x-1">
                                    <button onclick="salvarReclassificacao('{{ $dup->uuid }}')" class="px-2 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700 font-semibold">Salvar</button>
                                    <button onclick="cancelarEdicao('{{ $dup->uuid }}')" class="px-2 py-1 bg-gray-300 dark:bg-gray-600 text-gray-800 dark:text-gray-200 rounded hover:bg-gray-400 dark:hover:bg-gray-500">Cancelar</button>
                                </div>
                            </div>
                        </td>
                        <td class="px-4 py-3">
                            @php
                                $statusColor = match($dup->status) {
                                    'pendente_extracao' => 'text-amber-600 bg-amber-50 dark:bg-amber-950 dark:text-amber-400',
                                    'pendente_inferencia' => 'text-blue-600 bg-blue-50 dark:bg-blue-950 dark:text-blue-400',
                                    'aguardando_auditoria' => 'text-purple-600 bg-purple-50 dark:bg-purple-950 dark:text-purple-400',
                                    'aprovado_para_movimentacao' => 'text-emerald-600 bg-emerald-50 dark:bg-emerald-950 dark:text-emerald-400',
                                    'quarentena' => 'text-red-600 bg-red-50 dark:bg-red-950 dark:text-red-400',
                                    'concluido' => 'text-green-600 bg-green-50 dark:bg-green-950 dark:text-green-400',
                                    'descarte_pendente' => 'text-gray-600 bg-gray-100 dark:bg-gray-800 dark:text-gray-400',
                                    default => 'text-red-600 bg-red-50 dark:bg-red-950 dark:text-red-400'
                                };
                                $statusLabel = match($dup->status) {
                                    'pendente_extracao' => 'Pendente Extração',
                                    'pendente_inferencia' => 'Pendente Inferência',
                                    'aguardando_auditoria' => 'Aguardando Revisão',
                                    'aprovado_para_movimentacao' => 'Aprovado',
                                    'quarentena' => 'Quarentena',
                                    'concluido' => 'Concluído',
                                    'descarte_pendente' => 'Exclusão Física',
                                    default => ucfirst($dup->status)
                                };
                            @endphp
                            <span class="px-2 py-1 rounded-full text-[10px] font-medium {{ $statusColor }}">
                                {{ $statusLabel }}
                            </span>
                        </td>
                        <td class="px-4 py-3 text-right space-x-1 whitespace-nowrap">
                            @if ($dup->status !== 'aprovado_para_movimentacao' && $dup->status !== 'concluido' && $dup->status !== 'descarte_pendente')
                                <button onclick="aprovarDuplicado('{{ $dup->uuid }}')" 
                                        class="px-2.5 py-1.5 bg-emerald-600 text-white rounded hover:bg-emerald-700 transition font-medium" 
                                        title="Aprovar com o destino atual sugerido">
                                    Aprovar
                                </button>
                                <button onclick="editarDestino('{{ $dup->uuid }}')" 
                                        class="px-2.5 py-1.5 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition font-medium"
                                        title="Alterar destino do arquivo">
                                    Reclassificar
                                </button>
                            @endif

                            @if ($dup->status !== 'descarte_pendente' && $dup->status !== 'concluido')
                                <button onclick="descartarDuplicado('{{ $dup->uuid }}')" 
                                        class="px-2.5 py-1.5 bg-red-600 text-white rounded hover:bg-red-700 transition font-medium"
                                        title="Marcar para exclusão física pelo motor Python">
                                    Excluir Fisicamente
                                </button>
                            @endif
                        </td>
                    </tr>
                @endforeach
            </tbody>
        </table>
    </div>
</div>

<script>
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    }

    function aprovarDuplicado(uuid) {
        if (!confirm('Deseja aprovar esta duplicata para movimentação?')) return;
        
        fetch(`/admin/duplicados/${uuid}/aprovar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                alert('Erro ao aprovar duplicado.');
            }
        })
        .catch(err => {
            console.error(err);
            alert('Falha na comunicação com o servidor.');
        });
    }

    function descartarDuplicado(uuid) {
        if (!confirm('Deseja marcar esta duplicata para exclusão física definitiva pelo motor Python?')) return;

        fetch(`/admin/duplicados/${uuid}/descartar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                alert('Erro ao marcar descarte.');
            }
        })
        .catch(err => {
            console.error(err);
            alert('Falha na comunicação com o servidor.');
        });
    }

    function editarDestino(uuid) {
        document.getElementById(`dest-view-${uuid}`).classList.add('hidden');
        document.getElementById(`dest-edit-${uuid}`).classList.remove('hidden');
    }

    function cancelarEdicao(uuid) {
        document.getElementById(`dest-view-${uuid}`).classList.remove('hidden');
        document.getElementById(`dest-edit-${uuid}`).classList.add('hidden');
    }

    function salvarReclassificacao(uuid) {
        const caminhoDestino = document.getElementById(`input-dest-${uuid}`).value;
        if (!caminhoDestino || caminhoDestino.trim() === '') {
            alert('Por favor, informe o caminho de destino.');
            return;
        }

        fetch(`/admin/duplicados/${uuid}/reclassificar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': getCsrfToken()
            },
            body: JSON.stringify({ caminho_destino: caminhoDestino })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                alert('Erro ao reclassificar duplicado.');
            }
        })
        .catch(err => {
            console.error(err);
            alert('Falha na comunicação com o servidor.');
        });
    }
</script>
