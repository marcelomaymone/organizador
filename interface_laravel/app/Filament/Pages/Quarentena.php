<?php

namespace App\Filament\Pages;

use App\Models\ArquivoProcessamento;
use Filament\Pages\Page;
use Filament\Tables\Contracts\HasTable;
use Filament\Tables\Concerns\InteractsWithTable;
use Filament\Tables\Table;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Actions\Action;
use Filament\Notifications\Notification;

class Quarentena extends Page implements HasTable
{
    use InteractsWithTable;

    protected static ?string $navigationIcon = 'heroicon-o-shield-exclamation';

    protected static string $view = 'filament.pages.quarentena';

    protected static ?string $navigationLabel = 'Gestão de Quarentena';
    protected static ?string $title = 'Gestão de Quarentena';
    protected static ?string $slug = 'quarentena';

    public function table(Table $table): Table
    {
        return $table
            ->query(
                ArquivoProcessamento::query()->where('status', 'quarentena')
            )
            ->columns([
                TextColumn::make('nome_original')
                    ->label('Nome do Arquivo')
                    ->searchable()
                    ->sortable()
                    ->weight('bold')
                    ->limit(30),

                TextColumn::make('tamanho_bytes')
                    ->label('Tamanho')
                    ->sortable()
                    ->formatStateUsing(function ($state) {
                        if ($state >= 1073741824) {
                            return number_format($state / 1073741824, 2) . ' GB';
                        }
                        if ($state >= 1048576) {
                            return number_format($state / 1048576, 2) . ' MB';
                        }
                        return number_format($state / 1024, 2) . ' KB';
                    }),

                TextColumn::make('caminho_origem')
                    ->label('Caminho de Origem')
                    ->searchable()
                    ->limit(45),

                TextColumn::make('motivo_falha')
                    ->label('Motivo da Falha')
                    ->searchable()
                    ->wrap()
                    ->color('danger')
                    ->weight('medium'),

                TextColumn::make('mensagem_erro')
                    ->label('Detalhe Técnico')
                    ->limit(40)
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->actions([
                Action::make('reprocessar')
                    ->label('Reprocessar')
                    ->icon('heroicon-o-arrow-path')
                    ->color('warning')
                    ->action(function (ArquivoProcessamento $record) {
                        $record->update([
                            'status' => 'pendente_extracao',
                            'motivo_falha' => null,
                            'mensagem_erro' => null,
                        ]);

                        Notification::make()
                            ->title('Arquivo Reinventariado')
                            ->body("O status de {$record->nome_original} foi redefinido para pendente de extração.")
                            ->success()
                            ->send();
                    }),

                Action::make('descartar')
                    ->label('Descartar')
                    ->icon('heroicon-o-trash')
                    ->color('danger')
                    ->requiresConfirmation()
                    ->modalHeading('Confirmar Descarte de Arquivo')
                    ->modalDescription('Você tem certeza que deseja descartar este arquivo? Ele será marcado para exclusão física definitiva pelo motor Python.')
                    ->modalSubmitActionLabel('Sim, Descartar')
                    ->action(function (ArquivoProcessamento $record) {
                        $record->update([
                            'status' => 'descarte_pendente',
                        ]);

                        Notification::make()
                            ->title('Arquivo Mapeado para Descarte')
                            ->body("O arquivo {$record->nome_original} foi marcado para exclusão física definitiva.")
                            ->success()
                            ->send();
                    }),
            ])
            ->emptyStateHeading('Sem arquivos na quarentena')
            ->emptyStateDescription('Todos os seus arquivos foram processados ou classificados corretamente!')
            ->emptyStateIcon('heroicon-o-shield-check');
    }
}
