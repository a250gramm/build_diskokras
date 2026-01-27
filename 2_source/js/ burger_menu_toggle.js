// Burger menu toggle
document.addEventListener('DOMContentLoaded', () => {
    // Ищем burger внутри header_menu
    const menuContainer = document.querySelector('[data-path="header_menu"]');
    // Ищем icon с классом content-burger (ключ элемента - burger)
    const burger = menuContainer ? menuContainer.querySelector('icon.content-burger') : null;
    // Ищем nav с классом menu1 (ключ элемента - nav_menu1)
    const menuNav = menuContainer ? menuContainer.querySelector('nav.menu1') : null;
    
    console.log('Burger menu toggle:', { menuContainer, burger, menuNav });
    
    if (burger && menuNav) {
        burger.addEventListener('click', () => {
            console.log('Burger clicked, toggling opened class');
            menuNav.classList.toggle('opened');
            console.log('Menu classes:', menuNav.className);
        });
    } else {
        console.error('Burger menu elements not found:', { burger, menuNav });
    }
});

