<?php
/**
 * Organizador Pro - Script de Configuração de Ambiente Portátil
 * 
 * DECISÃO ARQUITETURAL:
 * Este script foi concebido para unificar a preparação do ambiente em PHP.
 * O uso de scripts batch (.bat) ou PowerShell puros para manipulação de arquivos de configuração
 * (.env) no Windows frequentemente falha devido a problemas de codificação, caminhos com espaços
 * (ex: "Marcelo Maymone") e escape de aspas. O PHP, por ser a linguagem do BFF Laravel
 * e já estar incluso no pacote portátil, é a ferramenta ideal para processar strings
 * e caminhos de forma segura e multiplataforma.
 */

$raizDir = dirname(__FILE__);
// Normaliza caminhos com barras normais (forward-slash) para o Laravel (.env)
$raizDirForwards = str_replace('\\', '/', $raizDir);

echo "====================================================\n";
echo "    Organizador Pro - Configurando Ambiente...      \n";
echo "====================================================\n";
echo "[+] Pasta Raiz detectada: {$raizDir}\n";

// 1. Garante que a pasta de banco de dados existe
$pastaDb = $raizDir . DIRECTORY_SEPARATOR . 'banco_dados';
if (!is_dir($pastaDb)) {
    mkdir($pastaDb, 0777, true);
    echo "[+] Pasta de banco de dados criada com sucesso.\n";
}

$dbPathForwards = $raizDirForwards . '/banco_dados/database.sqlite';
$destPathForwards = $raizDirForwards . '/pasta_organizada';

// 2. Configuração do .env da raiz do pacote (usado pelo motor Python no modo script)
$envRaiz = $raizDir . DIRECTORY_SEPARATOR . '.env';
if (!file_exists($envRaiz)) {
    echo "[+] Gerando .env na raiz do pacote...\n";
    $conteudoRaiz = "DB_CONNECTION=sqlite\n"
                  . "DB_DATABASE=\"{$dbPathForwards}\"\n"
                  . "DB_FOREIGN_KEYS=true\n"
                  . "DESTINATION_PATH=\"{$destPathForwards}\"\n"
                  . "EMBEDDING_PROVIDER=local\n";
    file_put_contents($envRaiz, $conteudoRaiz);
} else {
    // Atualiza os caminhos para garantir que funcionem se o usuário mover a pasta
    $conteudo = file_get_contents($envRaiz);
    $conteudo = preg_replace('/^DB_DATABASE=.*/m', "DB_DATABASE=\"{$dbPathForwards}\"", $conteudo);
    $conteudo = preg_replace('/^DESTINATION_PATH=.*/m', "DESTINATION_PATH=\"{$destPathForwards}\"", $conteudo);
    file_put_contents($envRaiz, $conteudo);
    echo "[+] .env da raiz atualizado com caminhos locais.\n";
}

// 3. Configuração do .env da interface Laravel
$envLaravel = $raizDir . DIRECTORY_SEPARATOR . 'interface_laravel' . DIRECTORY_SEPARATOR . '.env';
$laravelDir = $raizDir . DIRECTORY_SEPARATOR . 'interface_laravel';

if (!file_exists($envLaravel)) {
    $envExample = $laravelDir . DIRECTORY_SEPARATOR . '.env.example';
    if (file_exists($envExample)) {
        copy($envExample, $envLaravel);
        echo "[+] Criando .env do Laravel a partir do template .env.example...\n";
    } else {
        echo "[ERRO] Arquivo .env.example não encontrado em: {$laravelDir}\n";
        exit(1);
    }
}

// Atualiza caminhos com aspas no Laravel para evitar falhas do parser .env
$conteudoLaravel = file_get_contents($envLaravel);
$conteudoLaravel = preg_replace('/^DB_DATABASE=.*/m', "DB_DATABASE=\"{$dbPathForwards}\"", $conteudoLaravel);
$conteudoLaravel = preg_replace('/^DESTINATION_PATH=.*/m', "DESTINATION_PATH=\"{$destPathForwards}\"", $conteudoLaravel);
file_put_contents($envLaravel, $conteudoLaravel);
echo "[+] .env do Laravel atualizado e normalizado para caminhos com espaços.\n";

// 4. Configuração do .env do motor compilado (dist/motor_organizador/.env)
// Isto é uma compatibilidade necessária porque o executável antigo do motor Python
// foi compilado para buscar o arquivo .env no seu próprio diretório.
$pastaDistMotor = $raizDir . DIRECTORY_SEPARATOR . 'dist' . DIRECTORY_SEPARATOR . 'motor_organizador';
if (is_dir($pastaDistMotor)) {
    $envDist = $pastaDistMotor . DIRECTORY_SEPARATOR . '.env';
    $conteudoDist = "DB_CONNECTION=sqlite\n"
                  . "DB_DATABASE=\"{$dbPathForwards}\"\n"
                  . "DB_FOREIGN_KEYS=true\n"
                  . "DESTINATION_PATH=\"{$destPathForwards}\"\n"
                  . "EMBEDDING_PROVIDER=local\n";
    file_put_contents($envDist, $conteudoDist);
    echo "[+] .env de compatibilidade gerado em: dist/motor_organizador/.env\n";
}

// 5. Verifica/Gera o APP_KEY do Laravel
// O Laravel BFF exige uma chave de aplicação (APP_KEY) para encriptar sessões e cookies.
// Se estiver vazia, geramos uma de forma automática usando a ferramenta artisan CLI.
$linhasLaravel = file($envLaravel, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
$hasAppKey = false;
foreach ($linhasLaravel as $linha) {
    if (strpos($linha, 'APP_KEY=') === 0 && strlen(trim(substr($linha, 8))) > 0) {
        $hasAppKey = true;
        break;
    }
}

$artisanScript = $laravelDir . DIRECTORY_SEPARATOR . 'artisan';
$phpExe = $raizDir . DIRECTORY_SEPARATOR . 'php' . DIRECTORY_SEPARATOR . 'php.exe';
if (!file_exists($phpExe)) {
    $phpExe = 'php'; // Fallback para PHP do sistema
}

if (!$hasAppKey) {
    echo "[+] APP_KEY do Laravel não encontrada. Gerando chave automaticamente...\n";
    $cmdKey = '"' . $phpExe . '" "' . $artisanScript . '" key:generate';
    shell_exec($cmdKey);
}

// 6. Roda migrações do banco de dados (se necessário)
// Para garantir que o banco SQLite esteja estruturado na primeira execução portátil
// sem a necessidade de intervenção do usuário ou erros de "tabela inexistente".
echo "[+] Verificando estrutura do banco de dados...\n";
$cmdMigrate = '"' . $phpExe . '" "' . $artisanScript . '" migrate --force';
shell_exec($cmdMigrate);

echo "[+] Ambiente configurado com sucesso!\n";
echo "====================================================\n\n";
