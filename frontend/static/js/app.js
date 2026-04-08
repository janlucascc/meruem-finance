document.addEventListener("DOMContentLoaded", function () {
    const tabButtons = document.querySelectorAll(".tab-button");
    const loginPanel = document.getElementById("login-panel");
    const registerPanel = document.getElementById("register-panel");

    // Lógica das Abas (Login / Register)
    tabButtons.forEach((button) => {
        button.addEventListener("click", function () {
            const target = this.dataset.tab;

            tabButtons.forEach((btn) => btn.classList.remove("active"));
            this.classList.add("active");

            if (loginPanel) loginPanel.classList.remove("active");
            if (registerPanel) registerPanel.classList.remove("active");

            if (target === "login" && loginPanel) loginPanel.classList.add("active");
            if (target === "register" && registerPanel) registerPanel.classList.add("active");
        });
    });

    // Mantém a sidebar no estado salvo
    const sidebar = document.getElementById('main-sidebar');
    if (sidebar) {
        const isExpanded = localStorage.getItem('sidebar-expanded') === 'true';
        if (isExpanded) sidebar.classList.add('expanded');
    }

    // --- NOVA LÓGICA: VIBRAÇÃO DE ERRO ---
    // Verifica se há alguma notificação com a classe 'flash-error' na tela
    const errorFlash = document.querySelector('.flash-error');
    if (errorFlash) {
        // Pega todos os inputs da tela de autenticação que está ativa
        const formInputs = document.querySelectorAll('.tab-panel.active input, .auth-card input, .single-card-wrap input');
        
        formInputs.forEach(input => {
            // Adiciona a classe que faz o campo tremer e ficar vermelho
            input.classList.add('input-error');
            
            // UX de Ouro: Se o usuário começar a digitar novamente, o vermelho some!
            input.addEventListener('input', function() {
                this.classList.remove('input-error');
            });
        });
    }
});

// Abre/Fecha o menu de 3 pontinhos do cartão
function toggleMenu(id) {
    const menu = document.getElementById(id);
    if (!menu) return;
    document.querySelectorAll('.options-menu').forEach(m => {
        if (m.id !== id) m.classList.add('hidden');
    });
    menu.classList.toggle('hidden');
}

// Abre/Fecha a barra lateral
function toggleSidebar() {
    const sidebar = document.getElementById('main-sidebar');
    if (!sidebar) return;
    sidebar.classList.toggle('expanded');
    localStorage.setItem('sidebar-expanded', sidebar.classList.contains('expanded'));
}

// Fecha menus suspensos ao clicar fora
document.addEventListener('click', function(e) {
    if (!e.target.classList.contains('options-trigger')) {
        document.querySelectorAll('.options-menu').forEach(m => m.classList.add('hidden'));
    }
});

document.addEventListener('DOMContentLoaded', function() {
    
    // Apanhar os elementos
    const lista = document.getElementById('transactions-list');
    const itens = document.querySelectorAll('.transaction-item');
    const btnExpandir = document.getElementById('btn-expand-tx');
    const btnRecolher = document.getElementById('btn-collapse-tx');

    // Se não existirem na página (por exemplo, se estivermos noutra página), paramos aqui
    if (!lista || !btnExpandir || !btnRecolher) return;

    // Configurações iniciais
    const LIMITE_INICIAL = 3;
    const INCREMENTO = 10;
    let itensVisiveis = LIMITE_INICIAL;

    function atualizarInterface() {
        itens.forEach((item, index) => {
            if (index < itensVisiveis) {
                item.style.display = '';
                // Um pequeno truque para a animação do CSS funcionar
                setTimeout(() => item.style.opacity = '1', 50); 
            } else {
                item.style.opacity = '0';
                item.style.display = 'none';
            }
        });

        // Controlo dos botões
        btnExpandir.style.display = (itensVisiveis < itens.length) ? 'inline-block' : 'none';
        btnRecolher.style.display = (itensVisiveis > LIMITE_INICIAL) ? 'inline-block' : 'none';
    }

    // Ações dos cliques
    btnExpandir.addEventListener('click', function() {
        itensVisiveis += INCREMENTO;
        atualizarInterface();
    });

    btnRecolher.addEventListener('click', function() {
        itensVisiveis = LIMITE_INICIAL;
        atualizarInterface();
    });

    // Iniciar
    atualizarInterface();
});

// ==========================================
// EFEITO MAGNÉTICO E ORGÂNICO (Botões)
// ==========================================
document.addEventListener("DOMContentLoaded", function () {
    // Seleciona os botões que terão o efeito elástico/magnético
    const magneticButtons = document.querySelectorAll('.primary-button, .secondary-button, #btn-expand-tx, #btn-collapse-tx, .tab-button');

    magneticButtons.forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const rect = btn.getBoundingClientRect();
            // Calcula o centro do botão
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            
            // Aplica a força magnética (move o botão na direção do cursor)
            // O multiplicador (0.3) define o quão "elástico" ele é. 
            btn.style.transform = `translate(${x * 0.3}px, ${y * 0.3}px) scale(1.03)`;
        });

        btn.addEventListener('mouseleave', () => {
            // Quando o mouse sai, a mola solta e ele volta ao normal
            btn.style.transform = 'translate(0px, 0px) scale(1)';
        });
    });
});