(function () {
  const particlesContainer = document.getElementById('particles-js');
  if (particlesContainer && window.particlesJS) {
    particlesJS.load('particles-js', '/static/js/particles.json');
  }

  const timerEl = document.querySelector('[data-exam-timer]');
  if (!timerEl) {
    return;
  }

  let remaining = Number(timerEl.getAttribute('data-remaining-seconds') || 0);
  const fmt = (n) => String(n).padStart(2, '0');

  const render = () => {
    const mm = Math.floor(Math.max(remaining, 0) / 60);
    const ss = Math.max(remaining, 0) % 60;
    timerEl.textContent = `${fmt(mm)}:${fmt(ss)}`;
  };

  render();
  const interval = setInterval(() => {
    remaining -= 1;
    render();
    if (remaining <= 0) {
      clearInterval(interval);
      const submitBtn = document.querySelector('button[name="action"][value="submit"]');
      if (submitBtn) {
        submitBtn.click();
      }
    }
  }, 1000);
})();
