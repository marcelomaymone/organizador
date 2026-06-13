<?php

namespace App\Filament\Widgets;

use App\Models\ArquivoProcessamento;
use Filament\Widgets\Widget;

class EtlProgressWidget extends Widget
{
    protected static string $view = 'filament.widgets.etl-progress-widget';

    protected static ?int $sort = 1;

    // Ocupa a largura inteira do dashboard
    protected int | string | array $columnSpan = 'full';

    protected function getViewData(): array
    {
        $statusCounts = ArquivoProcessamento::query()
            ->selectRaw('status, count(*) as count')
            ->groupBy('status')
            ->pluck('count', 'status')
            ->toArray();

        $counts = [
            'pendente_extracao' => $statusCounts['pendente_extracao'] ?? 0,
            'pendente_inferencia' => $statusCounts['pendente_inferencia'] ?? 0,
            'aguardando_auditoria' => $statusCounts['aguardando_auditoria'] ?? 0,
            'aprovado_para_movimentacao' => $statusCounts['aprovado_para_movimentacao'] ?? 0,
            'quarentena' => $statusCounts['quarentena'] ?? 0,
            'concluido' => $statusCounts['concluido'] ?? 0,
            'erro' => $statusCounts['erro'] ?? 0,
            'descarte_pendente' => $statusCounts['descarte_pendente'] ?? 0,
        ];

        $total = array_sum($counts);
        
        // Consideramos processados os arquivos que já saíram da fila de ML
        // (ou seja: aguardando revisão, aprovados, concluídos, em quarentena ou descarte)
        $processados = $counts['aguardando_auditoria'] 
            + $counts['aprovado_para_movimentacao'] 
            + $counts['quarentena'] 
            + $counts['concluido'] 
            + $counts['erro'] 
            + $counts['descarte_pendente'];
        
        $porcentagem = $total > 0 ? round(($processados / $total) * 100, 1) : 0;

        return [
            'counts' => $counts,
            'total' => $total,
            'processados' => $processados,
            'porcentagem' => $porcentagem,
        ];
    }
}
