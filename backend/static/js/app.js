document.addEventListener("DOMContentLoaded", function () {
    const tabButtons = document.querySelectorAll(".tab-button");
    const loginPanel = document.getElementById("login-panel");
    const registerPanel = document.getElementById("register-panel");

    tabButtons.forEach((button) => {
        button.addEventListener("click", function () {
            const target = this.dataset.tab;

            tabButtons.forEach((btn) => btn.classList.remove("active"));
            this.classList.add("active");

            if (loginPanel) loginPanel.classList.remove("active");
            if (registerPanel) registerPanel.classList.remove("active");

            if (target === "login" && loginPanel) {
                loginPanel.classList.add("active");
            }

            if (target === "register" && registerPanel) {
                registerPanel.classList.add("active");
            }
        });
    });

    // Mantém a sidebar no estado que o utilizador deixou
    const sidebar = document.getElementById('main-sidebar');
    if (sidebar) {
        const isExpanded = localStorage.getItem('sidebar-expanded') === 'true';
        if (isExpanded) {
            sidebar.classList.add('expanded');
        }
    }
});

// Abre/Fecha o menu de 3 pontinhos do cartão
function toggleMenu(id) {
    const menu = document.getElementById(id);
    if (!menu) return;
    
    // Fecha outros menus abertos
    document.querySelectorAll('.options-menu').forEach(m => {
        if (m.id !== id) m.classList.add('hidden');
    });
    menu.classList.toggle('hidden');
}

// Abre/Fecha a barra lateral (O que estava a faltar!)
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