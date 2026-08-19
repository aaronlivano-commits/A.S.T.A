document.addEventListener('DOMContentLoaded', () => {
  const tabs = document.querySelectorAll('.tab');
  const panels = document.querySelectorAll('.panel');
  const consoleNav = document.querySelector('.console');
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function activate(tabId) {
    tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tabId));
    panels.forEach(p => p.classList.toggle('active', p.id === 'tab-' + tabId));
  }

  tabs.forEach(btn => {
    btn.addEventListener('click', () => {
      activate(btn.dataset.tab);
      const panel = document.getElementById('tab-' + btn.dataset.tab);
      panel.scrollIntoView({ behavior: prefersReduced ? 'auto' : 'smooth', block: 'start' });
    });
  });

  // Hero "INITIATE BRIEFING" button: jump into the console and open Overview
  const beginBtn = document.getElementById('beginBriefing');
  if (beginBtn) {
    beginBtn.addEventListener('click', () => {
      activate('overview');
      consoleNav.scrollIntoView({ behavior: prefersReduced ? 'auto' : 'smooth', block: 'start' });
    });
  }

  // Allow direct links like #tab-arch to open the right panel on load
  if (location.hash.startsWith('#tab-')) {
    const target = location.hash.replace('#tab-', '');
    activate(target);
  }
});
