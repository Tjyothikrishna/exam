(function () {
  const timerEl = document.querySelector('[data-exam-timer]');
  const questionForm = document.querySelector('[data-question-form]');

  // localStorage autosave for selected options
  if (questionForm) {
    const questionId = questionForm.dataset.questionId;
    const storageKey = 'exam_answers_cache';
    const flaggedKey = 'exam_flagged_cache';

    const answers = JSON.parse(localStorage.getItem(storageKey) || '{}');
    const flagged = JSON.parse(localStorage.getItem(flaggedKey) || '{}');

    if (questionId && answers[questionId]) {
      const radio = questionForm.querySelector(`input[name="option"][value="${answers[questionId]}"]`);
      if (radio) {
        radio.checked = true;
      }
    }

    questionForm.querySelectorAll('input[name="option"]').forEach((input) => {
      input.addEventListener('change', async () => {
        answers[questionId] = Number(input.value);
        localStorage.setItem(storageKey, JSON.stringify(answers));

        const formData = new URLSearchParams();
        formData.set('action', 'autosave');
        formData.set('current_index', questionForm.querySelector('input[name="current_index"]').value);
        formData.set('option', input.value);
        formData.set('flagged', questionForm.dataset.flagged || '0');

        try {
          await fetch(questionForm.dataset.autosaveUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData.toString(),
          });
        } catch (e) {
          console.debug('Autosave failed', e);
        }
      });
    });

    const flagBtn = questionForm.querySelector('button[name="action"][value="flag_toggle"]');
    if (flagBtn) {
      flagBtn.addEventListener('click', () => {
        flagged[questionId] = !(questionForm.dataset.flagged === '1');
        localStorage.setItem(flaggedKey, JSON.stringify(flagged));
      });
    }

    const submitBtn = questionForm.querySelector('button[name="action"][value="review"]');
    if (submitBtn) {
      submitBtn.addEventListener('click', () => {
        // Keep local storage for review stage.
      });
    }
  }

  // Countdown timer + warning + auto submit
  if (timerEl) {
    let remaining = Number(timerEl.getAttribute('data-remaining-seconds') || 0);
    const fmt = (n) => String(n).padStart(2, '0');

    const render = () => {
      const mm = Math.floor(Math.max(remaining, 0) / 60);
      const ss = Math.max(remaining, 0) % 60;
      timerEl.textContent = `${fmt(mm)}:${fmt(ss)}`;
      if (remaining <= 300) {
        timerEl.classList.add('timer-warning');
      }
    };

    render();
    const interval = setInterval(() => {
      remaining -= 1;
      render();
      if (remaining <= 0) {
        clearInterval(interval);
        const finalSubmit = document.querySelector('form[action$="/submit_test"] button[type="submit"]')
          || document.querySelector('button[name="action"][value="review"]');
        if (finalSubmit) {
          finalSubmit.click();
        }
      }
    }, 1000);
  }

  // Particles for landing
  const particlesContainer = document.getElementById('particles-js');
  if (particlesContainer && window.particlesJS) {
    particlesJS.load('particles-js', '/static/js/particles.json');
  }

  // cleanup local storage when result page is loaded
  if (window.location.pathname.includes('/submit_test') || window.location.pathname.includes('/test_result')) {
    localStorage.removeItem('exam_answers_cache');
    localStorage.removeItem('exam_flagged_cache');
  }
})();
