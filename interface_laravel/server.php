<?php
/**
 * Organizador Pro - Roteador de Emulação de Servidor Web (server.php)
 * 
 * DECISÃO ARQUITETURAL:
 * Este arquivo funciona como router para o PHP Built-in Server.
 * Sem ele, ao passar public/index.php diretamente no comando do servidor,
 * todas as requisições estáticas (CSS, JS, imagens do Filament) são capturadas
 * pelo Laravel, que retorna HTML da página de erro ou de login.
 * Retornando 'false' quando o arquivo físico existe em public/, o PHP
 * serve o arquivo estático diretamente com o Content-Type correto.
 */

$uri = urldecode(
    parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH)
);

// Se a rota aponta para um arquivo existente na pasta public, o PHP
// server deve servir o recurso estático diretamente.
if ($uri !== '/' && file_exists(__DIR__.'/public'.$uri)) {
    return false;
}

require_once __DIR__.'/public/index.php';
