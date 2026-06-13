<?php

namespace App\Filament\Resources\ArquivoProcessamentoResource\Pages;

use App\Filament\Resources\ArquivoProcessamentoResource;
use Filament\Actions;
use Filament\Resources\Pages\EditRecord;

class EditArquivoProcessamento extends EditRecord
{
    protected static string $resource = ArquivoProcessamentoResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\DeleteAction::make(),
        ];
    }
}
