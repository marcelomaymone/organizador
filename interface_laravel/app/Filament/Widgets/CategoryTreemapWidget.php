<?php

namespace App\Filament\Widgets;

use App\Models\ArquivoProcessamento;
use Filament\Widgets\Widget;

class CategoryTreemapWidget extends Widget
{
    protected static string $view = 'filament.widgets.category-treemap-widget';

    protected static ?int $sort = 2;

    // Ocupa a largura inteira do dashboard
    protected int | string | array $columnSpan = 'full';

    protected function getViewData(): array
    {
        $categoriesData = ArquivoProcessamento::query()
            ->selectRaw('categoria_proposta, SUM(tamanho_bytes) as total_bytes, COUNT(*) as file_count')
            ->whereNotNull('categoria_proposta')
            ->where('categoria_proposta', '!=', '')
            ->groupBy('categoria_proposta')
            ->get()
            ->map(function ($row) {
                // Formata o volume em Megabytes para facilitar a visualização no Treemap se preferir,
                // mas usaremos os bytes brutos e formataremos no tooltip.
                return [
                    'x' => $row->categoria_proposta,
                    'bytes' => (int) $row->total_bytes,
                    'count' => (int) $row->file_count,
                ];
            })
            ->toArray();

        return [
            'chartData' => json_encode($categoriesData),
        ];
    }
}
