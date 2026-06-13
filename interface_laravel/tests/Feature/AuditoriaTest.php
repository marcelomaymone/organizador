<?php

namespace Tests\Feature;

use App\Models\ArquivoProcessamento;
use App\Models\Dispositivo;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class AuditoriaTest extends TestCase
{
    use RefreshDatabase;

    public function test_pode_filtrar_arquivos_originais_e_duplicados(): void
    {
        $dispositivo = Dispositivo::create([
            'uuid' => 'dev-uuid',
            'nome' => 'Disco Externo',
        ]);

        $original = ArquivoProcessamento::create([
            'uuid' => 'orig-uuid',
            'dispositivo_id' => $dispositivo->id,
            'caminho_origem' => 'C:/origem/doc1.pdf',
            'nome_original' => 'doc1.pdf',
            'tamanho_bytes' => 1024,
            'hash_xxhash' => 'hash123',
            'status' => 'aguardando_auditoria',
            'eh_duplicado' => false,
        ]);

        $duplicado = ArquivoProcessamento::create([
            'uuid' => 'dup-uuid',
            'dispositivo_id' => $dispositivo->id,
            'caminho_origem' => 'C:/origem/backup/doc1.pdf',
            'nome_original' => 'doc1.pdf',
            'tamanho_bytes' => 1024,
            'hash_xxhash' => 'hash123',
            'status' => 'aguardando_auditoria',
            'eh_duplicado' => true,
        ]);

        // Testa o escopo de originais
        $originais = ArquivoProcessamento::original()->get();
        $this->assertCount(1, $originais);
        $this->assertEquals('orig-uuid', $originais->first()->uuid);

        // Testa a obtenção de duplicados a partir do original
        $dups = $original->obterDuplicados();
        $this->assertCount(1, $dups);
        $this->assertEquals('dup-uuid', $dups->first()->uuid);
    }

    public function test_pode_aprovar_duplicado_via_rota_ajax(): void
    {
        $dispositivo = Dispositivo::create([
            'uuid' => 'dev-uuid',
            'nome' => 'Disco Externo',
        ]);

        $duplicado = ArquivoProcessamento::create([
            'uuid' => 'dup-uuid',
            'dispositivo_id' => $dispositivo->id,
            'caminho_origem' => 'C:/origem/backup/doc1.pdf',
            'nome_original' => 'doc1.pdf',
            'tamanho_bytes' => 1024,
            'hash_xxhash' => 'hash123',
            'status' => 'aguardando_auditoria',
            'eh_duplicado' => true,
            'caminho_proposto' => 'C:/destino/doc1.pdf',
        ]);

        $response = $this->post("/admin/duplicados/{$duplicado->uuid}/aprovar");

        $response->assertStatus(200);
        $response->assertJson(['success' => true]);

        $duplicado->refresh();
        $this->assertEquals('aprovado_para_movimentacao', $duplicado->status);
        $this->assertEquals('C:/destino/doc1.pdf', $duplicado->caminho_aprovado);
    }

    public function test_pode_descartar_duplicado_via_rota_ajax(): void
    {
        $dispositivo = Dispositivo::create([
            'uuid' => 'dev-uuid',
            'nome' => 'Disco Externo',
        ]);

        $duplicado = ArquivoProcessamento::create([
            'uuid' => 'dup-uuid',
            'dispositivo_id' => $dispositivo->id,
            'caminho_origem' => 'C:/origem/backup/doc1.pdf',
            'nome_original' => 'doc1.pdf',
            'tamanho_bytes' => 1024,
            'hash_xxhash' => 'hash123',
            'status' => 'aguardando_auditoria',
            'eh_duplicado' => true,
        ]);

        $response = $this->post("/admin/duplicados/{$duplicado->uuid}/descartar");

        $response->assertStatus(200);
        $response->assertJson(['success' => true]);

        $duplicado->refresh();
        $this->assertEquals('descarte_pendente', $duplicado->status);
    }

    public function test_pode_reclassificar_duplicado_via_rota_ajax(): void
    {
        $dispositivo = Dispositivo::create([
            'uuid' => 'dev-uuid',
            'nome' => 'Disco Externo',
        ]);

        $duplicado = ArquivoProcessamento::create([
            'uuid' => 'dup-uuid',
            'dispositivo_id' => $dispositivo->id,
            'caminho_origem' => 'C:/origem/backup/doc1.pdf',
            'nome_original' => 'doc1.pdf',
            'tamanho_bytes' => 1024,
            'hash_xxhash' => 'hash123',
            'status' => 'aguardando_auditoria',
            'eh_duplicado' => true,
        ]);

        $response = $this->post("/admin/duplicados/{$duplicado->uuid}/reclassificar", [
            'caminho_destino' => 'C:/destino/reclassificado.pdf'
        ]);

        $response->assertStatus(200);
        $response->assertJson(['success' => true]);

        $duplicado->refresh();
        $this->assertEquals('aprovado_para_movimentacao', $duplicado->status);
        $this->assertEquals('C:/destino/reclassificado.pdf', $duplicado->caminho_aprovado);
    }
}
