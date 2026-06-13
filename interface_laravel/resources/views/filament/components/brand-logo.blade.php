<div class="brand-logo-container flex items-center gap-3 py-1">
    <!-- SVG Minimalista: Cubo Isométrico Organizador com gradientes Celeste e Solar -->
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" class="h-10 w-10">
        <defs>
            <!-- Gradiente Celeste (Marinho para Ciano) -->
            <linearGradient id="gradCeleste" x1="0%" y1="100%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#0284c7" />
                <stop offset="100%" stop-color="#06b6d4" />
            </linearGradient>
            <!-- Gradiente Solar (Laranja para Amarelo Ouro) -->
            <linearGradient id="gradSolar" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#f97316" />
                <stop offset="100%" stop-color="#eab308" />
            </linearGradient>
        </defs>

        <!-- Face Superior do Cubo (Solar) -->
        <polygon points="50,15 80,32 50,50 20,32" fill="url(#gradSolar)" opacity="0.9" />
        
        <!-- Face Esquerda (Marinho Escuro / Azul Profundo) -->
        <polygon points="20,32 50,50 50,85 20,67" fill="#1e3e62" opacity="0.8" />
        
        <!-- Face Direita (Celeste) -->
        <polygon points="50,50 80,32 80,67 50,85" fill="url(#gradCeleste)" opacity="0.95" />

        <!-- Elemento Central do Cubo (O "Core" da Organização) -->
        <circle cx="50" cy="50" r="8" fill="#ffffff" opacity="0.9" />
    </svg>
    
    <!-- Texto do Logotipo com Gradiente Premium -->
    <span class="brand-logo-text text-xl font-black tracking-wider uppercase font-sans">
        Organizador Pro
    </span>
</div>
