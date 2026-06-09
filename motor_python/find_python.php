<?php
$userProfile = getenv('USERPROFILE');
$output = "UserProfile: $userProfile\n";

$possiblePaths = [
    $userProfile . "\\Miniconda3\\python.exe",
    $userProfile . "\\Miniconda3\\Scripts\\python.exe",
    $userProfile . "\\Miniconda3\\Scripts\\uv.exe",
    $userProfile . "\\AppData\\Local\\Programs\\Python\\Python310\\python.exe",
    $userProfile . "\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
    $userProfile . "\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
    $userProfile . "\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
    "C:\\Python310\\python.exe",
    "C:\\Python311\\python.exe",
    "C:\\Python312\\python.exe",
    "C:\\Program Files\\Python310\\python.exe",
    "C:\\Program Files\\Python311\\python.exe",
    "C:\\Program Files\\Python312\\python.exe",
    $userProfile . "\\.local\\bin\\uv.exe"
];

foreach ($possiblePaths as $path) {
    if (file_exists($path)) {
        $output .= "ENCONTRADO: $path (Tamanho: " . filesize($path) . " bytes)\n";
    } else {
        $output .= "NAO EXISTE: $path\n";
    }
}

// Verifica variaveis de ambiente relevantes
$output .= "\n=== VARIAVEIS DE AMBIENTE ===\n";
$output .= "PATH: " . getenv('PATH') . "\n";

file_put_contents(__DIR__ . DIRECTORY_SEPARATOR . 'find_python_results.txt', $output);
echo "Resultados gravados com sucesso.\n";
