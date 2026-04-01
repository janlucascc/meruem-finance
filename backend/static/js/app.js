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