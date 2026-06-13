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
     * O método booted é registrado para vincular os listeners de ciclo de vida do Eloquent.
     * Decisão de Design: Centralizar a propagação lógica de decisões de governança humana
     * (aprovação, reclassificação ou descarte) do arquivo original para todos os seus duplicados
     * de forma automática diretamente no modelo de dados. Isso preserva o encapsulamento e evita
     * espalhar lógica redundante nos resources do Filament e controllers AJAX.
     */
    protected static function booted(): void
    {
        static::updated(function (self $arquivo) {
            // Regra de Negócio: A propagação só deve ocorrer se a alteração foi feita no arquivo original
            if (!$arquivo->eh_duplicado) {
                // Para evitar loops infinitos de atualização e minimizar queries redundantes no SQLite,
                // apenas propagamos se um dos campos de auditoria humana ou status foi de fato modificado.
                if ($arquivo->wasChanged(['status', 'caminho_aprovado', 'caminho_proposto', 'categoria_proposta', 'justificativa_classificacao'])) {
                    self::where('hash_xxhash', $arquivo->hash_xxhash)
                        ->where('eh_duplicado', true)
                        ->update([
                            'status' => $arquivo->status,
                            'caminho_aprovado' => $arquivo->caminho_aprovado,
                            'caminho_proposto' => $arquivo->caminho_proposto,
                            'categoria_proposta' => $arquivo->categoria_proposta,
                            'justificativa_classificacao' => $arquivo->justificativa_classificacao,
                            'data_processamento' => $arquivo->data_processamento,
                        ]);
                }
            }
        });
    }

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
