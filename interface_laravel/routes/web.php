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

Route::get('/admin/desligar', function () {
    // DECISÃO ARQUITETURAL:
    // Limpar os caches antes do desligamento garante que, quando a pasta portátil
    // for movida ou distribuída, não existam caminhos físicos absolutos cacheados
    // que possam quebrar a próxima execução em outro diretório.
    try {
        \Illuminate\Support\Facades\Artisan::call('config:clear');
        \Illuminate\Support\Facades\Artisan::call('cache:clear');
        \Illuminate\Support\Facades\Artisan::call('route:clear');
    } catch (\Exception $e) {
        // Silencia falhas no modo portátil
    }

    // Executa o comando de encerramento em background com atraso de 2 segundos no Windows.
    // Isso dá tempo para o servidor PHP enviar a resposta HTML de despedida antes de encerrar
    // seu próprio processo e o processo do motor Python de forma limpa.
    if (substr(php_uname(), 0, 7) == "Windows") {
        pclose(popen('start /B cmd /c "timeout /t 2 >nul && taskkill /F /IM motor_organizador.exe && taskkill /F /IM php.exe"', 'r'));
    } else {
        exec('sleep 2 && killall php > /dev/null &');
    }

    return view('desligar');
})->name('desligar-app');

