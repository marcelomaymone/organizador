<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Dispositivo extends Model
{
    protected $table = 'dispositivos';

    protected $fillable = [
        'uuid',
        'nome',
        'ponto_montagem',
        'tipo_sistema_arquivos',
        'capacidade_bytes',
        'espaco_livre_bytes',
        'hardware_id',
    ];

    /**
     * Relacionamento com arquivos em processamento.
     */
    public function arquivos(): HasMany
    {
        return $this->hasMany(ArquivoProcessamento::class, 'dispositivo_id');
    }
}
