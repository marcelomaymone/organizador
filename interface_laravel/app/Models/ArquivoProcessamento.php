<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Builder;

class ArquivoProcessamento extends Model
{
    protected $table = 'arquivos_processamento';
    protected $primaryKey = 'uuid';
    public $incrementing = false;
    protected $keyType = 'string';

    protected $fillable = [
        'uuid',
        'dispositivo_id',
        'caminho_origem',
        'nome_original',
        'tamanho_bytes',
        'hash_xxhash',
        'status',
        'caminho_proposto',
        'caminho_aprovado',
        'categoria_proposta',
        'justificativa_classificacao',
        'eh_duplicado',
        'motivo_falha',
        'mensagem_erro',
        'texto_extraido',
        'data_criacao_sistema',
        'data_modificacao_sistema',
        'data_registro',
        'data_processamento',
    ];

    protected $casts = [
        'eh_duplicado' => 'boolean',
        'data_registro' => 'datetime',
        'data_processamento' => 'datetime',
    ];

    /**
     * Relacionamento com o dispositivo.
     */
    public function dispositivo(): BelongsTo
    {
        return $this->belongsTo(Dispositivo::class, 'dispositivo_id');
    }

    /**
     * Escopo para carregar apenas arquivos originais de referência.
     */
    public function scopeOriginal(Builder $query): Builder
    {
        return $query->where('eh_duplicado', false);
    }

    /**
     * Escopo para carregar apenas arquivos duplicados.
     */
    public function scopeDuplicado(Builder $query): Builder
    {
        return $query->where('eh_duplicado', true);
    }

    /**
     * Obtém o arquivo original correspondente (mesmo hash, mas eh_duplicado = 0).
     */
    public function obterOriginal()
    {
        if (!$this->eh_duplicado) {
            return $this;
        }

        return self::where('hash_xxhash', $this->hash_xxhash)
            ->where('eh_duplicado', false)
            ->first();
    }

    /**
     * Obtém todas as duplicatas deste arquivo (mesmo hash, mas eh_duplicado = 1).
     */
    public function obterDuplicados()
    {
        // Se este arquivo for duplicado, buscamos os outros duplicados do mesmo hash (excluindo ele mesmo)
        // Se for o original, buscamos todos os duplicados dele.
        $query = self::where('hash_xxhash', $this->hash_xxhash)
            ->where('eh_duplicado', true);

        if ($this->eh_duplicado) {
            $query->where('uuid', '!=', $this->uuid);
        }

        return $query->get();
    }
}
