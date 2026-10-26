(function () {
  document.querySelectorAll('.recipe-copy-link').forEach(function (button) {
    const share = button.closest('.recipe-share');
    const status = share.querySelector('.recipe-copy-status');
    const fallback = share.querySelector('.recipe-share-fallback');

    button.addEventListener('click', async function () {
      const url = button.dataset.recipeLink;
      status.textContent = '';
      fallback.hidden = true;
      try {
        await navigator.clipboard.writeText(url);
      } catch (error) {
        fallback.hidden = false;
        fallback.focus();
        fallback.select();
        fallback.setSelectionRange(0, fallback.value.length);
        status.textContent = 'Select and copy this short link.';
        return;
      }
      status.textContent = 'Link copied!';
    });
  });
})();
