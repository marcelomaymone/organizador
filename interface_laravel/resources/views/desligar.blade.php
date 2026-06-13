<!DOCTYPE html>
<html lang="pt-BR" class="h-full bg-gray-950">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Desligando - Organizador Pro</title>
    <!-- Tailwind CSS (utilizando versão inline para independência de builds na distribuição estática) -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background-color: #030712;
            color: #f3f4f6;
            font-family: ui-sans-serif, system-ui, sans-serif;
        }
        @keyframes fadeOut {
            from { opacity: 1; transform: scale(1); }
            to { opacity: 0.3; transform: scale(0.95); }
        }
        .animate-shutdown {
            animation: fadeOut 2.5s forwards ease-in-out;
        }
        .brand-text {
            background: linear-gradient(to right, #ffffff, #06b6d4, #f97316);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
    </svg>
</head>
<body class="flex h-full flex-col items-center justify-center p-6 text-center">
    <div class="max-w-md w-full space-y-8 bg-gray-900 border border-gray-800 rounded-2xl p-8 shadow-2xl animate-shutdown">
        
        <!-- Logo do App -->
        <div class="flex justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 100 100" class="h-16 w-16 text-cyan-500">
                <polygon points="50,15 80,32 50,50 20,32" fill="#f97316" opacity="0.9" />
                <polygon points="20,32 50,50 50,85 20,67" fill="#1e3e62" opacity="0.8" />
                <polygon points="50,50 80,32 80,67 50,85" fill="#06b6d4" opacity="0.95" />
                <circle cx="50" cy="50" r="8" fill="#ffffff" />
            </svg>
        </div>

        <div class="space-y-4">
            <h1 class="text-2xl font-black tracking-wider uppercase brand-text">
                Organizador Pro
            </h1>
            <p id="status-title" class="text-lg font-bold text-white">
                Encerrando Aplicação...
            </p>
            <p id="status-desc" class="text-sm text-gray-400">
                Os servidores do Laravel e os Workers do motor Python estão sendo desligados. Os caches locais foram limpos.
            </p>
        </div>

        <!-- Indicador de Status/Carregamento -->
        <div class="flex justify-center py-2">
            <div class="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                <div class="h-full bg-gradient-to-r from-cyan-500 to-orange-500 rounded-full animate-[shimmer_2s_infinite]" style="width: 100%; transition: width 2s ease-in-out;"></div>
            </div>
        </div>

        <p class="text-xs text-gray-500">
            Esta aba do navegador tentará fechar automaticamente. Se não fechar, você pode fechá-la manualmente.
        </p>
    </div>

    <script>
        // Fecha a janela após 2 segundos (tempo suficiente para enviar a resposta HTTP)
        setTimeout(function() {
            window.close();
            // Caso o navegador bloqueie a fechamento por segurança, atualiza o status na tela
            document.getElementById('status-title').innerText = 'Aplicação Desligada!';
            document.getElementById('status-desc').innerText = 'Todos os serviços em segundo plano foram parados com sucesso. Você pode fechar esta aba com segurança.';
        }, 2000);
    </script>
</body>
</html>
