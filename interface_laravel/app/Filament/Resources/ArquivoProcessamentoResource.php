<?php

namespace App\Filament\Resources;

use App\Filament\Resources\ArquivoProcessamentoResource\Pages;
use App\Models\ArquivoProcessamento;
use App\Models\Dispositivo;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Filament\Notifications\Notification;
use Illuminate\Database\Eloquent\Builder;

class ArquivoProcessamentoResource extends Resource
{
    protected static ?string $model = ArquivoProcessamento::class;

    protected static ?string $navigationIcon = 'heroicon-o-document-magnifying-glass';
    
    protected static ?string $navigationLabel = 'Auditoria de Arquivos';
    protected static ?string $modelLabel = 'Arquivo';
    protected static ?string $pluralModelLabel = 'Auditoria de Arquivos';
    protected static ?string $slug = 'auditoria';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make('Informações do Arquivo')
                    ->schema([
                        Forms\Components\TextInput::make('nome_original')
                            ->label('Nome do Arquivo')
                            ->disabled(),
                        Forms\Components\TextInput::make('caminho_origem')
                            ->label('Caminho de Origem')
                            ->disabled()
                            ->columnSpanFull(),
                        Forms\Components\Textarea::make('texto_extraido')
                            ->label('Trecho de Texto Extraído')
                            ->disabled()
                            ->columnSpanFull()
                            ->rows(5),
                    ])->columns(2),
                
                Forms\Components\Section::make('Classificação Semântica (IA)')
                    ->schema([
                        Forms\Components\TextInput::make('categoria_proposta')
                            ->label('Categoria Recomendada')
                            ->disabled(),
                        Forms\Components\TextInput::make('status')
                            ->label('Status Atual')
                            ->disabled(),
                        Forms\Components\Textarea::make('justificativa_classificacao')
                            ->label('Justificativa (Chain of Thought)')
                            ->disabled()
                            ->columnSpanFull(),
                    ])->columns(2),

                Forms\Components\Section::make('Auditoria Humana')
                    ->schema([
                        Forms\Components\TextInput::make('caminho_proposto')
                            ->label('Destino Sugerido')
                            ->disabled()
                            ->columnSpanFull(),
                        Forms\Components\TextInput::make('caminho_aprovado')
                            ->label('Destino Aprovado')
                            ->placeholder('Será preenchido na aprovação ou reclassificação')
                            ->columnSpanFull(),
                    ]),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('nome_original')
                    ->label('Nome')
                    ->searchable()
                    ->sortable()
                    ->weight('bold')
                    ->limit(30),

                Tables\Columns\TextColumn::make('tamanho_bytes')
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

                Tables\Columns\TextColumn::make('dispositivo.nome')
                    ->label('Dispositivo')
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),

                Tables\Columns\TextColumn::make('status')
                    ->label('Status')
                    ->sortable()
                    ->badge()
                    ->color(fn (string $state): string => match ($state) {
                        'pendente_extracao' => 'warning',
                        'pendente_inferencia' => 'info',
                        'aguardando_auditoria' => 'primary',
                        'aprovado_para_movimentacao' => 'success',
                        'concluido' => 'success',
                        'quarentena', 'erro' => 'danger',
                        'descarte_pendente' => 'gray',
                        default => 'gray',
                    })
                    ->formatStateUsing(fn (string $state): string => match ($state) {
                        'pendente_extracao' => 'Pendente Extração',
                        'pendente_inferencia' => 'Pendente Inferência',
                        'aguardando_auditoria' => 'Aguardando Revisão',
                        'aprovado_para_movimentacao' => 'Aprovado',
                        'concluido' => 'Concluído',
                        'quarentena' => 'Quarentena',
                        'erro' => 'Erro',
                        'descarte_pendente' => 'Exclusão Física',
                        default => $state,
                    }),

                Tables\Columns\TextColumn::make('categoria_proposta')
                    ->label('Categoria')
                    ->sortable()
                    ->searchable()
                    ->badge()
                    ->color('gray'),

                Tables\Columns\TextColumn::make('caminho_proposto')
                    ->label('Destino Sugerido')
                    ->limit(35)
                    ->toggleable(isToggledHiddenByDefault: false),

                Tables\Columns\TextColumn::make('duplicados_count')
                    ->label('Duplicatas')
                    ->state(fn ($record) => $record->obterDuplicados()->count())
                    ->badge()
                    ->color(fn ($state) => $state > 0 ? 'warning' : 'gray'),
            ])
            ->defaultSort('data_registro', 'desc')
            ->filters([
                Tables\Filters\SelectFilter::make('status')
                    ->options([
                        'pendente_extracao' => 'Pendente Extração',
                        'pendente_inferencia' => 'Pendente Inferência',
                        'aguardando_auditoria' => 'Aguardando Revisão',
                        'aprovado_para_movimentacao' => 'Aprovado',
                        'concluido' => 'Concluído',
                        'erro' => 'Erro',
                    ]),
                Tables\Filters\SelectFilter::make('dispositivo_id')
                    ->label('Dispositivo')
                    ->relationship('dispositivo', 'nome'),
            ])
            ->actions([
                Tables\Actions\Action::make('aprovar')
                    ->label('Aprovar')
                    ->icon('heroicon-o-check')
                    ->color('success')
                    ->visible(fn ($record) => $record->status === 'aguardando_auditoria')
                    ->action(function ($record) {
                        $record->update([
                            'status' => 'aprovado_para_movimentacao',
                            'caminho_aprovado' => $record->caminho_proposto,
                            'data_processamento' => now(),
                        ]);

                        Notification::make()
                            ->title('Arquivo Aprovado')
                            ->body("O destino sugerido para {$record->nome_original} foi aprovado com sucesso.")
                            ->success()
                            ->send();
                    }),

                Tables\Actions\Action::make('reclassificar')
                    ->label('Reclassificar')
                    ->icon('heroicon-o-pencil-square')
                    ->color('indigo')
                    ->visible(fn ($record) => in_array($record->status, ['aguardando_auditoria', 'aprovado_para_movimentacao']))
                    ->form([
                        Forms\Components\TextInput::make('categoria_proposta')
                            ->label('Categoria')
                            ->default(fn ($record) => $record->categoria_proposta)
                            ->required(),
                        Forms\Components\TextInput::make('caminho_destino')
                            ->label('Caminho de Destino')
                            ->default(fn ($record) => $record->caminho_aprovado ?? $record->caminho_proposto)
                            ->required()
                            ->columnSpanFull(),
                    ])
                    ->action(function ($record, array $data) {
                        $record->update([
                            'status' => 'aprovado_para_movimentacao',
                            'categoria_proposta' => $data['categoria_proposta'],
                            'caminho_proposto' => $data['caminho_destino'],
                            'caminho_aprovado' => $data['caminho_destino'],
                            'data_processamento' => now(),
                        ]);

                        Notification::make()
                            ->title('Arquivo Reclassificado e Aprovado')
                            ->success()
                            ->send();
                    }),

                Tables\Actions\Action::make('gerenciar_duplicados')
                    ->label('Duplicatas')
                    ->icon('heroicon-o-document-duplicate')
                    ->color('warning')
                    ->modalHeading('Gerenciar Duplicatas Lógicas')
                    ->modalSubmitButton(false)
                    ->modalContent(fn ($record) => view('filament.resources.arquivo-processamento.duplicados-modal', [
                        'record' => $record,
                        'duplicados' => $record->obterDuplicados(),
                    ]))
                    ->visible(fn ($record) => $record->obterDuplicados()->count() > 0),

                Tables\Actions\ViewAction::make()
                    ->label('Detalhes'),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\BulkAction::make('aprovar_lote')
                        ->label('Aprovar Lote')
                        ->icon('heroicon-o-check-circle')
                        ->color('success')
                        ->action(function (\Illuminate\Support\Collection $records) {
                            $count = 0;
                            foreach ($records as $record) {
                                if ($record->status === 'aguardando_auditoria') {
                                    $record->update([
                                        'status' => 'aprovado_para_movimentacao',
                                        'caminho_aprovado' => $record->caminho_proposto,
                                        'data_processamento' => now(),
                                    ]);
                                    $count++;
                                }
                            }

                            Notification::make()
                                ->title("{$count} arquivos aprovados em lote.")
                                ->success()
                                ->send();
                        })
                        ->deselectRecordsAfterCompletion(),
                ]),
            ]);
    }

    public static function getEloquentQuery(): Builder
    {
        // Apenas arquivos originais na listagem principal
        // Exclui arquivos em quarentena (que possuem aba dedicada)
        return parent::getEloquentQuery()
            ->original()
            ->where('status', '!=', 'quarentena');
    }

    public static function getRelations(): array
    {
        return [];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListArquivoProcessamentos::route('/'),
        ];
    }
}
