<x-filament-panels::page>
    <x-filament-panels::form wire:submit="save">
        {{ $this->form }}

        <div class="mt-6 flex flex-wrap gap-4">
            <x-filament::button type="submit" size="lg">
                Salvar Configurações
            </x-filament::button>

            <x-filament::button wire:click="iniciarVarredura" color="warning" size="lg" icon="heroicon-o-magnifying-glass-circle">
                Iniciar Varredura (Scan)
            </x-filament::button>
        </div>
    </x-filament-panels::form>

    <!-- Modal Customizado do Seletor de Pastas (Folder Picker) -->
    @if($seletorAberto)
        <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-950/80 backdrop-blur-sm">
            <div class="relative w-full max-w-2xl bg-gray-900 border border-cyan-500/30 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
                
                <!-- Cabeçalho do Modal -->
                <div class="px-6 py-4 bg-gray-950 border-b border-gray-800 flex justify-between items-center">
                    <h3 class="text-lg font-bold text-white flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-6 w-6 text-cyan-400">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M15 13.5H9m4.06-7.19-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z" />
                        </svg>
                        Seletor de Pasta Local
                    </h3>
                    <button type="button" wire:click="$set('seletorAberto', false)" class="text-gray-400 hover:text-white transition">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-6 w-6">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <!-- Corpo do Modal / Navegador -->
                <div class="p-6 overflow-y-auto flex-1 space-y-4">
                    <!-- Caminho Atual -->
                    <div class="bg-gray-950 px-4 py-2 rounded-lg border border-gray-800 flex items-center gap-2 text-sm text-cyan-400 overflow-x-auto whitespace-nowrap">
                        <span class="text-gray-500 font-semibold font-mono">CAMINHO:</span>
                        <span class="font-mono">{{ $seletorCaminhoAtual }}</span>
                    </div>

                    <!-- Botão de Voltar / Subir Diretório -->
                    <div class="flex justify-between items-center gap-4">
                        <x-filament::button type="button" wire:click="subirDiretorio" color="gray" icon="heroicon-o-arrow-up-circle">
                            Subir uma Pasta
                        </x-filament::button>
                        
                        <!-- Criar Nova Pasta -->
                        <div class="flex gap-2 max-w-xs">
                            <input type="text" wire:model.defer="novaPastaNome" placeholder="Nova pasta..." 
                                   class="bg-gray-950 border border-gray-800 rounded-lg px-3 py-1.5 text-sm text-white focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none w-full" />
                            <x-filament::button type="button" wire:click="criarNovaPasta" size="sm" color="gray">
                                Criar
                            </x-filament::button>
                        </div>
                    </div>

                    <!-- Lista de Subpastas -->
                    <div class="border border-gray-800 rounded-xl bg-gray-950/50 divide-y divide-gray-800/60 max-h-[40vh] overflow-y-auto">
                        @if(empty($seletorDiretorios))
                            <div class="p-8 text-center text-gray-500 text-sm">
                                Nenhuma subpasta encontrada neste diretório.
                            </div>
                        @else
                            @foreach($seletorDiretorios as $pasta)
                                <div type="button" wire:click="entrarNaPasta('{{ addslashes($pasta) }}')" 
                                     class="flex items-center gap-3 px-4 py-3 hover:bg-cyan-500/10 cursor-pointer transition text-gray-300 hover:text-white">
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-5 w-5 text-cyan-500">
                                        <path d="M19.5 21a3 3 0 0 0 3-3v-4.5a3 3 0 0 0-3-3h-15a3 3 0 0 0-3 3V18a3 3 0 0 0 3 3h15ZM1.5 10.146V6a3 3 0 0 1 3-3h5.379a2.25 2.25 0 0 1 1.59.659l2.122 2.121c.14.141.33.22.53.22H19.5a3 3 0 0 1 3 3v1.146A4.483 4.483 0 0 0 19.5 9h-15a4.483 4.483 0 0 0-3 1.146Z" />
                                    </svg>
                                    <span class="text-sm font-semibold truncate">{{ $pasta }}</span>
                                </div>
                            @endforeach
                        @endif
                    </div>
                </div>

                <!-- Rodapé do Modal -->
                <div class="px-6 py-4 bg-gray-950 border-t border-gray-800 flex justify-end gap-3">
                    <x-filament::button type="button" wire:click="$set('seletorAberto', false)" color="gray">
                        Cancelar
                    </x-filament::button>
                    
                    <x-filament::button type="button" wire:click="confirmarSelecao" color="warning" icon="heroicon-o-check-circle">
                        Selecionar Esta Pasta
                    </x-filament::button>
                </div>

            </div>
        </div>
    @endif
</x-filament-panels::page>
