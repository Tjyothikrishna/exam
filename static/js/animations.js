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
  if (window.location.pathname !== '/question') {
    sessionStorage.removeItem('exam_elapsed_seconds');
  }

  const timerEl = document.querySelector('[data-exam-timer]');
  if (timerEl) {
    const key = 'exam_elapsed_seconds';
    let elapsed = Number(sessionStorage.getItem(key) || 0);
    const fmt = (n) => String(n).padStart(2, '0');
    const render = () => {
      const mm = Math.floor(elapsed / 60);
      const ss = elapsed % 60;
      timerEl.textContent = `${fmt(mm)}:${fmt(ss)}`;
    };

    render();
    const interval = setInterval(() => {
      elapsed += 1;
      sessionStorage.setItem(key, String(elapsed));
      render();
    }, 1000);

    window.addEventListener('beforeunload', () => clearInterval(interval));

    const submitBtn = document.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.addEventListener('click', () => {
        // keep elapsed timer during exam pages
      });
    }

  }
})();
