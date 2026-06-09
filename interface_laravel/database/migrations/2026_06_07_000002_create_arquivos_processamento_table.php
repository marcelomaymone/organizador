<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('arquivos_processamento', function (Blueprint $table) {
            $table->uuid('uuid')->primary();
            $table->foreignId('dispositivo_id')->nullable()->constrained('dispositivos')->onDelete('set null');
            $table->text('caminho_origem')->unique();
            $table->text('nome_original');
            $table->unsignedBigInteger('tamanho_bytes');
            $table->string('hash_xxhash', 32)->index();
            $table->string('status', 30)->default('pendente_extracao')->index();
            
            // Colunas de sugestao de IA e Auditoria
            $table->text('caminho_proposto')->nullable();
            $table->text('caminho_aprovado')->nullable();
            $table->string('categoria_proposta', 50)->nullable()->index();
            $table->text('justificativa_classificacao')->nullable();
            $table->boolean('eh_duplicado')->default(false)->index();
            
            // Tratamento de erros e quarentena
            $table->text('motivo_falha')->nullable();
            $table->text('mensagem_erro')->nullable();
            
            // Timestamps fisicos do SO e metadados ETL
            $table->unsignedBigInteger('data_criacao_sistema')->nullable();
            $table->unsignedBigInteger('data_modificacao_sistema')->nullable();
            $table->timestamp('data_registro')->useCurrent();
            $table->timestamp('data_processamento')->nullable();
            
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('arquivos_processamento');
    }
};
