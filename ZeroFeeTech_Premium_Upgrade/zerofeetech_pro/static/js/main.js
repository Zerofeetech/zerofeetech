(() => {
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
  const toolNames = {
    website: 'Website builder brief', app: 'App planner', software: 'Software architect', ai: 'AI project planner',
    automation: 'Automation mapper', uiux: 'UI/UX designer', graphic: 'Graphic design brief', logo: 'Logo concept lab',
    code: 'Coding assistant', social: 'Social content planner', email: 'Professional email', business: 'Business launch planner'
  };
  const placeholders = {
    website: 'Example: A clean website for a local bakery with a menu, opening hours, location, and contact form. It should look great on phones and computers.',
    app: 'Example: A habit-tracking app for students with a daily checklist, streak view, reminders, and a simple progress screen.',
    software: 'Example: A desktop tool that organizes PDF study notes by subject and lets users search them quickly.',
    ai: 'Example: An AI study helper that explains difficult Japanese grammar in simple Nepali and gives practice questions.',
    automation: 'Example: Every time I receive a project enquiry, collect the key details, categorize the request, and prepare a reply draft for review.',
    uiux: 'Example: A mobile-first learning dashboard for beginners, with lessons, progress, saved items, and a calm visual design.',
    graphic: 'Example: A promotional poster for a free coding workshop, aimed at students, with clear date, location, and signup details.',
    logo: 'Example: A modern, simple logo for a technology studio called ZeroFeeTech. Use an abstract Z mark, deep navy, lime accent, and clean typography.',
    code: 'Example: Build a responsive to-do app with add, edit, complete, delete, and local storage. Use plain HTML, CSS, and JavaScript and explain how to run it.',
    social: 'Example: A 7-day launch content plan for a free website that helps beginners explore coding, design, AI, and automation.',
    email: 'Example: Write a polite email asking a client for their project requirements and preferred deadline.',
    business: 'Example: Launch a free-first online toolkit for students and small businesses. I have limited budget and want to test demand before adding paid services.'
  };
  const tabs = [...document.querySelectorAll('.studio-tab')];
  const toolForm = document.getElementById('toolForm');
  const promptInput = document.getElementById('toolPrompt');
  const charCount = document.getElementById('charCount');
  const toolTitle = document.getElementById('toolTitle');
  const output = document.getElementById('toolOutput');
  const outputTitle = document.getElementById('outputTitle');
  const outputText = document.getElementById('outputText');
  const outputNotice = document.getElementById('outputNotice');
  const generateBtn = document.getElementById('generateBtn');
  let selectedTool = 'website';
  let latestPrompt = '';

  function chooseTool(name, shouldScroll = false) {
    if (!toolNames[name]) return;
    selectedTool = name;
    tabs.forEach(tab => {
      const active = tab.dataset.tool === name;
      tab.classList.toggle('active', active);
      tab.setAttribute('aria-pressed', String(active));
    });
    if (toolTitle) toolTitle.textContent = toolNames[name];
    if (promptInput && !promptInput.value.trim()) promptInput.placeholder = placeholders[name] || '';
    if (output) output.hidden = true;
    if (shouldScroll) document.getElementById('studio')?.scrollIntoView({behavior: 'smooth'});
  }
  tabs.forEach(tab => tab.addEventListener('click', () => chooseTool(tab.dataset.tool)));
  document.querySelectorAll('[data-preset]').forEach(link => link.addEventListener('click', () => {
    const key = link.dataset.preset;
    const mapped = key === 'automation' ? 'automation' : key === 'uiux' ? 'uiux' : 'website';
    chooseTool(mapped);
  }));
  if (promptInput && charCount) promptInput.addEventListener('input', () => charCount.textContent = `${promptInput.value.length} / 3000`);
  if (toolForm) toolForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const prompt = promptInput.value.trim();
    if (prompt.length < 4) return;
    generateBtn.disabled = true; generateBtn.textContent = 'Preparing…';
    try {
      const res = await fetch('/api/tool', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({tool: selectedTool, prompt})});
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Could not prepare the prompt.');
      latestPrompt = data.result;
      outputTitle.textContent = data.title;
      outputText.textContent = data.result;
      outputNotice.textContent = data.notice;
      output.hidden = false;
      output.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    } catch (error) {
      output.hidden = false; outputTitle.textContent = 'Could not prepare this prompt'; outputNotice.textContent = error.message; outputText.textContent = '';
    } finally { generateBtn.disabled = false; generateBtn.innerHTML = 'Create my prompt <span>↗</span>'; }
  });
  document.getElementById('clearTool')?.addEventListener('click', () => {
    if (promptInput) promptInput.value = '';
    if (charCount) charCount.textContent = '0 / 3000';
    if (output) output.hidden = true;
    latestPrompt = '';
  });
  document.getElementById('copyPrompt')?.addEventListener('click', async (event) => {
    if (!latestPrompt) return;
    const button = event.currentTarget;
    try { await navigator.clipboard.writeText(latestPrompt); button.textContent = 'Copied ✓'; }
    catch { const range = document.createRange(); range.selectNodeContents(outputText); const sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(range); button.textContent = 'Select and copy'; }
    setTimeout(() => button.textContent = 'Copy prompt', 1800);
  });
  document.getElementById('savePrompt')?.addEventListener('click', async () => {
    const message = document.getElementById('saveMessage');
    if (!latestPrompt) return;
    const loggedIn = document.body.dataset.loggedIn === 'true';
    if (!loggedIn) { message.innerHTML = 'Please <a href="/login">log in</a> to save prompts.'; return; }
    try {
      const res = await fetch('/api/save', {method: 'POST', headers: {'Content-Type':'application/json','X-CSRF-Token':csrf}, body: JSON.stringify({title: outputTitle.textContent, kind: selectedTool, content: latestPrompt})});
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Could not save.');
      message.textContent = 'Saved to your workspace ✓';
    } catch (e) { message.textContent = e.message; }
  });
  // Login state is rendered by the server on the body element.

  document.querySelectorAll('[data-copy]').forEach(button => button.addEventListener('click', async () => {
    const content = button.dataset.copy || '';
    try { await navigator.clipboard.writeText(content); button.textContent = 'Copied ✓'; }
    catch { button.textContent = 'Copy unavailable'; }
    setTimeout(() => button.textContent = 'Copy ↗', 1600);
  }));
})();
