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
        Schema::create('dispositivos', function (Blueprint $table) {
            $table->id();
            $table->uuid('uuid')->unique();
            $table->string('nome')->nullable();
            $table->string('ponto_montagem')->nullable();
            $table->string('tipo_sistema_arquivos')->nullable();
            $table->unsignedBigInteger('capacidade_bytes')->nullable();
            $table->unsignedBigInteger('espaco_livre_bytes')->nullable();
            $table->string('hardware_id')->unique()->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('dispositivos');
    }
};
