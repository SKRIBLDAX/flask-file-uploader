// main.js — универсальный скрипт для темы и языка на всех страницах

// --- Универсальные функции темы ---
function setTheme(theme) {
  if (theme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('theme', 'dark');
    if (window.themeSwitch) themeSwitch.checked = true;
    if (window.themeSwitchDropdown) themeSwitchDropdown.checked = true;
    if (window.themeSwitchLabelDropdown) themeSwitchLabelDropdown.textContent = getTranslation('light');
    if (window.themeSwitchLabel) themeSwitchLabel.textContent = getTranslation('light');
  } else {
    document.documentElement.setAttribute('data-theme', 'light');
    localStorage.setItem('theme', 'light');
    if (window.themeSwitch) themeSwitch.checked = false;
    if (window.themeSwitchDropdown) themeSwitchDropdown.checked = false;
    if (window.themeSwitchLabelDropdown) themeSwitchLabelDropdown.textContent = getTranslation('dark');
    if (window.themeSwitchLabel) themeSwitchLabel.textContent = getTranslation('dark');
  }
}

// --- Универсальные функции языка ---
function setLang(lang) {
  localStorage.setItem('lang', lang);
  // Переключатели
  if (window.langLabelDropdown) langLabelDropdown.textContent = lang.toUpperCase();
  if (window.langFlagDropdown) langFlagDropdown.textContent = lang === 'ru' ? '🇷🇺' : '🇬🇧';
  if (window.langLabel) langLabel.textContent = lang.toUpperCase();
  if (window.langFlag) langFlag.textContent = lang === 'ru' ? '🇷🇺' : '🇬🇧';
  // Переводы для страницы
  applyTranslations(lang);
}

// --- Получить перевод по ключу ---
function getTranslation(key) {
  const lang = localStorage.getItem('lang') || 'ru';
  if (window.translations && translations[lang] && translations[lang][key]) {
    return translations[lang][key];
  }
  return key;
}

// --- Применить переводы для страницы ---
function applyTranslations(lang) {
  // Для каждой страницы реализовать свою applyTranslations, если нужно
  if (typeof window.applyPageTranslations === 'function') {
    window.applyPageTranslations(lang);
  }
}

// --- Синхронизация между вкладками ---
window.addEventListener('storage', function(e) {
  if (e.key === 'theme') setTheme(localStorage.getItem('theme'));
  if (e.key === 'lang') setLang(localStorage.getItem('lang'));
});

// --- Инициализация ---
document.addEventListener('DOMContentLoaded', function() {
  // Переключатель темы
  window.themeSwitch = document.getElementById('themeSwitch');
  window.themeSwitchDropdown = document.getElementById('themeSwitchDropdown');
  window.themeSwitchLabelDropdown = document.getElementById('themeSwitchLabelDropdown');
  window.themeSwitchLabel = document.getElementById('themeSwitchLabel');
  // Переключатель языка
  window.langLabelDropdown = document.getElementById('langLabelDropdown');
  window.langFlagDropdown = document.getElementById('langFlagDropdown');
  window.langLabel = document.getElementById('langLabel');
  window.langFlag = document.getElementById('langFlag');

  // Обработчики темы
  if (window.themeSwitchDropdown) {
    themeSwitchDropdown.addEventListener('change', function() {
      setTheme(this.checked ? 'dark' : 'light');
    });
  }
  if (window.themeSwitch) {
    themeSwitch.addEventListener('change', function() {
      setTheme(this.checked ? 'dark' : 'light');
    });
  }

  // Обработчики языка
  document.querySelectorAll('.lang-option-dropdown').forEach(el => {
    el.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      setLang(this.dataset.lang);
      // Оставить dropdown открытым
      const dropdownMenu = this.closest('.dropdown-menu');
      if (dropdownMenu) {
        const dropdownToggle = dropdownMenu.parentElement.querySelector('[data-bs-toggle="dropdown"]');
        if (dropdownToggle) {
          setTimeout(() => {
            const dropdown = bootstrap.Dropdown.getOrCreateInstance(dropdownToggle);
            dropdown.show();
          }, 0);
        }
      }
    });
  });
  document.querySelectorAll('.lang-option').forEach(el => {
    el.addEventListener('click', function(e) {
      e.preventDefault();
      setLang(this.dataset.lang);
    });
  });

  // Применить тему и язык при загрузке
  setTheme(localStorage.getItem('theme') || 'light');
  setLang(localStorage.getItem('lang') || 'ru');
}); 