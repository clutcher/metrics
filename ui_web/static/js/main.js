function initializeTaskForecastToggles() {
    document.querySelectorAll('.task-toggle').forEach(button => {
        button.addEventListener('click', function() {
            const parentLevel = parseInt(this.getAttribute('data-parent-level'));
            const parentRow = this.closest('tr');
            const icon = this.querySelector('i[class*="iconoir"]');
            
            let currentRow = parentRow.nextElementSibling;
            const childRows = [];
            
            while (currentRow) {
                const rowLevel = parseInt(currentRow.getAttribute('data-level'));
                
                if (rowLevel <= parentLevel) {
                    break;
                }
                
                if (rowLevel > parentLevel) {
                    childRows.push(currentRow);
                }
                
                currentRow = currentRow.nextElementSibling;
            }
            
            const isExpanded = icon.classList.contains('iconoir-nav-arrow-down');
            
            childRows.forEach(row => {
                if (isExpanded) {
                    row.classList.add('is-hidden');
                    const childToggle = row.querySelector('.task-toggle i[class*="iconoir"]');
                    if (childToggle && childToggle.classList.contains('iconoir-nav-arrow-down')) {
                        childToggle.className = 'iconoir-nav-arrow-right';
                    }
                } else {
                    const rowLevel = parseInt(row.getAttribute('data-level'));
                    if (rowLevel === parentLevel + 1) {
                        row.classList.remove('is-hidden');
                    }
                }
            });
            
            if (icon) {
                icon.className = isExpanded ? 'iconoir-nav-arrow-right' : 'iconoir-nav-arrow-down';
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    
    function handleMenuToggle(e) {
        e.preventDefault();
        
        const targetId = this.getAttribute('data-target');
        const submenu = document.getElementById(targetId);
        
        if (submenu) {
            const isHidden = submenu.classList.contains('is-hidden');
            
            if (isHidden) {
                submenu.classList.remove('is-hidden');
                this.setAttribute('aria-expanded', 'true');
            } else {
                submenu.classList.add('is-hidden');
                this.setAttribute('aria-expanded', 'false');
            }
        }
    }
    
    function setActiveMenuItem(clickedElement) {
        if (!clickedElement || clickedElement.tagName !== 'A' || !clickedElement.closest('.menu-list')) {
            return;
        }
        
        document.querySelectorAll('.menu-list .is-active').forEach(item => {
            item.classList.remove('is-active');
        });
        
        clickedElement.classList.add('is-active');
        
        const parentSubmenu = clickedElement.closest('.menu-submenu');
        if (parentSubmenu) {
            parentSubmenu.classList.remove('is-hidden');
            
            const submenuId = parentSubmenu.getAttribute('id');
            const toggle = document.querySelector(`[data-target="${submenuId}"]`);
            if (toggle) {
                toggle.classList.add('is-active');
                toggle.setAttribute('aria-expanded', 'true');
            }
        }
    }
    
    function expandInitialActiveMenus() {
        const activeMenus = document.querySelectorAll('.menu-list .is-active');
        activeMenus.forEach(activeItem => {
            const parentSubmenu = activeItem.closest('.menu-submenu');
            if (parentSubmenu) {
                parentSubmenu.classList.remove('is-hidden');
                
                const submenuId = parentSubmenu.getAttribute('id');
                const toggle = document.querySelector(`[data-target="${submenuId}"]`);
                if (toggle) {
                    toggle.setAttribute('aria-expanded', 'true');
                }
            }
        });
    }
    
    function showLoadingIndicator() {
        const indicator = document.getElementById('loading-indicator');
        if (indicator) {
            indicator.classList.remove('is-hidden');
        }
    }
    
    function hideLoadingIndicator() {
        const indicator = document.getElementById('loading-indicator');
        if (indicator) {
            indicator.classList.add('is-hidden');
        }
    }
    
    document.querySelectorAll('.menu-toggle').forEach(toggle => {
        toggle.addEventListener('click', handleMenuToggle);
    });
    expandInitialActiveMenus();
    
    document.querySelectorAll('.menu-list a').forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.hasAttribute('hx-get') || this.hasAttribute('hx-post')) {
                setActiveMenuItem(this);
            }
        });
    });
    
    document.querySelectorAll('details').forEach(details => {
        details.addEventListener('toggle', function() {
            const icon = this.querySelector('summary i[class*="iconoir"]');
            if (icon) {
                icon.className = this.open ? 'iconoir-nav-arrow-down' : 'iconoir-nav-arrow-right';
            }
        });
    });
    
    document.body.addEventListener('htmx:beforeRequest', showLoadingIndicator);
    document.body.addEventListener('htmx:afterRequest', hideLoadingIndicator);
    
    window.addEventListener('popstate', function() {
        const currentPath = window.location.pathname;
        const currentSearch = window.location.search;
        const currentUrl = currentPath + currentSearch;
        
        const matchingLink = document.querySelector(`.menu-list a[href="${currentUrl}"]`);
        if (matchingLink) {
            setActiveMenuItem(matchingLink);
        }
    });
});