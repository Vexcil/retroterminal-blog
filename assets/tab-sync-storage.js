(function(root) {
  'use strict';
  const clone = value => value == null ? null : JSON.parse(JSON.stringify(value));
  function canonicalFile(file) {
    return decodeURIComponent(new URL(file, 'https://retroterminal.net').pathname);
  }
  function validSync(value) {
    if (!value || value.version !== 1 || !/^[\w-]{11}$/.test(value.videoId || '') ||
        !Number.isInteger(value.barCount) || value.barCount < 1 || value.barCount > 20000 ||
        !Array.isArray(value.points) || value.points.length > 20001) return false;
    let previous = -1;
    return value.points.every(p => {
      if (!p || !Number.isInteger(p.barIndex) || p.barIndex < 0 || p.barIndex >= 20000 ||
          !Number.isInteger(p.barOccurence) || p.barOccurence < 0 || p.barOccurence >= 20000 ||
          ![0,1].includes(p.barPosition) || !Number.isFinite(p.millisecondOffset) ||
          p.millisecondOffset < 0 || p.millisecondOffset > 86400000 || p.millisecondOffset <= previous) return false;
      previous = p.millisecondOffset;
      return true;
    });
  }
  function createStore(options) {
    let data = null, revision = null, dirty = false, conflict = false, change = 0;
    let loading, flushing, timer;
    const status = (state, error) => options.onStatus?.(state, error);
    function cache() {
      try { options.writeLocal({version:2, sync:clone(data), revision, pending:dirty}); } catch (_) { /* The server remains authoritative. */ }
    }
    function publish() { options.onData?.(clone(data)); }
    function save(value) {
      if (revision === null) throw new Error('Wait for saved timing to load from the server, then try again.');
      if (conflict) throw new Error('Another device changed this tab. Export your local timing or load the server version.');
      if (!validSync(value)) throw new Error('The video timing is invalid.');
      data = clone(value); dirty = true; change++; cache(); status('saving');
      clearTimeout(timer); timer = setTimeout(() => flush().catch(() => {}), options.delay ?? 250);
    }
    async function flush() {
      clearTimeout(timer);
      if (flushing) return flushing;
      if (!dirty) return;
      if (conflict || revision === null) throw new Error('Load the server version before saving again.');
      flushing = (async () => {
        while (dirty) {
          const stamp = change;
          status('saving');
          let result;
          try {
            result = await options.request('POST', {file:options.file, revision, sync:clone(data)});
          } catch (error) {
            if (error.status === 409) { conflict = true; status('conflict', error); }
            else status('error', error);
            throw error;
          }
          revision = result.revision;
          if (stamp === change) dirty = false;
          cache();
        }
        status('saved');
      })();
      try { return await flushing; } finally { flushing = null; if(!dirty || conflict) clearTimeout(timer); }
    }
    async function load(discardLocal = false) {
      if (loading) return loading;
      if ((dirty || flushing || conflict) && !discardLocal) return clone(data);
      loading = (async () => {
        status('loading');
        let local;
        try { local = options.readLocal(); } catch (_) { local = null; }
        try {
          const result = await options.request('GET', {file:options.file});
          if (!Number.isInteger(result.revision) || result.revision < 0 || (result.sync !== null && !validSync(result.sync)))
            throw new Error('The server returned invalid timing.');
          const draft = local?.version === 2 && local.pending && validSync(local.sync);
          const legacy = validSync(local) ? local : null;
          revision = result.revision;
          if (!discardLocal && draft && local.revision !== revision) {
            data = clone(local.sync); dirty = true; conflict = true;
            publish(); status('conflict'); return clone(data);
          }
          data = clone(result.sync); dirty = false; conflict = false;
          if (!discardLocal && ((draft && local.revision === revision) || (!data && legacy))) {
            data = clone(draft ? local.sync : legacy);
            save(data);
          } else { cache(); status(data ? 'saved' : 'empty'); }
          publish(); return clone(data);
        } catch (error) {
          if (revision === null) {
            data = clone(validSync(local?.sync) ? local.sync : validSync(local) ? local : null);
            publish();
          }
          status('error', error); throw error;
        }
      })();
      try { return await loading; } finally { loading = null; }
    }
    return {
      load, save, flush,
      get dirty() { return dirty; },
      get conflict() { return conflict; },
      get readyForEdits() { return revision !== null && !conflict; },
      async ready() {
        if (loading) await loading;
        if (revision === null) throw new Error('Saved timing could not load. Use Retry server save before editing.');
        if (conflict) throw new Error('Another device changed this tab. Export your local timing or load the server version.');
      },
      async retry() { if (revision === null) return load(); if (conflict) return load(true); return dirty ? flush() : load(); }
    };
  }
  const core = {canonicalFile, validSync, createStore};
  if (typeof module !== 'undefined' && module.exports) module.exports = core;
  root.RetroTabStorage = core;
})(typeof window !== 'undefined' ? window : globalThis);
