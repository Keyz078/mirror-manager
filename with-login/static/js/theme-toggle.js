// Theme toggle logic (copy dari index.html)
const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');
const themeToggleBtn = document.getElementById('theme-toggle');

function updateThemeIcon() {
    if (localStorage.getItem('color-theme') === 'dark' ||
        (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        themeToggleLightIcon.classList.remove('hidden');
        themeToggleDarkIcon.classList.add('hidden');
        document.documentElement.classList.add('dark');
    } else {
        themeToggleDarkIcon.classList.remove('hidden');
        themeToggleLightIcon.classList.add('hidden');
        document.documentElement.classList.remove('dark');
    }
}

if (themeToggleBtn) {
    updateThemeIcon();
    themeToggleBtn.addEventListener('click', function () {
        // toggle theme
        if (document.documentElement.classList.contains('dark')) {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('color-theme', 'light');
        } else {
            document.documentElement.classList.add('dark');
            localStorage.setItem('color-theme', 'dark');
        }
        updateThemeIcon();
    });
} else {
    updateThemeIcon();
}