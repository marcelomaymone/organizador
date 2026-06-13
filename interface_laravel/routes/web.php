<?php

use Illuminate\Support\Facades\Route;
use App\Models\ArquivoProcessamento;
use Illuminate\Http\Request;

Route::get('/', function () {
    return redirect('/admin'); // Redireciona para o painel principal do Filament
});

Route::post('/admin/duplicados/{uuid}/aprovar', function ($uuid) {
    $arquivo = ArquivoProcessamento::findOrFail($uuid);
    $arquivo->update([
        'status' => 'aprovado_para_movimentacao',
        'caminho_aprovado' => $arquivo->caminho_proposto ?? $arquivo->caminho_origem,
    ]);
    return response()->json(['success' => true]);
})->name('admin.duplicados.aprovar');

Route::post('/admin/duplicados/{uuid}/descartar', function ($uuid) {
    $arquivo = ArquivoProcessamento::findOrFail($uuid);
    $arquivo->update([
        'status' => 'descarte_pendente',
    ]);
    return response()->json(['success' => true]);
})->name('admin.duplicados.descartar');

Route::post('/admin/duplicados/{uuid}/reclassificar', function (Request $request, $uuid) {
    $arquivo = ArquivoProcessamento::findOrFail($uuid);
    $caminho = $request->input('caminho_destino');
    $arquivo->update([
        'status' => 'aprovado_para_movimentacao',
        'caminho_proposto' => $caminho,
        'caminho_aprovado' => $caminho,
    ]);
    return response()->json(['success' => true]);
})->name('admin.duplicados.reclassificar');

