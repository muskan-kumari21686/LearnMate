/* ═══════════════════════════════════════════════════════════════════════════
   LearnMate — Frontend JavaScript
   Dark mode · Chat · Enroll · Progress · Assessment · Roadmap · Utils
   ═══════════════════════════════════════════════════════════════════════════ */

'use strict';

/* ── Helpers ────────────────────────────────────────────────────────────── */

function getCsrfToken() {
  // Primary: meta tag injected in base.html on every page
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta && meta.content) return meta.content;
  // Fallback: hidden input inside a form
  const input = document.querySelector('input[name="csrf_token"]');
  if (input && input.value) return input.value;
  console.warn('[LearnMate] CSRF token not found — POST requests will be rejected.');
  return '';
}

async function apiFetch(url, options = {}) {
  const defaults = {
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
  };
  const res = await fetch(url, { ...defaults, ...options, headers: { ...defaults.headers, ...(options.headers || {}) } });
  return res;
}

function showToast(message, type = 'info', duration = 3500) {
  let container = document.querySelector('.lm-toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'lm-toast-container';
    document.body.appendChild(container);
  }
  const icons = { success: '✅', danger: '❌', info: 'ℹ️', warning: '⚠️' };
  const toast = document.createElement('div');
  toast.className = `lm-toast ${type}`;
  toast.textContent = `${icons[type] || ''} ${message}`;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity .3s'; setTimeout(() => toast.remove(), 350); }, duration);
}

function autoResizeTextarea(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 140) + 'px';
}

function renderMarkdown(text) {
  if (typeof marked === 'undefined') return text.replace(/\n/g, '<br>');
  try {
    marked.setOptions({ breaks: true, gfm: true });
    return marked.parse(text);
  } catch (_) {
    return text.replace(/\n/g, '<br>');
  }
}

/* ── Dark Mode ──────────────────────────────────────────────────────────── */

(function initTheme() {
  const saved = localStorage.getItem('lm-theme') || 'light';
  document.documentElement.setAttribute('data-bs-theme', saved);
  updateThemeIcon(saved);
})();

function updateThemeIcon(theme) {
  const icon = document.getElementById('themeIcon');
  if (!icon) return;
  icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
}

document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('themeToggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-bs-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-bs-theme', next);
      localStorage.setItem('lm-theme', next);
      updateThemeIcon(next);
    });
  }
});

/* ── Password Toggle ────────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.lm-toggle-pw').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = document.getElementById(btn.dataset.target);
      if (!target) return;
      const isPassword = target.type === 'password';
      target.type = isPassword ? 'text' : 'password';
      btn.querySelector('i').className = isPassword ? 'bi bi-eye-slash-fill' : 'bi bi-eye-fill';
    });
  });
});

/* ── Chat ───────────────────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  const chatMessages = document.getElementById('chatMessages');
  const chatInput    = document.getElementById('chatInput');
  const sendBtn      = document.getElementById('sendBtn');
  const typingIndicator = document.getElementById('typingIndicator');

  if (!chatMessages || !chatInput) return;

  // Scroll to bottom on load
  scrollChatToBottom();

  // Render any existing markdown messages
  document.querySelectorAll('.lm-markdown').forEach(el => {
    el.innerHTML = renderMarkdown(el.textContent);
  });

  // Auto-resize textarea
  chatInput.addEventListener('input', () => autoResizeTextarea(chatInput));

  // Send on Enter (Shift+Enter for new line)
  chatInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  sendBtn && sendBtn.addEventListener('click', sendMessage);

  // Suggestion buttons
  document.querySelectorAll('.lm-suggestion-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      chatInput.value = btn.dataset.msg || '';
      chatInput.focus();
      autoResizeTextarea(chatInput);
      // Close mobile offcanvas if open
      const offcanvas = document.getElementById('mobileSidebar');
      if (offcanvas) {
        const bsOffcanvas = bootstrap.Offcanvas.getInstance(offcanvas);
        if (bsOffcanvas) bsOffcanvas.hide();
      }
    });
  });

  // Clear chat
  ['clearChatBtn', 'clearChatMobile'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('click', clearChat);
  });

  async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    // Append user message
    appendMessage('user', message);
    chatInput.value = '';
    autoResizeTextarea(chatInput);
    sendBtn && (sendBtn.disabled = true);
    showTyping();

    try {
      const res = await apiFetch('/chat/send', {
        method: 'POST',
        body: JSON.stringify({ message }),
      });
      hideTyping();
      if (res.ok) {
        const data = await res.json();
        appendMessage('assistant', data.reply);
      } else {
        appendMessage('assistant', '⚠️ Something went wrong. Please try again.');
      }
    } catch (_) {
      hideTyping();
      appendMessage('assistant', '⚠️ Network error. Please check your connection.');
    } finally {
      sendBtn && (sendBtn.disabled = false);
      chatInput.focus();
    }
  }

  function appendMessage(role, content) {
    const isUser = role === 'user';
    const wrapper = document.createElement('div');
    wrapper.className = `lm-msg lm-msg-${role}`;

    const avatarHtml = isUser
      ? `<div class="lm-msg-avatar lm-user-avatar">${document.querySelector('.lm-avatar-circle')?.textContent || 'U'}</div>`
      : `<div class="lm-msg-avatar"><i class="bi bi-robot"></i></div>`;

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const contentHtml = isUser
      ? content.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
      : renderMarkdown(content);

    wrapper.innerHTML = `
      ${!isUser ? avatarHtml : ''}
      <div class="lm-msg-bubble">
        <div class="lm-msg-content lm-markdown">${contentHtml}</div>
        <div class="lm-msg-time">${timeStr}</div>
      </div>
      ${isUser ? avatarHtml : ''}
    `;

    // Insert before typing indicator
    const typing = document.getElementById('typingIndicator');
    if (typing) {
      chatMessages.insertBefore(wrapper, typing);
    } else {
      chatMessages.appendChild(wrapper);
    }

    // Animate in
    wrapper.style.opacity = '0';
    wrapper.style.transform = 'translateY(10px)';
    wrapper.style.transition = 'opacity .25s, transform .25s';
    requestAnimationFrame(() => {
      wrapper.style.opacity = '1';
      wrapper.style.transform = 'translateY(0)';
    });

    scrollChatToBottom();
  }

  function showTyping() {
    typingIndicator && typingIndicator.classList.remove('d-none');
    scrollChatToBottom();
  }
  function hideTyping() {
    typingIndicator && typingIndicator.classList.add('d-none');
  }
  function scrollChatToBottom() {
    if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  async function clearChat() {
    if (!confirm('Clear all chat history?')) return;
    await apiFetch('/chat/clear', { method: 'POST' });
    // Remove all messages except the typing indicator
    Array.from(chatMessages.children).forEach(child => {
      if (child.id !== 'typingIndicator') child.remove();
    });
    showToast('Chat cleared.', 'info');
  }
});

/* ── Course Enroll ──────────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.lm-enroll-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const courseId = btn.dataset.courseId;
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

      try {
        const res = await apiFetch(`/courses/${courseId}/enroll`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'enrolled') {
          btn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Enrolled!';
          btn.className = 'btn lm-btn-sm w-100';
          btn.style.background = 'rgba(34,197,94,.15)';
          btn.style.color = 'var(--lm-green)';
          showToast(`Enrolled in "${data.course_title}" — good luck! 🚀`, 'success');
        } else if (data.status === 'already_enrolled') {
          btn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Already enrolled';
          btn.disabled = true;
          showToast('You are already enrolled in this course.', 'info');
        }
      } catch (_) {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-plus-circle me-1"></i>Enroll Now';
        showToast('Enroll failed. Please try again.', 'danger');
      }
    });
  });
});

/* ── Course Unenroll ─────────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.lm-unenroll-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('Remove this course from your enrollments?')) return;
      const courseId = btn.dataset.courseId;
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

      try {
        const res = await apiFetch(`/courses/${courseId}/unenroll`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'unenrolled') {
          showToast('Enrollment removed.', 'info');
          // Remove the whole card from the DOM
          const card = btn.closest('.col-md-6, .col-xl-4');
          if (card) {
            card.style.transition = 'opacity .3s';
            card.style.opacity = '0';
            setTimeout(() => card.remove(), 320);
          }
        }
      } catch (_) {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-trash3 me-1"></i>Remove Enrollment';
        showToast('Failed to remove enrollment. Please try again.', 'danger');
      }
    });
  });
});

/* ── Progress Modal ─────────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  const modal        = document.getElementById('progressModal');
  const range        = document.getElementById('progressRange');
  const display      = document.getElementById('progressDisplay');
  const courseIdInput= document.getElementById('modalCourseId');
  const saveBtn      = document.getElementById('saveProgressBtn');

  if (!modal) return;
  const bsModal = new bootstrap.Modal(modal);

  range && range.addEventListener('input', () => {
    display.textContent = `${range.value}%`;
  });

  document.querySelectorAll('.lm-update-progress').forEach(btn => {
    btn.addEventListener('click', () => {
      const courseId = btn.dataset.courseId;
      const current  = parseInt(btn.dataset.current || 0);
      courseIdInput.value = courseId;
      range.value = current;
      display.textContent = `${current}%`;
      bsModal.show();
    });
  });

  saveBtn && saveBtn.addEventListener('click', async () => {
    const courseId = courseIdInput.value;
    const pct = parseInt(range.value);
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving…';

    try {
      const res = await apiFetch(`/courses/${courseId}/progress`, {
        method: 'POST',
        body: JSON.stringify({ progress_pct: pct }),
      });
      const data = await res.json();
      bsModal.hide();
      if (data.status === 'completed') {
        showToast(`🎉 Course completed! +${data.xp_awarded} XP earned!`, 'success', 5000);
        setTimeout(() => location.reload(), 2000);
      } else {
        showToast(`Progress updated to ${pct}%`, 'success');
        setTimeout(() => location.reload(), 1200);
      }
    } catch (_) {
      showToast('Failed to update progress.', 'danger');
    } finally {
      saveBtn.disabled = false;
      saveBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i>Save Progress';
    }
  });
});

/* ── Roadmap Generator ──────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  const generateBtn  = document.getElementById('generateRoadmapBtn');
  const createBtn    = document.getElementById('createRoadmapBtn');
  const generatePanel= document.getElementById('generatePanel');
  const loading      = document.getElementById('roadmapLoading');
  const display      = document.getElementById('roadmapDisplay');
  const empty        = document.getElementById('roadmapEmpty');

  if (!createBtn) return;

  generateBtn && generateBtn.addEventListener('click', () => {
    generatePanel.style.display = '';
    generatePanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  createBtn.addEventListener('click', async () => {
    const careerGoal = document.getElementById('rmCareerGoal')?.value.trim() || '';
    const skillLevel = document.getElementById('rmSkillLevel')?.value || 'beginner';
    const interests  = document.getElementById('rmInterests')?.value.trim() || '';

    if (!careerGoal) {
      showToast('Please enter a career goal.', 'warning');
      return;
    }

    generatePanel.style.display = 'none';
    empty && (empty.style.display = 'none');
    loading && loading.classList.remove('d-none');
    display && display.classList.add('d-none');

    try {
      const res = await apiFetch('/roadmap/generate', {
        method: 'POST',
        body: JSON.stringify({ career_goal: careerGoal, skill_level: skillLevel, interests }),
      });
      const data = await res.json();
      loading && loading.classList.add('d-none');

      if (data.roadmap) {
        renderRoadmap(data.roadmap);
        display && display.classList.remove('d-none');
        display && display.scrollIntoView({ behavior: 'smooth' });
        showToast('Roadmap generated! 🗺️', 'success');
      } else {
        showToast('Failed to generate roadmap. Please try again.', 'danger');
        generatePanel.style.display = '';
      }
    } catch (_) {
      loading && loading.classList.add('d-none');
      showToast('Network error. Please try again.', 'danger');
      generatePanel.style.display = '';
    }
  });

  // If roadmap data is already available from server render, enhance it
  if (typeof ROADMAP_DATA !== 'undefined' && ROADMAP_DATA) {
    // Already rendered by Jinja — nothing to do
  }
});

function renderRoadmap(rm) {
  const display = document.getElementById('roadmapDisplay');
  if (!display) return;

  const levelColors = { Foundation: 'green', 'Core Skills': 'blue', Intermediate: 'orange', Advanced: 'purple', Expert: 'red' };

  let html = `
    <div class="lm-roadmap-header mb-4">
      <h3 class="fw-800">${escHtml(rm.title || '')}</h3>
      <p class="text-muted"><i class="bi bi-bullseye me-1"></i>Goal: <strong>${escHtml(rm.career_goal || '')}</strong></p>
      <div class="d-flex gap-3 flex-wrap">
        <span class="lm-meta-badge"><i class="bi bi-calendar3 me-1"></i>${rm.total_estimated_weeks || '?'} weeks total</span>
        <span class="lm-meta-badge"><i class="bi bi-layers me-1"></i>${(rm.stages || []).length} stages</span>
      </div>
    </div>
    <div class="lm-roadmap-stages">`;

  (rm.stages || []).forEach((stage, idx) => {
    const color = levelColors[stage.stage_name] || 'accent';
    const isLast = idx === (rm.stages.length - 1);
    html += `
      <div class="lm-stage-card">
        <div class="lm-stage-connector">
          <div class="lm-stage-dot ${idx === 0 ? 'lm-dot-active' : ''}"></div>
          ${!isLast ? '<div class="lm-stage-line"></div>' : ''}
        </div>
        <div class="lm-stage-body ${idx === 0 ? 'lm-stage-active' : ''}">
          <div class="d-flex align-items-start justify-content-between flex-wrap gap-2 mb-3">
            <div>
              <span class="lm-stage-num">Stage ${idx + 1}</span>
              <h5 class="fw-800 mb-0">${escHtml(stage.stage_name || '')}</h5>
              <p class="text-muted small mb-0">${escHtml(stage.description || '')}</p>
            </div>
            <span class="lm-meta-badge"><i class="bi bi-clock me-1"></i>~${stage.estimated_weeks || '?'} weeks</span>
          </div>`;

    if (stage.topics && stage.topics.length) {
      html += `<div class="mb-3">
        <h6 class="fw-700 small text-uppercase text-muted mb-2">📚 Topics to Cover</h6>
        <div class="d-flex flex-wrap gap-2">
          ${stage.topics.map(t => `<span class="lm-topic-tag">${escHtml(t)}</span>`).join('')}
        </div></div>`;
    }

    html += `<div class="row g-3">`;

    if (stage.resources && stage.resources.length) {
      html += `<div class="col-md-4">
        <h6 class="fw-700 small text-uppercase text-muted mb-2">🔗 Resources</h6>
        <ul class="lm-resource-list">${stage.resources.map(r =>
          `<li><span class="lm-resource-type lm-type-${escHtml(r.type || 'course')}">${escHtml(r.type || 'course')}</span>
           ${escHtml(r.title || '')}
           ${r.provider ? `<span class="text-muted small"> · ${escHtml(r.provider)}</span>` : ''}
           ${r.free ? '<span class="lm-free-badge">FREE</span>' : ''}</li>`
        ).join('')}</ul></div>`;
    }

    if (stage.projects && stage.projects.length) {
      html += `<div class="col-md-4">
        <h6 class="fw-700 small text-uppercase text-muted mb-2">💻 Projects</h6>
        <ul class="lm-project-list">${stage.projects.map(p =>
          `<li><i class="bi bi-code-slash me-1 text-accent"></i>${escHtml(p)}</li>`
        ).join('')}</ul></div>`;
    }

    if (stage.certifications && stage.certifications.length) {
      html += `<div class="col-md-4">
        <h6 class="fw-700 small text-uppercase text-muted mb-2">🏆 Certifications</h6>
        <ul class="lm-cert-list">${stage.certifications.map(c =>
          `<li><i class="bi bi-award-fill me-1 text-warning"></i>${escHtml(c)}</li>`
        ).join('')}</ul></div>`;
    }

    html += `</div>`;

    if (stage.milestone) {
      html += `<div class="lm-milestone-box mt-3">
        <i class="bi bi-flag-fill me-2 text-success"></i>
        <strong>Milestone:</strong> ${escHtml(stage.milestone)}
      </div>`;
    }

    html += `</div></div>`;
  });

  html += `</div>`;

  if (rm.career_outcomes && rm.career_outcomes.length) {
    html += `<div class="lm-roadmap-outcomes mt-4">
      <h5 class="fw-800 mb-3"><i class="bi bi-briefcase-fill me-2 text-accent"></i>Career Outcomes</h5>
      <div class="d-flex flex-wrap gap-2">
        ${rm.career_outcomes.map(o => `<span class="lm-outcome-tag">${escHtml(o)}</span>`).join('')}
      </div></div>`;
  }

  if (rm.next_steps) {
    html += `<div class="lm-next-steps-card mt-4">
      <h6 class="fw-700"><i class="bi bi-rocket-takeoff me-2 text-accent"></i>Next Steps</h6>
      <p class="mb-0">${escHtml(rm.next_steps)}</p>
    </div>`;
  }

  display.innerHTML = html;
}

function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

/* ── Skill Assessment Quiz ──────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  const domainSelector = document.getElementById('domainSelector');
  const quizArea       = document.getElementById('quizArea');
  const resultsArea    = document.getElementById('resultsArea');
  if (!domainSelector) return;

  let currentDomain    = '';
  let questions        = [];
  let currentIndex     = 0;
  let userAnswers      = {};

  document.querySelectorAll('.lm-start-quiz').forEach(btn => {
    btn.addEventListener('click', async () => {
      currentDomain = btn.dataset.domain;
      try {
        const res = await fetch(`/assessment/quiz/${encodeURIComponent(currentDomain)}`);
        const data = await res.json();
        questions = data.questions || [];
        currentIndex = 0;
        userAnswers = {};

        domainSelector.classList.add('d-none');
        quizArea.classList.remove('d-none');
        document.getElementById('quizDomainTitle').textContent = `${currentDomain} Assessment`;
        renderQuestion();
      } catch (_) {
        showToast('Failed to load quiz. Please try again.', 'danger');
      }
    });
  });

  document.getElementById('backToDomains')?.addEventListener('click', () => {
    quizArea.classList.add('d-none');
    domainSelector.classList.remove('d-none');
  });

  document.getElementById('prevQuestionBtn')?.addEventListener('click', () => {
    if (currentIndex > 0) { currentIndex--; renderQuestion(); }
  });

  document.getElementById('nextQuestionBtn')?.addEventListener('click', async () => {
    if (currentIndex < questions.length - 1) {
      currentIndex++;
      renderQuestion();
    } else {
      await submitQuiz();
    }
  });

  document.getElementById('retakeBtn')?.addEventListener('click', () => {
    resultsArea.classList.add('d-none');
    domainSelector.classList.remove('d-none');
  });

  function renderQuestion() {
    const q = questions[currentIndex];
    const total = questions.length;
    const pct = Math.round(((currentIndex + 1) / total) * 100);

    document.getElementById('quizProgress').textContent = `Question ${currentIndex + 1} of ${total}`;
    document.getElementById('quizProgressBar').style.width = `${pct}%`;

    const selected = userAnswers[currentIndex];
    const html = `
      <div class="lm-question-card">
        <p class="fw-700 mb-4 fs-6">${escHtml(q.q)}</p>
        ${q.options.map((opt, i) => `
          <button class="lm-option-btn ${selected === i ? 'selected' : ''}"
                  data-idx="${i}" type="button">
            <span class="fw-700 me-2">${String.fromCharCode(65 + i)}.</span>${escHtml(opt)}
          </button>`).join('')}
      </div>`;

    document.getElementById('questionContainer').innerHTML = html;

    document.querySelectorAll('.lm-option-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        userAnswers[currentIndex] = parseInt(btn.dataset.idx);
        document.querySelectorAll('.lm-option-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
      });
    });

    document.getElementById('prevQuestionBtn').disabled = currentIndex === 0;
    const nextBtn = document.getElementById('nextQuestionBtn');
    nextBtn.innerHTML = currentIndex === total - 1
      ? 'Submit <i class="bi bi-send-fill ms-1"></i>'
      : 'Next <i class="bi bi-arrow-right ms-1"></i>';
  }

  async function submitQuiz() {
    try {
      const res = await apiFetch('/assessment/submit', {
        method: 'POST',
        body: JSON.stringify({ domain: currentDomain, answers: userAnswers }),
      });
      const data = await res.json();

      quizArea.classList.add('d-none');
      resultsArea.classList.remove('d-none');

      document.getElementById('scoreCircle').textContent = `${data.score}%`;
      document.getElementById('resultLevel').textContent = `Level: ${data.level.charAt(0).toUpperCase() + data.level.slice(1)}`;
      document.getElementById('resultSubtext').textContent =
        data.score >= 80 ? '🌟 Excellent work! You\'re advanced in this domain.'
        : data.score >= 50 ? '👍 Good effort! You\'re at an intermediate level.'
        : '💪 Keep learning! You\'re at the beginner level.';

      const feedbackEl = document.getElementById('feedbackContent');
      if (feedbackEl) feedbackEl.innerHTML = renderMarkdown(data.feedback || '');

      // Detailed results
      const detailEl = document.getElementById('detailedResults');
      if (detailEl && data.results) {
        let detailHtml = '<h6 class="fw-700 mb-3">Detailed Results</h6>';
        data.results.forEach((r, i) => {
          const icon = r.correct ? '✅' : '❌';
          detailHtml += `
            <div class="mb-3 p-3 rounded" style="background:${r.correct ? 'rgba(34,197,94,.08)' : 'rgba(239,68,68,.08)'}; border:1px solid ${r.correct ? 'rgba(34,197,94,.2)' : 'rgba(239,68,68,.2)'}">
              <div class="fw-600 mb-1">${icon} Q${i+1}: ${escHtml(r.question)}</div>
              <div class="small text-muted">Your answer: <strong>${escHtml(r.user_answer)}</strong></div>
              ${!r.correct ? `<div class="small text-success">Correct: <strong>${escHtml(r.correct_answer)}</strong></div>` : ''}
            </div>`;
        });
        detailEl.innerHTML = detailHtml;
      }

      showToast(`Assessment complete! +50 XP earned 🎯`, 'success', 4000);
    } catch (_) {
      showToast('Failed to submit. Please try again.', 'danger');
    }
  }
});

/* ── Profile Form ───────────────────────────────────────────────────────── */
// profile.html inline script handles this, but expose showToast globally
window.showToast = showToast;
window.getCsrfToken = getCsrfToken;
