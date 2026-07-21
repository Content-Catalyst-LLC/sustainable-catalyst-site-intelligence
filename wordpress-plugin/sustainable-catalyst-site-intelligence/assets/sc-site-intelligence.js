(function () {
  'use strict';

  const cfg = window.SCSiteIntelligence || {};
  const headers = {'Content-Type': 'application/json'};
  if (cfg.restNonce) headers['X-WP-Nonce'] = cfg.restNonce;

  function pushDataLayer(eventName, params) {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(Object.assign({event: eventName}, params || {}));
  }

  function backendEvent(eventName, params) {
    const payload = Object.assign({
      event_name: eventName,
      page_path: window.location.pathname,
      page_title: document.title,
      client_time: new Date().toISOString(),
      metadata: {
        href: params && params.href ? params.href : '',
        version: cfg.version || '1.5.0'
      }
    }, params || {});

    pushDataLayer(eventName, payload);

    if (!cfg.restBase || !cfg.enableEventBridge) {
      return;
    }

    fetch(cfg.restBase + '/event', {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(payload),
      keepalive: true
    }).catch(function () {});
  }

  function classifyLink(anchor) {
    const explicit = anchor.getAttribute('data-scsi-event');
    if (explicit) return explicit;
    const href = anchor.getAttribute('href') || '';
    const text = (anchor.textContent || '').toLowerCase();
    if (!href) return null;
    if (href.indexOf('github.com') !== -1 || text.indexOf('github repository') !== -1 || text.indexOf('full github') !== -1) return 'sc_repository_click';
    if (href.indexOf('/workbench') !== -1 || text.indexOf('workbench') !== -1 || text.indexOf('calculator') !== -1) return 'sc_workbench_open';
    if (href.indexOf('/research-librarian') !== -1 || text.indexOf('research librarian') !== -1) return 'sc_research_librarian_open';
    if (href.indexOf('/decision-studio') !== -1 || text.indexOf('decision studio') !== -1) return 'sc_decision_studio_open';
    if (href.indexOf('/research-library') !== -1 || href.indexOf('/library') !== -1 || text.indexOf('research library') !== -1) return 'sc_library_nav';
    if (anchor.closest('[data-scsi-pathway], [aria-label*="article" i], .series-strip, .related, .toc, nav')) return 'sc_pathway_continue';
    return null;
  }

  function setupActivePageLinks() {
    const current = normalizePath(window.location.pathname || '/');
    document.querySelectorAll('.ccp-site-intelligence-public a[href], .ccp-platform-current a[href], .cch-home-current a[href], .scsi-public-nav-row a[href]').forEach(function (anchor) {
      const href = anchor.getAttribute('href') || '';
      if (!href || href.charAt(0) === '#') return;
      const path = normalizePath(href);
      if (path === current) {
        anchor.classList.add('scsi-active-link');
        anchor.setAttribute('aria-current', 'page');
      }
    });
  }

  function setupClickTracking() {
    document.addEventListener('click', function (event) {
      const copyButton = event.target.closest ? event.target.closest('[data-scsi-copy]') : null;
      if (copyButton) {
        const value = copyButton.getAttribute('data-scsi-copy') || '';
        if (navigator.clipboard && value) {
          navigator.clipboard.writeText(value).then(function () { copyButton.textContent = 'Copied'; }).catch(function () {});
        }
        event.preventDefault();
        return;
      }
      const anchor = event.target.closest ? event.target.closest('a') : null;
      if (!anchor) return;
      const eventName = classifyLink(anchor);
      if (!eventName) return;
      backendEvent(eventName, {
        page_path: window.location.pathname,
        page_title: document.title,
        tool_id: anchor.getAttribute('data-scsi-tool-id') || undefined,
        pathway_id: anchor.getAttribute('data-scsi-pathway-id') || undefined,
        repository_url: eventName === 'sc_repository_click' ? anchor.href : undefined,
        metadata: {
          href: anchor.href,
          text: (anchor.textContent || '').trim().slice(0, 120),
          class_name: anchor.className || ''
        }
      });
    }, {capture: true});
  }

  function setupScrollTracking() {
    const thresholds = [25, 50, 75, 90];
    const seen = new Set();
    window.addEventListener('scroll', function () {
      const doc = document.documentElement;
      const scrollTop = window.scrollY || doc.scrollTop;
      const height = Math.max(1, doc.scrollHeight - window.innerHeight);
      const pct = Math.round((scrollTop / height) * 100);
      thresholds.forEach(function (threshold) {
        if (pct >= threshold && !seen.has(threshold)) {
          seen.add(threshold);
          backendEvent('sc_scroll_depth', {value: threshold});
        }
      });
    }, {passive: true});
  }

  function formatNumber(value) {
    const n = Number(value || 0);
    return n.toLocaleString(undefined, {maximumFractionDigits: 1});
  }

  function escapeHtml(value) {
    return String(value || '').replace(/[&<>'"]/g, function (ch) {
      return {'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[ch];
    });
  }

  function cleanErrorMessage(value, fallback) {
    let msg = String(value || '').trim();
    if (!msg) return fallback;
    if (/<!doctype|<html|cloudflare|bad gateway|cf-wrapper/i.test(msg)) {
      return 'Site Intelligence backend or site proxy returned a gateway error. The raw HTML error was suppressed; test the direct Render endpoint and redeploy if needed.';
    }
    msg = msg.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
    return msg.length > 280 ? msg.slice(0, 277) + '…' : msg;
  }

  function errorMessageFromResponse(data, fallback) {
    if (!data) return fallback;
    if (data.message) return cleanErrorMessage(data.message, fallback);
    if (data.detail) {
      if (typeof data.detail === 'string') return cleanErrorMessage(data.detail, fallback);
      if (data.detail.message) {
        let msg = data.detail.message;
        if (data.detail.error_type || data.detail.error_message) {
          msg += ' (' + [data.detail.error_type, data.detail.error_message].filter(Boolean).join(': ') + ')';
        }
        return cleanErrorMessage(msg, fallback);
      }
    }
    if (data.code && data.message) return cleanErrorMessage(data.code + ': ' + data.message, fallback);
    return fallback;
  }

  function showError(root, message) {
    const safeMessage = cleanErrorMessage(message || 'Unable to load Site Intelligence backend.', 'Site Intelligence panel is temporarily unavailable.');
    const muted = root.querySelector('.scsi-muted');
    if (muted) muted.textContent = safeMessage;
    const out = root.querySelector('.scsi-output');
    if (out && !out.innerHTML) {
      out.innerHTML = '<div class="scsi-error-box"><strong>Panel unavailable</strong><small>' + escapeHtml(safeMessage) + '</small></div>';
    }
  }

  function fetchJson(url) {
    return fetch(url, {headers: headers}).then(function (r) {
      return r.text().then(function (text) {
        let data = null;
        try { data = text ? JSON.parse(text) : null; } catch (e) { data = {message: text}; }
        if (!r.ok || (data && data.code)) {
          throw new Error(errorMessageFromResponse(data, 'Site Intelligence request failed. HTTP ' + r.status));
        }
        return data || {};
      });
    });
  }

  function statusBadge(status) {
    const safe = (status || 'unmapped').toLowerCase();
    return '<span class="scsi-badge scsi-badge-' + escapeHtml(safe) + '">' + escapeHtml(safe) + '</span>';
  }

  function renderDashboard(root, data) {
    const totals = data.totals || {};
    const pages = data.top_pages || [];
    const recs = data.recommendations || [];
    const coverage = data.mapping_coverage || {};
    const readiness = data.conversion_readiness || {};
    root.querySelector('.scsi-muted').textContent = 'Source: ' + data.source + ' · Date range: ' + data.date_range.start_date + ' to ' + data.date_range.end_date;
    const out = root.querySelector('.scsi-output');
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid';
    [
      ['Views', totals.screen_page_views],
      ['Active users', totals.active_users],
      ['Repository clicks', totals.repository_clicks],
      ['Workbench events', totals.workbench_events],
      ['Depth score', totals.avg_institutional_depth_score],
      ['Conversion readiness', readiness.score || 0, '%'],
      ['Mapping coverage', coverage.mapping_coverage_rate || totals.mapping_coverage_rate, '%']
    ].forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat';
      card.innerHTML = '<strong>' + formatNumber(item[1]) + (item[2] || '') + '</strong><span>' + item[0] + '</span>';
      grid.appendChild(card);
    });
    out.appendChild(grid);

    const mapLine = document.createElement('p');
    mapLine.className = 'scsi-muted';
    mapLine.textContent = 'Registry: ' + formatNumber(data.registry_count) + ' explicit entries · ' + formatNumber(coverage.explicit_pages || totals.explicit_pages) + ' explicit GA4 pages · ' + formatNumber(coverage.inferred_pages || totals.inferred_pages) + ' inferred · ' + formatNumber(coverage.unmapped_pages || totals.unmapped_pages) + ' unmapped.';
    out.appendChild(mapLine);

    const h = document.createElement('h3');
    h.textContent = 'Top interpreted pages';
    out.appendChild(h);
    pages.slice(0, 8).forEach(function (page) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row';
      row.innerHTML = '<strong>' + escapeHtml(page.title || page.path) + '</strong><br>' +
        statusBadge(page.mapping_status) + '<span class="scsi-badge">' + escapeHtml(page.hub) + '</span> Depth ' + formatNumber(page.institutional_depth_score) + ' · Authority ' + formatNumber(page.authority_surface_score) +
        (page.mapping_reason ? '<br><small>' + escapeHtml(page.mapping_reason) + '</small>' : '');
      out.appendChild(row);
    });

    const list = document.createElement('ul');
    list.className = 'scsi-list';
    recs.forEach(function (rec) {
      const li = document.createElement('li');
      li.textContent = rec;
      list.appendChild(li);
    });
    out.appendChild(list);
  }

  function renderPage(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    if (!data.page) {
      muted.textContent = data.message || 'No page analytics available yet.';
      return;
    }
    const page = data.page;
    muted.textContent = 'Source: ' + data.source + ' · ' + page.hub + (page.article_map ? ' · ' + page.article_map : '') + ' · ' + page.mapping_status;
    out.innerHTML = '<div class="scsi-grid">' +
      '<div class="scsi-stat"><strong>' + formatNumber(page.screen_page_views) + '</strong><span>Views</span></div>' +
      '<div class="scsi-stat"><strong>' + formatNumber(page.institutional_depth_score) + '</strong><span>Depth score</span></div>' +
      '<div class="scsi-stat"><strong>' + formatNumber(page.authority_surface_score) + '</strong><span>Authority score</span></div>' +
      '<div class="scsi-stat"><strong>' + formatNumber(page.workbench_events) + '</strong><span>Workbench events</span></div>' +
      '</div><p class="scsi-muted">Mapping: ' + escapeHtml(page.mapping_reason || page.mapping_status) + '</p>';
    const list = document.createElement('ul');
    list.className = 'scsi-list';
    (page.recommendations || []).forEach(function (rec) {
      const li = document.createElement('li');
      li.textContent = rec;
      list.appendChild(li);
    });
    out.appendChild(list);
  }

  function renderUnmapped(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const coverage = data.mapping_coverage || {};
    muted.textContent = 'Source: ' + data.source + ' · Mapping coverage ' + formatNumber(coverage.mapping_coverage_rate) + '%';
    out.innerHTML = '';
    const suggestions = data.suggestions || [];
    if (!suggestions.length) {
      out.innerHTML = '<p class="scsi-muted">No unmapped or inferred pages were returned for this date range.</p>';
      return;
    }
    suggestions.forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-unmapped-row';
      const sample = item.sample_registry_item || {};
      row.innerHTML = '<strong>' + escapeHtml(item.title || item.path) + '</strong><br>' +
        '<code>' + escapeHtml(item.path) + '</code><br>' +
        '<span class="scsi-badge">' + escapeHtml(item.suggested_hub) + '</span>' +
        (item.suggested_article_map ? '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.suggested_article_map) + '</span>' : '') +
        '<small> Views ' + formatNumber(item.views) + ' · Confidence ' + formatNumber((item.confidence || 0) * 100) + '% · ' + escapeHtml(item.reason) + '</small>' +
        '<details><summary>Suggested registry JSON</summary><pre>' + escapeHtml(JSON.stringify(sample, null, 2)) + '</pre></details>';
      out.appendChild(row);
    });
  }

  function renderEvents(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const diagnostics = data.diagnostics || {};
    const readiness = diagnostics.readiness || {};
    muted.textContent = 'Source: ' + data.source + ' · Conversion readiness ' + formatNumber(readiness.score) + '% · ' + (readiness.status || 'unknown');
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid';
    [
      ['Readiness', readiness.score || 0, '%'],
      ['Tracked event total', diagnostics.tracked_event_total || 0],
      ['Active tracked events', diagnostics.tracked_events_active || 0],
      ['Visible GA4 events', diagnostics.visible_ga4_event_names || 0]
    ].forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat';
      card.innerHTML = '<strong>' + formatNumber(item[1]) + (item[2] || '') + '</strong><span>' + item[0] + '</span>';
      grid.appendChild(card);
    });
    out.appendChild(grid);
    (diagnostics.events || []).forEach(function (eventItem) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-event-row';
      row.innerHTML = '<strong>' + escapeHtml(eventItem.label) + '</strong><br>' +
        statusBadge(eventItem.status) + '<span class="scsi-badge">' + escapeHtml(eventItem.event_name) + '</span>' +
        '<small> Count ' + formatNumber(eventItem.event_count) + ' · Priority ' + escapeHtml(eventItem.priority) + '</small><br>' +
        '<small>' + escapeHtml(eventItem.next_action || '') + '</small>';
      out.appendChild(row);
    });
    const recList = document.createElement('ul');
    recList.className = 'scsi-list';
    (data.recommendations || []).forEach(function (rec) {
      const li = document.createElement('li');
      li.textContent = rec;
      recList.appendChild(li);
    });
    out.appendChild(recList);
  }

  function renderOpportunities(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = 'Source: ' + data.source + ' · Date range: ' + data.date_range.start_date + ' to ' + data.date_range.end_date;
    out.innerHTML = '';
    const opportunities = data.opportunities || [];
    if (!opportunities.length) {
      out.innerHTML = '<p class="scsi-muted">No conversion opportunities were returned for this date range.</p>';
      return;
    }
    opportunities.forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-opportunity-row';
      const actions = (item.actions || []).map(function (action) { return '<li>' + escapeHtml(action) + '</li>'; }).join('');
      row.innerHTML = '<strong>' + escapeHtml(item.title || item.path) + '</strong><br>' +
        '<code>' + escapeHtml(item.path) + '</code><br>' +
        '<span class="scsi-badge">Priority ' + formatNumber(item.priority_score) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Views ' + formatNumber(item.views) + '</span>' +
        '<small> Repo ' + formatNumber(item.repository_rate) + '% · Workbench ' + formatNumber(item.workbench_rate) + '% · Librarian ' + formatNumber(item.research_librarian_rate) + '% · Pathway ' + formatNumber(item.pathway_rate) + '%</small>' +
        '<ul class="scsi-list">' + actions + '</ul>';
      out.appendChild(row);
    });
  }



  function queryFromDataset(root, keys) {
    const params = new URLSearchParams();
    keys.forEach(function (key) {
      const value = root.dataset[key];
      if (value) {
        const wireKey = key === 'latitude' ? 'latitude' : key === 'longitude' ? 'longitude' : key === 'startDate' ? 'start_date' : key === 'endDate' ? 'end_date' : key === 'start' ? 'start_date' : key === 'end' ? 'end_date' : key === 'priorStart' ? 'prior_start_date' : key === 'priorEnd' ? 'prior_end_date' : key === 'priorStartDate' ? 'prior_start_date' : key === 'priorEndDate' ? 'prior_end_date' : key === 'forceRefresh' ? 'force_refresh' : key === 'useAi' ? 'use_ai' : key;
        params.set(wireKey, value);
      }
    });
    const str = params.toString();
    return str ? '?' + str : '';
  }

  function renderExternalHealth(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const connectors = data.connectors || [];
    muted.textContent = 'Source: ' + (data.source || 'external') + ' · Checked ' + (data.generated_at || 'now') + (data.cache ? ' · Cache entries ' + formatNumber(data.cache.entries_count || 0) : '');
    out.innerHTML = '';
    if (!connectors.length) {
      out.innerHTML = '<p class="scsi-muted">No external connectors were returned.</p>';
      return;
    }
    connectors.forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-external-row';
      row.innerHTML = '<strong>' + escapeHtml(item.name || item.connector_id) + '</strong><br>' +
        statusBadge(item.status || 'unknown') +
        '<span class="scsi-badge scsi-badge-soft">' + (item.live ? 'live' : 'fallback') + '</span>' +
        (item.latency_ms ? '<span class="scsi-badge scsi-badge-soft">' + formatNumber(item.latency_ms) + ' ms</span>' : '') +
        '<span class="scsi-badge scsi-badge-soft">cache ' + escapeHtml(item.cache_status || 'none') + '</span>' +
        (item.age_seconds ? '<span class="scsi-badge scsi-badge-soft">age ' + formatNumber(item.age_seconds) + 's</span>' : '') +
        '<small>' + escapeHtml(item.message || '') + '</small>';
      out.appendChild(row);
    });
  }

  function renderExternalCache(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const entries = data.entries || [];
    muted.textContent = 'Cache entries: ' + formatNumber(data.entries_count || 0) + ' · Hits ' + formatNumber(data.hits || 0) + ' · Misses ' + formatNumber(data.misses || 0) + ' · Stale hits ' + formatNumber(data.stale_hits || 0);
    out.innerHTML = '';
    if (!entries.length) {
      out.innerHTML = '<p class="scsi-muted">No external source cache entries yet. Load the Climate + Energy dashboard to populate the cache.</p>';
      return;
    }
    entries.forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-cache-row';
      row.innerHTML = '<strong>' + escapeHtml(item.source || 'external') + '</strong><br>' +
        '<code>' + escapeHtml(item.cache_key || '') + '</code><br>' +
        '<span class="scsi-badge ' + (item.fresh ? 'scsi-badge-healthy' : 'scsi-badge-fallback') + '">' + (item.fresh ? 'fresh' : 'expired') + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">age ' + formatNumber(item.age_seconds || 0) + 's</span>' +
        '<span class="scsi-badge scsi-badge-soft">ttl ' + formatNumber(item.ttl_seconds || 0) + 's</span>' +
        '<small>Cached at ' + escapeHtml(item.cached_at || '') + (item.last_error ? ' · Last error: ' + escapeHtml(item.last_error) : '') + '</small>';
      out.appendChild(row);
    });
  }

  function renderClimateEnergy(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const loc = data.location || {};
    const emissions = data.emissions_summary || {};
    const indicators = data.indicators || [];
    const layers = data.earth_observation_layers || [];
    const stability = data.stability || {};
    const cache = data.cache_summary || {};
    muted.textContent = 'Source: ' + (data.source || 'external') + ' · Stability ' + (stability.status || 'unknown') + ' · Public status ' + (stability.public_status || 'internal_review') + ' · Location ' + formatNumber(loc.latitude) + ', ' + formatNumber(loc.longitude) + ' · Country ' + (loc.country || '');
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid';
    indicators.slice(0, 6).forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat';
      card.innerHTML = '<strong>' + (item.value === null || typeof item.value === 'undefined' ? '—' : formatNumber(item.value)) + '</strong><span>' + escapeHtml(item.label) + (item.unit ? ' · ' + escapeHtml(item.unit) : '') + '</span>';
      grid.appendChild(card);
    });
    const emCard = document.createElement('div');
    emCard.className = 'scsi-stat';
    emCard.innerHTML = '<strong>' + formatNumber(emissions.total_emissions_tonnes_co2e || 0) + '</strong><span>Emissions tCO₂e · ' + escapeHtml(String(emissions.year || '')) + '</span>';
    grid.appendChild(emCard);
    const stCard = document.createElement('div');
    stCard.className = 'scsi-stat';
    stCard.innerHTML = '<strong>' + formatNumber(stability.score || 0) + '%</strong><span>Dashboard stability</span>';
    grid.appendChild(stCard);
    const cacheCard = document.createElement('div');
    cacheCard.className = 'scsi-stat';
    cacheCard.innerHTML = '<strong>' + formatNumber(cache.oldest_age_seconds || 0) + 's</strong><span>Oldest cached source</span>';
    grid.appendChild(cacheCard);
    out.appendChild(grid);

    const h1 = document.createElement('h3');
    h1.textContent = 'Interpretive indicators';
    out.appendChild(h1);
    indicators.forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-indicator-row';
      row.innerHTML = '<strong>' + escapeHtml(item.label) + '</strong><br>' +
        '<span class="scsi-badge">' + (item.value === null || typeof item.value === 'undefined' ? 'No value' : formatNumber(item.value) + ' ' + escapeHtml(item.unit || '')) + '</span>' +
        '<small>' + escapeHtml(item.interpretation || '') + '</small>';
      out.appendChild(row);
    });

    const h2 = document.createElement('h3');
    h2.textContent = 'Earth observation layers';
    out.appendChild(h2);
    layers.slice(0, 8).forEach(function (layer) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-layer-row';
      row.innerHTML = '<strong>' + escapeHtml(layer.title || layer.layer_id) + '</strong><br>' +
        '<code>' + escapeHtml(layer.layer_id || '') + '</code><br>' +
        '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(layer.category || 'earth_observation') + '</span>' +
        '<small>' + escapeHtml(layer.interpretation || '') + '</small>';
      out.appendChild(row);
    });

    const h3 = document.createElement('h3');
    h3.textContent = 'Emissions sector signal';
    out.appendChild(h3);
    (emissions.top_sectors || []).forEach(function (sector) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-emissions-row';
      row.innerHTML = '<strong>' + escapeHtml(sector.sector || 'unknown') + '</strong><br>' +
        '<span class="scsi-badge">' + formatNumber(sector.emissions_tonnes_co2e || 0) + ' tCO₂e</span>';
      out.appendChild(row);
    });

    const recList = document.createElement('ul');
    recList.className = 'scsi-list';
    (data.recommendations || []).forEach(function (rec) {
      const li = document.createElement('li');
      li.textContent = rec;
      recList.appendChild(li);
    });
    out.appendChild(recList);

    const method = data.methodology || {};
    if (method.summary) {
      const m = document.createElement('p');
      m.className = 'scsi-muted';
      m.textContent = 'Methodology: ' + method.summary + ' ' + (method.review_note || '');
      out.appendChild(m);
    }
    if ((data.notes || []).length) {
      const notes = document.createElement('p');
      notes.className = 'scsi-muted';
      notes.textContent = 'Notes: ' + (data.notes || []).join(' · ');
      out.appendChild(notes);
    }
  }



  function pct(value) {
    return formatNumber(value || 0) + '%';
  }

  function renderSearchIntelligence(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const totals = data.totals || {};
    const topics = data.topic_momentum || [];
    const pages = data.top_pages || [];
    const queries = data.top_queries || [];
    muted.textContent = 'Source: ' + (data.source || 'search') + ' · Date range: ' + (data.date_range ? data.date_range.start_date + ' to ' + data.date_range.end_date : '') + ' · Site: ' + (data.site_url || '');
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid';
    [
      ['Clicks', totals.clicks || 0],
      ['Impressions', totals.impressions || 0],
      ['CTR', totals.ctr || 0, '%'],
      ['Avg position', totals.avg_position || 0],
      ['Pages', totals.pages || 0],
      ['Queries', totals.queries || 0],
      ['Opportunities', totals.opportunities || 0]
    ].forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat';
      card.innerHTML = '<strong>' + formatNumber(item[1]) + (item[2] || '') + '</strong><span>' + item[0] + '</span>';
      grid.appendChild(card);
    });
    out.appendChild(grid);

    const recList = document.createElement('ul');
    recList.className = 'scsi-list';
    (data.recommendations || []).forEach(function (rec) {
      const li = document.createElement('li');
      li.textContent = rec;
      recList.appendChild(li);
    });
    out.appendChild(recList);

    const topicHeading = document.createElement('h3');
    topicHeading.textContent = 'Article Map Search Momentum';
    out.appendChild(topicHeading);
    topics.slice(0, 8).forEach(function (topic) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-search-topic-row';
      row.innerHTML = '<strong>' + escapeHtml(topic.topic || 'Unclassified') + '</strong><br>' +
        '<span class="scsi-badge">Momentum ' + formatNumber(topic.momentum_score || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Impressions ' + formatNumber(topic.impressions || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">CTR ' + pct(topic.ctr || 0) + '</span>' +
        '<small>Queries ' + formatNumber(topic.queries || 0) + ' · Avg position ' + formatNumber(topic.avg_position || 0) + ' · ' + escapeHtml(topic.discipline || '') + '</small>';
      out.appendChild(row);
    });

    const pageHeading = document.createElement('h3');
    pageHeading.textContent = 'Top search opportunity pages';
    out.appendChild(pageHeading);
    pages.slice(0, 8).forEach(function (page) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-search-page-row';
      const q = (page.top_queries || []).slice(0, 3).map(function (item) { return escapeHtml(item.query || ''); }).join(' · ');
      row.innerHTML = '<strong>' + escapeHtml(page.title || page.page) + '</strong><br>' +
        '<code>' + escapeHtml(page.page || '') + '</code><br>' +
        statusBadge(page.mapping_status || 'unmapped') +
        '<span class="scsi-badge">Opportunity ' + formatNumber(page.opportunity_score || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Impressions ' + formatNumber(page.impressions || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">CTR ' + pct(page.ctr || 0) + '</span>' +
        '<small>Position ' + formatNumber(page.position || 0) + (q ? ' · Queries: ' + q : '') + '</small>';
      out.appendChild(row);
    });

    const queryHeading = document.createElement('h3');
    queryHeading.textContent = 'Top query opportunities';
    out.appendChild(queryHeading);
    queries.slice(0, 8).forEach(function (query) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-search-query-row';
      row.innerHTML = '<strong>' + escapeHtml(query.query || '') + '</strong><br>' +
        '<span class="scsi-badge">' + escapeHtml(query.topic || 'Unclassified') + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Impressions ' + formatNumber(query.impressions || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">CTR ' + pct(query.ctr || 0) + '</span>' +
        '<small>Position ' + formatNumber(query.position || 0) + ' · Opportunity ' + formatNumber(query.opportunity_score || 0) + '</small>';
      out.appendChild(row);
    });

    const method = data.methodology || {};
    if (method.summary) {
      const note = document.createElement('p');
      note.className = 'scsi-muted';
      note.textContent = 'Methodology: ' + method.summary + ' ' + (method.score_note || '');
      out.appendChild(note);
    }
  }

  function renderSearchOpportunities(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const opportunities = data.opportunities || [];
    muted.textContent = 'Source: ' + (data.source || 'search') + ' · Search opportunity pages ' + formatNumber(opportunities.length);
    out.innerHTML = '';
    if (!opportunities.length) {
      out.innerHTML = '<p class="scsi-muted">No search opportunities were returned.</p>';
      return;
    }
    opportunities.forEach(function (page) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-search-opportunity-row';
      const recs = (page.recommendations || []).map(function (rec) { return '<li>' + escapeHtml(rec) + '</li>'; }).join('');
      const queries = (page.top_queries || []).slice(0, 4).map(function (q) { return escapeHtml(q.query || '') + ' (' + formatNumber(q.impressions || 0) + ')'; }).join(' · ');
      row.innerHTML = '<strong>' + escapeHtml(page.title || page.page) + '</strong><br>' +
        '<code>' + escapeHtml(page.page || '') + '</code><br>' +
        statusBadge(page.mapping_status || 'unmapped') +
        '<span class="scsi-badge">Opportunity ' + formatNumber(page.opportunity_score || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Clicks ' + formatNumber(page.clicks || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Impressions ' + formatNumber(page.impressions || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">CTR ' + pct(page.ctr || 0) + '</span>' +
        '<small>Position ' + formatNumber(page.position || 0) + (queries ? ' · Queries: ' + queries : '') + '</small>' +
        '<ul class="scsi-list">' + recs + '</ul>';
      out.appendChild(row);
    });
  }


  function renderMetadataIntelligence(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const summary = data.summary || {};
    const reviews = data.metadata_reviews || [];
    muted.textContent = 'Source: ' + (data.source || 'search') + ' · Pages reviewed ' + formatNumber(summary.pages_reviewed || 0) + ' · Priority pages ' + formatNumber(summary.priority_pages || 0);
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid';
    [
      ['Pages reviewed', summary.pages_reviewed || 0],
      ['Priority pages', summary.priority_pages || 0],
      ['Low-CTR pages', summary.low_ctr_pages || 0],
      ['Generic titles', summary.generic_title_pages || 0]
    ].forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat';
      card.innerHTML = '<strong>' + formatNumber(item[1]) + '</strong><span>' + item[0] + '</span>';
      grid.appendChild(card);
    });
    out.appendChild(grid);

    const recList = document.createElement('ul');
    recList.className = 'scsi-list';
    (data.recommendations || []).forEach(function (rec) {
      const li = document.createElement('li');
      li.textContent = rec;
      recList.appendChild(li);
    });
    out.appendChild(recList);

    reviews.forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-metadata-row';
      const recs = (item.recommendations || []).map(function (rec) { return '<li>' + escapeHtml(rec) + '</li>'; }).join('');
      row.innerHTML = '<strong>' + escapeHtml(item.title || item.page) + '</strong><br>' +
        '<code>' + escapeHtml(item.page || '') + '</code><br>' +
        statusBadge(item.title_status || 'review') +
        '<span class="scsi-badge">Priority ' + formatNumber(item.metadata_priority_score || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Title length ' + formatNumber(item.title_length || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">CTR ' + pct(item.ctr || 0) + '</span>' +
        '<small>Top query: ' + escapeHtml(item.top_query || '') + ' · Query-title overlap ' + formatNumber((item.query_title_overlap || 0) * 100) + '% · Position ' + formatNumber(item.position || 0) + '</small>' +
        '<ul class="scsi-list">' + recs + '</ul>';
      out.appendChild(row);
    });
    const method = data.methodology || {};
    if (method.limitation) {
      const note = document.createElement('p');
      note.className = 'scsi-muted';
      note.textContent = 'Note: ' + method.limitation;
      out.appendChild(note);
    }
  }

  function renderInternalLinkIntelligence(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const summary = data.summary || {};
    const opportunities = data.internal_link_opportunities || [];
    muted.textContent = 'Source: ' + (data.source || 'search') + ' · Priority pages ' + formatNumber(summary.priority_pages || 0) + ' · Near page-one ' + formatNumber(summary.near_page_one_pages || 0);
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid';
    [
      ['Pages reviewed', summary.pages_reviewed || 0],
      ['Priority pages', summary.priority_pages || 0],
      ['Near page-one', summary.near_page_one_pages || 0],
      ['Unmapped search pages', summary.unmapped_search_pages || 0]
    ].forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat';
      card.innerHTML = '<strong>' + formatNumber(item[1]) + '</strong><span>' + item[0] + '</span>';
      grid.appendChild(card);
    });
    out.appendChild(grid);

    const recList = document.createElement('ul');
    recList.className = 'scsi-list';
    (data.recommendations || []).forEach(function (rec) {
      const li = document.createElement('li');
      li.textContent = rec;
      recList.appendChild(li);
    });
    out.appendChild(recList);

    opportunities.forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-internal-link-row';
      const actions = (item.actions || []).map(function (action) { return '<li>' + escapeHtml(action) + '</li>'; }).join('');
      const anchors = (item.anchor_suggestions || []).map(function (anchor) { return '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(anchor) + '</span>'; }).join('');
      const sources = (item.source_link_candidates || []).slice(0, 3).map(function (candidate) { return escapeHtml(candidate.title || candidate.page || ''); }).join(' · ');
      row.innerHTML = '<strong>' + escapeHtml(item.title || item.page) + '</strong><br>' +
        '<code>' + escapeHtml(item.page || '') + '</code><br>' +
        statusBadge(item.mapping_status || 'unmapped') +
        '<span class="scsi-badge">Link priority ' + formatNumber(item.internal_link_priority_score || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Impressions ' + formatNumber(item.impressions || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Position ' + formatNumber(item.position || 0) + '</span>' +
        '<div class="scsi-anchor-suggestions">' + anchors + '</div>' +
        (sources ? '<small>Possible source pages: ' + sources + '</small>' : '') +
        '<ul class="scsi-list">' + actions + '</ul>';
      out.appendChild(row);
    });
    const method = data.methodology || {};
    if (method.limitation) {
      const note = document.createElement('p');
      note.className = 'scsi-muted';
      note.textContent = 'Note: ' + method.limitation;
      out.appendChild(note);
    }
  }

  function renderSeoRecommendations(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const summary = data.summary || {};
    const items = data.top_recommendations || [];
    muted.textContent = 'Source: ' + (data.source || 'search') + ' · Combined priority pages ' + formatNumber(summary.combined_priority_pages || 0);
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid';
    [
      ['Metadata priority', summary.metadata_priority_pages || 0],
      ['Internal-link priority', summary.internal_link_priority_pages || 0],
      ['Combined priority', summary.combined_priority_pages || 0]
    ].forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat';
      card.innerHTML = '<strong>' + formatNumber(item[1]) + '</strong><span>' + item[0] + '</span>';
      grid.appendChild(card);
    });
    out.appendChild(grid);

    const recList = document.createElement('ul');
    recList.className = 'scsi-list';
    (data.recommendations || []).slice(0, 8).forEach(function (rec) {
      const li = document.createElement('li');
      li.textContent = rec;
      recList.appendChild(li);
    });
    out.appendChild(recList);

    items.forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-seo-rec-row';
      const recs = (item.recommendations || []).map(function (rec) { return '<li>' + escapeHtml(rec) + '</li>'; }).join('');
      const anchors = (item.anchor_suggestions || []).map(function (anchor) { return '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(anchor) + '</span>'; }).join('');
      row.innerHTML = '<strong>' + escapeHtml(item.title || item.page) + '</strong><br>' +
        '<code>' + escapeHtml(item.page || '') + '</code><br>' +
        '<span class="scsi-badge">Priority ' + formatNumber(item.priority_score || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Metadata ' + formatNumber(item.metadata_priority_score || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Links ' + formatNumber(item.internal_link_priority_score || 0) + '</span>' +
        '<div class="scsi-anchor-suggestions">' + anchors + '</div>' +
        '<ul class="scsi-list">' + recs + '</ul>';
      out.appendChild(row);
    });
    const method = data.methodology || {};
    if (method.review_note) {
      const note = document.createElement('p');
      note.className = 'scsi-muted';
      note.textContent = 'Review note: ' + method.review_note;
      out.appendChild(note);
    }
  }


  function boolBadge(label, value) {
    return '<span class="scsi-badge ' + (value ? 'scsi-badge-healthy' : 'scsi-badge-fallback') + '">' + escapeHtml(label) + ': ' + (value ? 'yes' : 'no') + '</span>';
  }

  function renderIndexingIntelligence(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const totals = data.totals || {};
    const rows = data.coverage_rows || [];
    const source = data.source || {};
    muted.textContent = 'Sources: sitemap ' + (source.sitemap || 'unknown') + ' · GA4 ' + (source.ga4 || 'unknown') + ' · Search ' + (source.search || 'unknown') + ' · Coverage ' + formatNumber(totals.coverage_rate || 0) + '%';
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid';
    [
      ['Total paths', totals.total_paths || 0],
      ['Sitemap URLs', totals.sitemap_urls || 0],
      ['Registry URLs', totals.registry_urls || 0],
      ['GA4 pages', totals.ga4_pages || 0],
      ['Search pages', totals.search_console_pages || 0],
      ['Coverage', totals.coverage_rate || 0, '%'],
      ['Visible unmapped', totals.unmapped_visible_pages || 0],
      ['404 diagnostics', totals.diagnostic_404_pages || 0]
    ].forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat';
      card.innerHTML = '<strong>' + formatNumber(item[1]) + (item[2] || '') + '</strong><span>' + item[0] + '</span>';
      grid.appendChild(card);
    });
    out.appendChild(grid);

    const recList = document.createElement('ul');
    recList.className = 'scsi-list';
    (data.recommendations || []).forEach(function (rec) {
      const li = document.createElement('li');
      li.textContent = rec;
      recList.appendChild(li);
    });
    out.appendChild(recList);

    const h = document.createElement('h3');
    h.textContent = 'Coverage action rows';
    out.appendChild(h);
    rows.slice(0, 18).forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-indexing-row';
      const recs = (item.recommendations || []).map(function (rec) { return '<li>' + escapeHtml(rec) + '</li>'; }).join('');
      row.innerHTML = '<strong>' + escapeHtml(item.title || item.path) + '</strong><br>' +
        '<code>' + escapeHtml(item.path || '') + '</code><br>' +
        statusBadge(item.status || 'partial') +
        '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.kind || 'content') + '</span>' +
        '<span class="scsi-badge">Coverage ' + formatNumber(item.coverage_score || 0) + '</span><br>' +
        boolBadge('sitemap', item.in_sitemap) + boolBadge('registry', item.in_registry) + boolBadge('GA4', item.in_ga4) + boolBadge('Search', item.in_search_console) +
        '<small>Views ' + formatNumber(item.ga4_views || 0) + ' · Search impressions ' + formatNumber(item.search_impressions || 0) + ' · Hub ' + escapeHtml(item.hub || 'Unmapped') + '</small>' +
        '<ul class="scsi-list">' + recs + '</ul>';
      out.appendChild(row);
    });
    const method = data.methodology || {};
    if (method.public_note) {
      const note = document.createElement('p');
      note.className = 'scsi-muted';
      note.textContent = 'Review note: ' + method.public_note;
      out.appendChild(note);
    }
  }

  function renderSitemapCoverage(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = 'Source: ' + (data.source || 'sitemap') + ' · URLs ' + formatNumber(data.total_urls || 0) + ' · Mapped ' + formatNumber(data.mapping_rate || 0) + '%';
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid';
    [
      ['Total URLs', data.total_urls || 0],
      ['Mapped URLs', data.mapped_urls || 0],
      ['Unmapped URLs', data.unmapped_urls || 0],
      ['Mapping rate', data.mapping_rate || 0, '%']
    ].forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat';
      card.innerHTML = '<strong>' + formatNumber(item[1]) + (item[2] || '') + '</strong><span>' + item[0] + '</span>';
      grid.appendChild(card);
    });
    out.appendChild(grid);
    if (data.message) {
      const msg = document.createElement('p');
      msg.className = 'scsi-muted';
      msg.textContent = data.message;
      out.appendChild(msg);
    }
    const unmapped = data.unmapped || [];
    if (!unmapped.length) {
      out.innerHTML += '<p class="scsi-muted">No unmapped sitemap URLs were returned.</p>';
      return;
    }
    const h = document.createElement('h3');
    h.textContent = 'Unmapped sitemap URLs';
    out.appendChild(h);
    unmapped.slice(0, 30).forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-sitemap-row';
      row.innerHTML = '<strong>' + escapeHtml(item.path || item.url) + '</strong><br>' +
        '<code>' + escapeHtml(item.url || item.path || '') + '</code><br>' +
        statusBadge(item.mapping_status || 'unmapped') +
        '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.kind || 'content') + '</span>';
      out.appendChild(row);
    });
  }

  function render404Intelligence(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const rows = data.urls || [];
    muted.textContent = '404/routing candidates: ' + formatNumber(data.count || rows.length || 0);
    out.innerHTML = '';
    const recList = document.createElement('ul');
    recList.className = 'scsi-list';
    (data.recommendations || []).forEach(function (rec) {
      const li = document.createElement('li');
      li.textContent = rec;
      recList.appendChild(li);
    });
    out.appendChild(recList);
    if (!rows.length) {
      out.innerHTML += '<p class="scsi-muted">No 404 candidates were returned for this date range.</p>';
      return;
    }
    rows.forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-404-row';
      const recs = (item.recommendations || []).map(function (rec) { return '<li>' + escapeHtml(rec) + '</li>'; }).join('');
      row.innerHTML = '<strong>' + escapeHtml(item.title || item.path) + '</strong><br>' +
        '<code>' + escapeHtml(item.path || '') + '</code><br>' +
        statusBadge(item.status || 'diagnostic') +
        '<span class="scsi-badge scsi-badge-soft">Views ' + formatNumber(item.ga4_views || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Impressions ' + formatNumber(item.search_impressions || 0) + '</span>' +
        '<ul class="scsi-list">' + recs + '</ul>';
      out.appendChild(row);
    });
  }


  function renderContentStrategy(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const totals = data.totals || {};
    const pages = data.top_pages || [];
    const maps = data.article_map_performance || [];
    muted.textContent = 'Sources: GA4 ' + ((data.source || {}).ga4 || 'unknown') + ' · Search ' + ((data.source || {}).search || 'unknown') + ' · Current ' + ((data.date_range || {}).start_date || '') + ' to ' + ((data.date_range || {}).end_date || '') + ' · Prior ' + ((data.comparison_range || {}).start_date || '') + ' to ' + ((data.comparison_range || {}).end_date || '');
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid';
    [
      ['Current views', totals.current_views || 0],
      ['Prior views', totals.prior_views || 0],
      ['Views growth', totals.views_growth_rate || 0, '%'],
      ['Priority pages', totals.priority_pages || 0],
      ['Decay pages', totals.decay_pages || 0],
      ['Rising pages', totals.rising_pages || 0],
      ['Promotion opportunities', totals.promotion_opportunities || 0],
      ['Article maps reviewed', totals.article_maps_reviewed || 0]
    ].forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat';
      card.innerHTML = '<strong>' + formatNumber(item[1]) + (item[2] || '') + '</strong><span>' + item[0] + '</span>';
      grid.appendChild(card);
    });
    out.appendChild(grid);

    const recList = document.createElement('ul');
    recList.className = 'scsi-list';
    (data.recommendations || []).forEach(function (rec) {
      const li = document.createElement('li');
      li.textContent = rec;
      recList.appendChild(li);
    });
    out.appendChild(recList);

    const h = document.createElement('h3');
    h.textContent = 'Publishing priority pages';
    out.appendChild(h);
    pages.slice(0, 12).forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-publishing-row';
      const actions = (item.actions || []).map(function (action) { return '<li>' + escapeHtml(action) + '</li>'; }).join('');
      const queries = (item.top_queries || []).slice(0, 3).map(function (q) { return escapeHtml(q.query || ''); }).join(' · ');
      row.innerHTML = '<strong>' + escapeHtml(item.title || item.path) + '</strong><br>' +
        '<code>' + escapeHtml(item.path || '') + '</code><br>' +
        statusBadge(item.status || 'maintain') +
        '<span class="scsi-badge">Score ' + formatNumber(item.strategy_score || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Views ' + formatNumber(item.current_views || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Growth ' + formatNumber(item.views_growth_rate || 0) + '%</span>' +
        '<span class="scsi-badge scsi-badge-soft">Search ' + formatNumber(item.search_impressions || 0) + '</span>' +
        '<small>' + escapeHtml(item.hub || '') + (item.article_map ? ' · ' + escapeHtml(item.article_map) : '') + (queries ? ' · Queries: ' + queries : '') + '</small>' +
        '<ul class="scsi-list">' + actions + '</ul>';
      out.appendChild(row);
    });

    const mh = document.createElement('h3');
    mh.textContent = 'Article-map performance';
    out.appendChild(mh);
    maps.slice(0, 8).forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-article-map-row';
      row.innerHTML = '<strong>' + escapeHtml(item.name || '') + '</strong><br>' +
        '<span class="scsi-badge">Strategy ' + formatNumber(item.avg_strategy_score || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Views ' + formatNumber(item.current_views || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Growth ' + formatNumber(item.views_growth_rate || 0) + '%</span>' +
        '<span class="scsi-badge scsi-badge-soft">Search ' + formatNumber(item.search_impressions || 0) + '</span>' +
        '<small>Pages ' + formatNumber(item.pages || 0) + ' · Workbench ' + formatNumber(item.workbench_events || 0) + ' · Repository ' + formatNumber(item.repository_clicks || 0) + '</small>';
      out.appendChild(row);
    });

    const method = data.methodology || {};
    if (method.review_note) {
      const note = document.createElement('p');
      note.className = 'scsi-muted';
      note.textContent = 'Review note: ' + method.review_note;
      out.appendChild(note);
    }
  }

  function renderTopicMomentum(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const topics = data.topics || [];
    const maps = data.article_map_performance || [];
    muted.textContent = 'Topics: ' + formatNumber(topics.length) + ' · Current ' + ((data.date_range || {}).start_date || '') + ' to ' + ((data.date_range || {}).end_date || '');
    out.innerHTML = '';
    const recList = document.createElement('ul');
    recList.className = 'scsi-list';
    (data.recommendations || []).forEach(function (rec) {
      const li = document.createElement('li');
      li.textContent = rec;
      recList.appendChild(li);
    });
    out.appendChild(recList);
    topics.forEach(function (topic) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-topic-row';
      row.innerHTML = '<strong>' + escapeHtml(topic.topic || topic.name || '') + '</strong><br>' +
        '<span class="scsi-badge">Momentum ' + formatNumber(topic.momentum_score || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Views ' + formatNumber(topic.views || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Search ' + formatNumber(topic.search_impressions || 0) + '</span>' +
        '<small>' + escapeHtml(topic.hub || '') + ' · Source ' + escapeHtml(topic.source || '') + (topic.views_growth_rate ? ' · Growth ' + formatNumber(topic.views_growth_rate) + '%' : '') + '</small>';
      out.appendChild(row);
    });
  }

  function renderUpdatePriorities(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const decay = data.content_decay || [];
    const rising = data.rising_pages || [];
    const queue = data.publishing_queue || [];
    muted.textContent = 'Decay ' + formatNumber(decay.length) + ' · Rising ' + formatNumber(rising.length) + ' · Queue ' + formatNumber(queue.length);
    out.innerHTML = '';
    const recList = document.createElement('ul');
    recList.className = 'scsi-list';
    (data.recommendations || []).forEach(function (rec) {
      const li = document.createElement('li');
      li.textContent = rec;
      recList.appendChild(li);
    });
    out.appendChild(recList);
    const h = document.createElement('h3');
    h.textContent = 'Publishing action queue';
    out.appendChild(h);
    queue.slice(0, 15).forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-update-row';
      const actions = (item.actions || []).map(function (action) { return '<li>' + escapeHtml(action) + '</li>'; }).join('');
      const signals = item.signals || {};
      row.innerHTML = '<strong>' + escapeHtml(item.title || item.path) + '</strong><br>' +
        '<code>' + escapeHtml(item.path || '') + '</code><br>' +
        statusBadge(item.status || 'review') +
        '<span class="scsi-badge">Priority ' + formatNumber(item.priority_score || 0) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.suggested_surface || '') + '</span>' +
        '<small>Views ' + formatNumber(signals.current_views || 0) + ' · Growth ' + formatNumber(signals.views_growth_rate || 0) + '% · Search ' + formatNumber(signals.search_impressions || 0) + '</small>' +
        '<ul class="scsi-list">' + actions + '</ul>';
      out.appendChild(row);
    });
    if (data.newsletter_candidates && data.newsletter_candidates.length) {
      const nh = document.createElement('h3');
      nh.textContent = 'Newsletter / Substack candidates';
      out.appendChild(nh);
      data.newsletter_candidates.slice(0, 8).forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-newsletter-row';
        row.innerHTML = '<strong>' + escapeHtml(item.title || item.path) + '</strong><br>' +
          '<span class="scsi-badge">Newsletter score ' + formatNumber(item.newsletter_score || 0) + '</span>' +
          '<small>' + escapeHtml(item.angle || '') + '</small>';
        out.appendChild(row);
      });
    }
  }

  function renderPublishingOpportunities(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const opps = data.promotion_opportunities || [];
    const newsletters = data.newsletter_candidates || [];
    muted.textContent = 'Promotion opportunities ' + formatNumber(opps.length) + ' · Newsletter candidates ' + formatNumber(newsletters.length);
    out.innerHTML = '';
    const recList = document.createElement('ul');
    recList.className = 'scsi-list';
    (data.recommendations || []).forEach(function (rec) {
      const li = document.createElement('li');
      li.textContent = rec;
      recList.appendChild(li);
    });
    out.appendChild(recList);
    opps.forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-promotion-row';
      const actions = (item.actions || []).map(function (action) { return '<li>' + escapeHtml(action) + '</li>'; }).join('');
      const surfaces = (item.surfaces || []).map(function (surface) { return '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(surface) + '</span>'; }).join('');
      const signals = item.signals || {};
      row.innerHTML = '<strong>' + escapeHtml(item.title || item.path) + '</strong><br>' +
        '<code>' + escapeHtml(item.path || '') + '</code><br>' +
        '<span class="scsi-badge">Promotion ' + formatNumber(item.promotion_score || 0) + '</span>' + surfaces +
        '<small>Views ' + formatNumber(signals.views || 0) + ' · Growth ' + formatNumber(signals.growth || 0) + '% · Search ' + formatNumber(signals.search_impressions || 0) + ' · Authority ' + formatNumber(signals.authority_score || 0) + '</small>' +
        '<ul class="scsi-list">' + actions + '</ul>';
      out.appendChild(row);
    });
  }



  function renderPublicLanding(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const status = data.status || {};
    muted.textContent = (data.lede || 'Public-safe dashboard overview.') + ' · Stage: ' + (status.release_stage || 'public preview');
    out.innerHTML = '';

    const hero = document.createElement('div');
    hero.className = 'scsi-public-hero';
    hero.innerHTML = '<div><p class="scsi-eyebrow">' + escapeHtml(data.eyebrow || 'Public Dashboard Framework') + '</p>' +
      '<h3>' + escapeHtml(data.title || 'Sustainable Catalyst Site Intelligence') + '</h3>' +
      '<p>' + escapeHtml(data.lede || '') + '</p></div>' +
      '<div class="scsi-public-status-stack">' +
      statusBadge(status.public_mode || 'enabled') +
      statusBadge(status.raw_analytics_exposed ? 'review' : 'sanitized') +
      statusBadge(status.private_strategy_exposed ? 'review' : 'public_safe') +
      '</div>';
    out.appendChild(hero);

    const grid = document.createElement('div');
    grid.className = 'scsi-grid scsi-public-card-grid';
    (data.cards || []).forEach(function (card) {
      const el = document.createElement('div');
      el.className = 'scsi-stat scsi-public-polish-card';
      el.innerHTML = '<span class="scsi-public-label">' + escapeHtml(card.label || '') + '</span>' +
        '<strong>' + escapeHtml(card.value || '') + '</strong>' +
        '<small>' + escapeHtml(card.detail || '') + '</small>';
      grid.appendChild(el);
    });
    out.appendChild(grid);

    const sectionsTitle = document.createElement('h3');
    sectionsTitle.textContent = 'Public dashboard sections';
    out.appendChild(sectionsTitle);
    (data.sections || []).forEach(function (section) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-public-section-row';
      row.innerHTML = '<strong>' + escapeHtml(section.name || '') + '</strong><br>' +
        '<code>' + escapeHtml(section.shortcode || '') + '</code>' +
        '<small>' + escapeHtml(section.purpose || '') + '</small>';
      out.appendChild(row);
    });

    if ((data.public_ctas || []).length) {
      const ctaWrap = document.createElement('div');
      ctaWrap.className = 'scsi-public-cta-row';
      data.public_ctas.forEach(function (cta) {
        const a = document.createElement('a');
        a.className = 'scsi-public-cta';
        a.href = cta.url || '#';
        a.textContent = cta.label || 'Open';
        if ((cta.url || '').indexOf('http') === 0) { a.target = '_blank'; a.rel = 'noopener'; }
        ctaWrap.appendChild(a);
      });
      out.appendChild(ctaWrap);
    }

    const notes = document.createElement('ul');
    notes.className = 'scsi-list scsi-public-notes';
    (data.review_notes || []).forEach(function (note) { const li = document.createElement('li'); li.textContent = note; notes.appendChild(li); });
    out.appendChild(notes);
  }

  function renderPublicMethodologyBlock(out, methodology) {
    methodology = methodology || {};
    const included = (methodology.included || []).map(function (item) { return '<li>' + escapeHtml(item) + '</li>'; }).join('');
    const excluded = (methodology.excluded || []).map(function (item) { return '<li>' + escapeHtml(item) + '</li>'; }).join('');
    const notes = (methodology.review_notes || []).map(function (item) { return '<li>' + escapeHtml(item) + '</li>'; }).join('');
    out.innerHTML += '<h3>Methodology</h3><p class="scsi-muted">' + escapeHtml(methodology.summary || '') + '</p>' +
      '<div class="scsi-grid"><div class="scsi-stat"><strong>Shown</strong><span>Aggregated public signals</span></div><div class="scsi-stat"><strong>Hidden</strong><span>Raw internal analytics</span></div></div>' +
      '<h4>Included</h4><ul class="scsi-list">' + included + '</ul>' +
      '<h4>Excluded</h4><ul class="scsi-list">' + excluded + '</ul>' +
      '<h4>Review notes</h4><ul class="scsi-list">' + notes + '</ul>';
  }

  function renderPublicDashboard(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const summary = data.summary || {};
    muted.textContent = 'Mode: public-safe · Source: ' + (data.source || 'unknown') + ' · Status: ' + (data.public_status || 'internal_review') + ' · Date range: ' + ((data.date_range || {}).start_date || '') + ' to ' + ((data.date_range || {}).end_date || '');
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid';
    [
      ['Activity band', summary.views_band || '—'],
      ['Rounded views', formatNumber(summary.rounded_views || 0)],
      ['Knowledge areas', summary.knowledge_areas || 0],
      ['Registry entries', summary.registry_entries || 0],
      ['Mapping coverage', formatNumber(summary.mapping_coverage_rate || 0) + '%'],
      ['Public readiness', formatNumber(data.public_readiness_score || 0) + '%']
    ].forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat';
      card.innerHTML = '<strong>' + escapeHtml(item[1]) + '</strong><span>' + escapeHtml(item[0]) + '</span>';
      grid.appendChild(card);
    });
    out.appendChild(grid);

    const h = document.createElement('h3');
    h.textContent = 'Public modules';
    out.appendChild(h);
    (data.modules || []).forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-public-module-row';
      row.innerHTML = '<strong>' + escapeHtml(item.module || '') + '</strong><br>' + statusBadge(item.status || 'internal_review') + '<small>' + escapeHtml(item.public_output || '') + '</small>';
      out.appendChild(row);
    });

    const areas = document.createElement('h3');
    areas.textContent = 'Knowledge areas';
    out.appendChild(areas);
    (data.knowledge_areas || []).slice(0, 6).forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-public-area-row';
      row.innerHTML = '<strong>' + escapeHtml(item.hub || '') + '</strong><br>' +
        '<span class="scsi-badge scsi-badge-soft">Activity ' + escapeHtml(item.activity_band || '—') + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Depth ' + formatNumber(item.depth_score || 0) + '</span>' +
        '<small>' + escapeHtml(item.role || '') + '</small>';
      out.appendChild(row);
    });

    const recs = document.createElement('ul');
    recs.className = 'scsi-list';
    (data.public_recommendations || []).forEach(function (rec) {
      const li = document.createElement('li');
      li.textContent = rec;
      recs.appendChild(li);
    });
    out.appendChild(recs);
  }

  function renderPublicKnowledgeOverview(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const summary = data.summary || {};
    muted.textContent = 'Public-safe overview · ' + formatNumber(summary.knowledge_areas || 0) + ' knowledge areas · Mapping coverage ' + formatNumber(summary.mapping_coverage_rate || 0) + '%';
    out.innerHTML = '';
    (data.knowledge_areas || []).forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-public-area-row';
      row.innerHTML = '<strong>' + escapeHtml(item.hub || '') + '</strong><br>' +
        '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.activity_band || '—') + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">Pages ' + formatNumber(item.pages || 0) + '</span>' +
        '<small>' + escapeHtml(item.role || '') + '</small>';
      out.appendChild(row);
    });
    const h = document.createElement('h3');
    h.textContent = 'Featured public surfaces';
    out.appendChild(h);
    (data.featured_surfaces || []).forEach(function (page) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-public-surface-row';
      row.innerHTML = '<strong>' + escapeHtml(page.title || page.path) + '</strong><br>' +
        '<code>' + escapeHtml(page.path || '') + '</code><br>' +
        '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(page.hub || '') + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(page.depth_status || '') + '</span>' +
        '<small>' + escapeHtml(page.public_focus || '') + '</small>';
      out.appendChild(row);
    });
  }

  function renderPublicClimateEnergy(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const loc = data.location || {};
    const stability = data.stability || {};
    muted.textContent = 'Public-safe external data · Source: ' + (data.source || 'external') + ' · Stability ' + (stability.status || 'unknown') + ' · Public status ' + (stability.public_status || 'review') + ' · Location ' + formatNumber(loc.latitude || 0) + ', ' + formatNumber(loc.longitude || 0);
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid';
    (data.indicators || []).slice(0, 6).forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat';
      card.innerHTML = '<strong>' + (item.value === null || typeof item.value === 'undefined' ? '—' : formatNumber(item.value)) + '</strong><span>' + escapeHtml(item.label || '') + (item.unit ? ' · ' + escapeHtml(item.unit) : '') + '</span>';
      grid.appendChild(card);
    });
    out.appendChild(grid);
    const emissions = data.emissions_summary || {};
    const em = document.createElement('div');
    em.className = 'scsi-page-row scsi-public-source-row';
    em.innerHTML = '<strong>Emissions summary</strong><br><span class="scsi-badge scsi-badge-soft">' + formatNumber(emissions.total_emissions_tonnes_co2e || 0) + ' tCO₂e</span><small>Year ' + escapeHtml(String(emissions.year || '')) + '</small>';
    out.appendChild(em);
    (data.earth_observation_layers || []).slice(0, 6).forEach(function (layer) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-public-source-row';
      row.innerHTML = '<strong>' + escapeHtml(layer.title || layer.layer_id) + '</strong><br><code>' + escapeHtml(layer.layer_id || '') + '</code><small>' + escapeHtml(layer.interpretation || '') + '</small>';
      out.appendChild(row);
    });
    const notes = document.createElement('ul');
    notes.className = 'scsi-list';
    (data.notes || []).forEach(function (note) { const li = document.createElement('li'); li.textContent = note; notes.appendChild(li); });
    if ((data.methodology || {}).summary) { const method = document.createElement('p'); method.className = 'scsi-public-method-note'; method.textContent = (data.methodology || {}).summary; out.appendChild(method); }
    out.appendChild(notes);
  }

  function renderPublicMethodology(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = data.summary || 'Public dashboards show aggregated public-safe signals.';
    out.innerHTML = '';
    renderPublicMethodologyBlock(out, data);
  }

  function renderPublicReadiness(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = 'Status: ' + (data.public_status || 'internal_review') + ' · Score ' + formatNumber(data.public_readiness_score || 0) + '%';
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid';
    const card = document.createElement('div');
    card.className = 'scsi-stat';
    card.innerHTML = '<strong>' + formatNumber(data.public_readiness_score || 0) + '%</strong><span>Public readiness</span>';
    grid.appendChild(card);
    out.appendChild(grid);
    (data.checks || []).forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-public-check-row';
      row.innerHTML = '<strong>' + escapeHtml(item.check || '') + '</strong><br>' + statusBadge(item.status || 'review') + '<small>' + escapeHtml(item.detail || '') + '</small>';
      out.appendChild(row);
    });
    const list = document.createElement('ul');
    list.className = 'scsi-list';
    (data.recommended_next_steps || []).forEach(function (rec) { const li = document.createElement('li'); li.textContent = rec; list.appendChild(li); });
    out.appendChild(list);
  }


  function renderAdvancedExternalDashboard(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const stability = data.stability || {};
    muted.textContent = (data.title || 'Advanced External Data') + ' · Source: ' + (data.source || 'external') + ' · Stability ' + (stability.status || 'unknown') + ' · Score ' + formatNumber(stability.score || 0) + '%';
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid';
    [
      ['Live sources', stability.live_sources || 0],
      ['Fallback sources', stability.fallback_sources || 0],
      ['Needs key', stability.needs_key_sources || 0],
      ['Indicators', (data.indicators || []).length]
    ].forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat';
      card.innerHTML = '<strong>' + formatNumber(item[1]) + '</strong><span>' + escapeHtml(item[0]) + '</span>';
      grid.appendChild(card);
    });
    out.appendChild(grid);
    if (data.summary) {
      const p = document.createElement('p');
      p.className = 'scsi-public-method-note';
      p.textContent = data.summary;
      out.appendChild(p);
    }
    const hSources = document.createElement('h3');
    hSources.textContent = 'Source status';
    out.appendChild(hSources);
    (data.source_summaries || []).forEach(function (src) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-external-row';
      const cache = src.cache || {};
      row.innerHTML = '<strong>' + escapeHtml(src.source || 'external') + '</strong><br>' +
        '<span class="scsi-badge ' + (src.live ? 'scsi-badge-healthy' : 'scsi-badge-fallback') + '">' + (src.live ? 'live' : 'fallback') + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">cache ' + escapeHtml(cache.status || 'none') + '</span>' +
        (src.latency_ms ? '<span class="scsi-badge scsi-badge-soft">' + formatNumber(src.latency_ms) + ' ms</span>' : '') +
        '<small>' + escapeHtml(src.summary || src.message || '') + '</small>';
      out.appendChild(row);
    });
    const hIndicators = document.createElement('h3');
    hIndicators.textContent = 'Interpretive indicators';
    out.appendChild(hIndicators);
    (data.indicators || []).slice(0, 12).forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-indicator-row';
      row.innerHTML = '<strong>' + escapeHtml(item.label || '') + '</strong><br>' +
        '<span class="scsi-badge">' + (item.value === null || typeof item.value === 'undefined' ? 'Context' : formatNumber(item.value) + (item.unit ? ' ' + escapeHtml(item.unit) : '')) + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.source || 'external') + '</span>' +
        '<small>' + escapeHtml(item.interpretation || '') + '</small>';
      out.appendChild(row);
    });
    const maps = document.createElement('p');
    maps.className = 'scsi-muted';
    maps.textContent = 'Linked article maps: ' + (data.linked_article_maps || []).join(', ') + ' · Workbench tools: ' + (data.linked_workbench_tools || []).join(', ');
    out.appendChild(maps);
    const list = document.createElement('ul');
    list.className = 'scsi-list';
    (data.recommendations || []).forEach(function (rec) { const li = document.createElement('li'); li.textContent = rec; list.appendChild(li); });
    out.appendChild(list);
  }


  function renderAiStatus(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = 'Provider: ' + (data.provider || 'disabled') + ' · Mode: ' + (data.mode || 'deterministic-fallback') + ' · Model: ' + (data.model || 'rules');
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid scsi-ai-status-grid';
    [
      ['Enabled', data.enabled ? 'Yes' : 'No'],
      ['Configured', data.configured ? 'Yes' : 'No'],
      ['Provider', data.provider || 'disabled'],
      ['Public safe', data.public_safe ? 'Yes' : 'Review']
    ].forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat';
      card.innerHTML = '<strong>' + escapeHtml(item[1]) + '</strong><span>' + escapeHtml(item[0]) + '</span>';
      grid.appendChild(card);
    });
    out.appendChild(grid);
    const list = document.createElement('ul');
    list.className = 'scsi-list scsi-ai-notes';
    (data.notes || []).forEach(function (note) { const li = document.createElement('li'); li.textContent = note; list.appendChild(li); });
    out.appendChild(list);
  }


  function publicDashboardBriefFallback() {
    return {
      ok: true,
      brief_id: 'public-dashboard-ai-brief',
      title: 'AI-Assisted Public Dashboard Brief',
      generated_at: new Date().toISOString(),
      mode: 'public',
      provider: 'deterministic-local',
      model: 'browser-fallback-v0.9.0',
      source_report: {title: 'Public Dashboard Readiness Report'},
      executive_summary: 'The Sustainable Catalyst public dashboard layer is suitable for reviewed public presentation when it uses sanitized, source-labeled summaries, methodology notes, and public-safe snapshots rather than raw analytics or live operational diagnostics.',
      key_findings: [
        'Public dashboard modules should remain aggregated, reviewed, and source-labeled.',
        'Raw GA4 analytics, conversion diagnostics, report queues, and operational notes should remain private.',
        'Public pages should use fast snapshots by default and reserve live connector calls for private testing.'
      ],
      recommended_actions: [
        'Use the public landing, public knowledge overview, climate/energy summary, and methodology shortcodes on public pages.',
        'Keep the Public Dashboard Brief deterministic unless directly testing the backend route.',
        'Pair public summaries with clear educational and analytical boundaries.'
      ],
      content_opportunities: [
        'Use the public dashboard as portfolio evidence for open infrastructure, analytics, and responsible sustainability tooling.',
        'Turn reviewed public dashboard findings into LinkedIn or Substack updates only after manual review.'
      ],
      risk_notes: [
        'Public dashboards should not expose raw analytics, private recommendations, API configuration, or backend diagnostic details.',
        'This local fallback exists so the page remains stable even when Render, Bluehost, Cloudflare, or an AI provider is unavailable.'
      ],
      public_safe_summary: 'Public Site Intelligence can be presented as a reviewed, source-labeled dashboard framework for Sustainable Catalyst. It should emphasize methodology, knowledge architecture, public data context, and educational boundaries while keeping raw analytics and operational diagnostics private.',
      private_notes: [],
      confidence: {level: 'medium', basis: 'Generated from the v0.9.0 browser fallback to avoid gateway-dependent public rendering.'}
    };
  }

  function renderAiBrief(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const source = data.source_report || {};
    muted.textContent = 'Provider: ' + (data.provider || 'deterministic') + ' · Model: ' + (data.model || 'rules') + ' · Mode: ' + (data.mode || 'private') + (source.title ? ' · Source: ' + source.title : '');
    out.innerHTML = '';

    const summary = document.createElement('div');
    summary.className = 'scsi-ai-summary';
    summary.innerHTML = '<h3>Executive summary</h3><p>' + escapeHtml(data.executive_summary || data.summary || '') + '</p>';
    out.appendChild(summary);

    const conf = data.confidence || {};
    const meta = document.createElement('p');
    meta.className = 'scsi-muted scsi-ai-confidence';
    meta.textContent = 'Confidence: ' + (conf.level || 'review') + (conf.basis ? ' · ' + conf.basis : '');
    out.appendChild(meta);

    [
      ['Key findings', data.key_findings || []],
      ['Recommended next actions', data.recommended_actions || []],
      ['Content and platform opportunities', data.content_opportunities || []],
      ['Risk and uncertainty notes', data.risk_notes || []]
    ].forEach(function (group) {
      if (!group[1].length) return;
      const h = document.createElement('h3');
      h.textContent = group[0];
      out.appendChild(h);
      const list = document.createElement('ul');
      list.className = 'scsi-list scsi-ai-list';
      group[1].slice(0, 8).forEach(function (item) { const li = document.createElement('li'); li.textContent = item; list.appendChild(li); });
      out.appendChild(list);
    });

    if (data.public_safe_summary) {
      const pub = document.createElement('div');
      pub.className = 'scsi-ai-public-summary';
      pub.innerHTML = '<h3>Public-safe summary draft</h3><p>' + escapeHtml(data.public_safe_summary) + '</p>';
      out.appendChild(pub);
    }

    if ((data.private_notes || []).length) {
      const note = document.createElement('p');
      note.className = 'scsi-muted scsi-ai-private-note';
      note.textContent = (data.private_notes || []).join(' ');
      out.appendChild(note);
    }

    if (data.ai_error) {
      const err = document.createElement('p');
      err.className = 'scsi-muted scsi-ai-error';
      err.textContent = 'AI provider fallback: ' + (data.ai_error.error_type || 'error') + ' — ' + (data.ai_error.message || 'The deterministic brief was used.');
      out.appendChild(err);
    }
  }


  function renderReport(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const title = data.title || 'Site Intelligence Report';
    const dateRange = data.date_range || {};
    muted.textContent = 'Generated ' + (data.generated_at || 'now') + (dateRange.start_date ? ' · ' + dateRange.start_date + ' to ' + (dateRange.end_date || '') : '') + ' · Formats: ' + ((data.export_formats || ['json']).join(', '));
    out.innerHTML = '';

    const summary = document.createElement('p');
    summary.className = 'scsi-report-summary';
    summary.textContent = data.summary || '';
    out.appendChild(summary);

    if ((data.highlights || []).length) {
      const h = document.createElement('h3');
      h.textContent = 'Highlights';
      out.appendChild(h);
      const list = document.createElement('ul');
      list.className = 'scsi-list scsi-report-highlights';
      (data.highlights || []).forEach(function (item) {
        const li = document.createElement('li');
        li.textContent = item;
        list.appendChild(li);
      });
      out.appendChild(list);
    }

    if ((data.recommendations || []).length) {
      const h = document.createElement('h3');
      h.textContent = 'Recommendations';
      out.appendChild(h);
      const list = document.createElement('ul');
      list.className = 'scsi-list scsi-report-recommendations';
      (data.recommendations || []).slice(0, 10).forEach(function (item) {
        const li = document.createElement('li');
        li.textContent = item;
        list.appendChild(li);
      });
      out.appendChild(list);
    }

    (data.sections || []).slice(0, 6).forEach(function (section) {
      const wrap = document.createElement('div');
      wrap.className = 'scsi-report-section';
      let html = '<h3>' + escapeHtml(section.title || 'Report section') + '</h3>';
      if (section.summary) html += '<p class="scsi-muted">' + escapeHtml(section.summary) + '</p>';
      const metrics = section.metrics || {};
      const metricKeys = Object.keys(metrics).slice(0, 8);
      if (metricKeys.length) {
        html += '<div class="scsi-grid scsi-report-metrics">';
        metricKeys.forEach(function (key) {
          html += '<div class="scsi-stat"><strong>' + escapeHtml(metrics[key]) + '</strong><span>' + escapeHtml(key.replace(/_/g, ' ')) + '</span></div>';
        });
        html += '</div>';
      }
      wrap.innerHTML = html;
      out.appendChild(wrap);
      (section.rows || []).slice(0, 8).forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-report-row';
        if (typeof item === 'object' && item !== null) {
          const label = item.title || item.name || item.path || item.query || item.connector_id || 'Report item';
          const status = item.status || item.mapping_status || item.public_status || item.source || '';
          const actions = (item.actions || item.recommendations || []).slice ? (item.actions || item.recommendations || []).slice(0, 3) : [];
          row.innerHTML = '<strong>' + escapeHtml(label) + '</strong><br>' +
            (status ? statusBadge(String(status)) : '') +
            (item.strategy_score || item.opportunity_score || item.coverage_score ? '<span class="scsi-badge scsi-badge-soft">Score ' + escapeHtml(item.strategy_score || item.opportunity_score || item.coverage_score) + '</span>' : '') +
            '<small>' + escapeHtml(item.summary || item.path || item.query || item.message || '') + '</small>' +
            (actions.length ? '<ul class="scsi-list">' + actions.map(function (a) { return '<li>' + escapeHtml(a) + '</li>'; }).join('') + '</ul>' : '');
        } else {
          row.textContent = String(item || '');
        }
        out.appendChild(row);
      });
    });

    const methodology = data.methodology || {};
    if (methodology.summary) {
      const note = document.createElement('p');
      note.className = 'scsi-muted scsi-report-methodology';
      note.textContent = methodology.summary + (methodology.privacy_note ? ' ' + methodology.privacy_note : '');
      out.appendChild(note);
    }

    const exportNote = document.createElement('p');
    exportNote.className = 'scsi-muted scsi-report-export-note';
    exportNote.textContent = 'Export endpoints are available through the backend with ?format=markdown or ?format=csv for internal planning.';
    out.appendChild(exportNote);
  }

  function aiBriefEndpoint(type) {
    const map = {
      'site-intelligence': '/ai-site-intelligence-brief',
      'search': '/ai-search-brief',
      'publishing': '/ai-publishing-brief',
      'external-sources': '/ai-external-sources-brief',
      'public-dashboard': '/ai-public-dashboard-brief'
    };
    return map[type] || '/ai-site-intelligence-brief';
  }


  function reportEndpoint(type) {
    const map = {
      'site-intelligence': '/report-site-intelligence',
      'search-intelligence': '/report-search-intelligence',
      'content-strategy': '/report-content-strategy',
      'external-sources': '/report-external-sources',
      'climate-energy': '/report-climate-energy',
      'indexing': '/report-indexing',
      'export': '/report-export'
    };
    return map[type] || '/report-site-intelligence';
  }



  function adminEndpoint(type) {
    const map = {
      'overview': '/admin-overview',
      'registry': '/admin-registry',
      'sources': '/admin-sources',
      'modules': '/admin-modules',
      'shortcodes': '/admin-shortcodes',
      'diagnostics': '/admin-diagnostics',
      'visibility': '/admin-visibility',
      'source-control': '/admin-source-control',
      'status': '/admin-status',
      'connection-check': '/admin-connection-check',
      'public-readiness': '/admin-public-readiness-check',
      'diagnostic-summary': '/admin-diagnostic-summary',
      'release-status': '/release-status'
    };
    return map[type] || '/admin-overview';
  }

  function renderAdminControl(root, data, type) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    out.innerHTML = '';
    muted.textContent = 'Generated: ' + (data.generated_at || 'now') + (data.version ? ' · Version ' + data.version : '') + ' · Private admin control plane';

    if (type === 'connection-check' || type === 'diagnostic-summary' || type === 'status' || type === 'public-readiness' || type === 'release-status') {
      const counts = data.counts || data.status_counts || {};
      const grid = document.createElement('div');
      grid.className = 'scsi-grid scsi-admin-grid';
      if (type === 'release-status') {
        [['Score', data.release_score || data.score || 0], ['Passed', counts.pass || 0], ['Review', counts.review || 0], ['Failed', counts.fail || 0]].forEach(function (item) {
          const card = document.createElement('div');
          card.className = 'scsi-stat';
          card.innerHTML = '<strong>' + formatNumber(item[1]) + '</strong><span>' + escapeHtml(item[0]) + '</span>';
          grid.appendChild(card);
        });
      } else if (type === 'diagnostic-summary') {
        [['Warnings', counts.warnings || 0], ['Modules', counts.modules || 0], ['Shortcodes', counts.shortcodes || 0], ['External connectors', counts.external_connectors || 0]].forEach(function (item) {
          const card = document.createElement('div');
          card.className = 'scsi-stat';
          card.innerHTML = '<strong>' + formatNumber(item[1]) + '</strong><span>' + escapeHtml(item[0]) + '</span>';
          grid.appendChild(card);
        });
      } else {
        [['Healthy', counts.healthy || 0], ['Warnings', counts.warning || data.warning_count || 0], ['Fallback', counts.fallback || 0], ['Disabled', counts.disabled || 0]].forEach(function (item) {
          const card = document.createElement('div');
          card.className = 'scsi-stat';
          card.innerHTML = '<strong>' + formatNumber(item[1]) + '</strong><span>' + escapeHtml(item[0]) + '</span>';
          grid.appendChild(card);
        });
      }
      out.appendChild(grid);
      if (data.summary) {
        const p = document.createElement('p');
        p.className = 'scsi-muted';
        p.textContent = data.summary;
        out.appendChild(p);
      }
      const checks = data.checks || (data.connection && data.connection.checks) || [];
      if (checks.length) {
        const h = document.createElement('h3');
        h.textContent = 'Checks';
        out.appendChild(h);
        checks.forEach(function (item) {
          const row = document.createElement('div');
          row.className = 'scsi-page-row scsi-admin-row';
          row.innerHTML = '<strong>' + escapeHtml(item.label || item.id || '') + '</strong><br>' + statusBadge(item.status || 'unknown') + '<small>' + escapeHtml(item.message || item.detail || String(item.value || '')) + '</small>' + (item.action ? '<small><b>Action:</b> ' + escapeHtml(item.action) + '</small>' : '');
          out.appendChild(row);
        });
      }
      const actions = data.recommended_next_actions || data.troubleshooting || data.launch_notes || data.warnings || [];
      if (actions.length) {
        const h2 = document.createElement('h3');
        h2.textContent = type === 'public-readiness' ? 'Public/private warnings' : 'Recommended next actions';
        out.appendChild(h2);
        const list = document.createElement('ul');
        list.className = 'scsi-list';
        actions.forEach(function (rec) { const li = document.createElement('li'); li.textContent = typeof rec === 'string' ? rec : (rec.label || rec.id || JSON.stringify(rec)); list.appendChild(li); });
        out.appendChild(list);
      }
      if (data.recommended_public_stack) {
        const h3 = document.createElement('h3');
        h3.textContent = 'Recommended public shortcode stack';
        out.appendChild(h3);
        data.recommended_public_stack.forEach(function (code) {
          const row = document.createElement('div');
          row.className = 'scsi-page-row scsi-admin-row';
          row.innerHTML = '<code>' + escapeHtml(code) + '</code> <button type="button" class="scsi-copy-button" data-scsi-copy="' + escapeHtml(code) + '">Copy</button>';
          out.appendChild(row);
        });
      }
      if (type === 'release-status') {
        if (data.public_shortcode) {
          const row = document.createElement('div');
          row.className = 'scsi-page-row scsi-admin-row scsi-release-status-row';
          row.innerHTML = '<strong>Recommended public shortcode</strong><br><code>' + escapeHtml(data.public_shortcode) + '</code> <button type="button" class="scsi-copy-button" data-scsi-copy="' + escapeHtml(data.public_shortcode) + '">Copy</button>';
          out.appendChild(row);
        }
        if (data.metadata) {
          const meta = document.createElement('div');
          meta.className = 'scsi-page-row scsi-admin-row scsi-release-metadata-row';
          meta.innerHTML = '<strong>Suggested metadata</strong><br><small><b>SEO title:</b> ' + escapeHtml(data.metadata.seo_title || '') + '</small><small><b>Meta description:</b> ' + escapeHtml(data.metadata.meta_description || '') + '</small>';
          out.appendChild(meta);
        }
      }
      return;
    }

    if (type === 'shortcodes') {
      const counts = data.category_counts || {};
      const visibility = data.visibility_counts || {};
      const grid = document.createElement('div');
      grid.className = 'scsi-grid scsi-admin-grid';
      [
        ['Shortcodes', data.count || 0],
        ['Public', visibility.public || 0],
        ['Private', visibility.private || 0],
        ['Categories', Object.keys(counts).length]
      ].forEach(function (item) {
        const card = document.createElement('div');
        card.className = 'scsi-stat';
        card.innerHTML = '<strong>' + formatNumber(item[1]) + '</strong><span>' + escapeHtml(item[0]) + '</span>';
        grid.appendChild(card);
      });
      out.appendChild(grid);
      (data.placement_notes || []).forEach(function (note) {
        const p = document.createElement('p');
        p.className = 'scsi-muted';
        p.textContent = note;
        out.appendChild(p);
      });
      (data.shortcodes || []).forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-admin-row';
        row.innerHTML = '<strong><code>' + escapeHtml(item.shortcode || '') + '</code></strong> <button type="button" class="scsi-copy-button" data-scsi-copy="' + escapeHtml(item.shortcode || '') + '">Copy</button><br>' +
          statusBadge(item.visibility || 'private') + '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.category || 'general') + '</span>' +
          (item.endpoint ? '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.endpoint) + '</span>' : '') +
          '<small>' + escapeHtml(item.purpose || '') + '</small>';
        out.appendChild(row);
      });
      return;
    }

    if (type === 'modules') {
      const modules = data.modules || [];
      const grid = document.createElement('div');
      grid.className = 'scsi-grid scsi-admin-grid';
      [
        ['Modules', data.count || modules.length],
        ['Active', (data.status_counts || {}).active || 0],
        ['Public', (data.visibility_counts || {}).public || 0],
        ['Private', (data.visibility_counts || {}).private || 0]
      ].forEach(function (item) {
        const card = document.createElement('div');
        card.className = 'scsi-stat';
        card.innerHTML = '<strong>' + formatNumber(item[1]) + '</strong><span>' + escapeHtml(item[0]) + '</span>';
        grid.appendChild(card);
      });
      out.appendChild(grid);
      modules.forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-admin-row';
        row.innerHTML = '<strong>' + escapeHtml(item.name || item.id) + '</strong><br>' +
          statusBadge(item.status || 'unknown') + '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.visibility || 'private') + '</span>' +
          '<small>' + escapeHtml(item.notes || '') + '</small>' +
          (item.shortcodes && item.shortcodes.length ? '<p class="scsi-muted">Shortcodes: ' + item.shortcodes.map(escapeHtml).join(' · ') + '</p>' : '') +
          (item.endpoints && item.endpoints.length ? '<p class="scsi-muted">Endpoints: ' + item.endpoints.map(escapeHtml).join(' · ') + '</p>' : '');
        out.appendChild(row);
      });
      return;
    }

    const totals = data.totals || {};
    const grid = document.createElement('div');
    grid.className = 'scsi-grid scsi-admin-grid';
    [
      ['Registry items', totals.registry_items || 0],
      ['Hubs', totals.hubs || 0],
      ['External connectors', totals.external_connectors || 0],
      ['Modules', totals.modules || 0],
      ['Shortcodes', totals.shortcodes || 0],
      ['Warnings', totals.warnings || 0]
    ].forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat';
      card.innerHTML = '<strong>' + formatNumber(item[1]) + '</strong><span>' + escapeHtml(item[0]) + '</span>';
      grid.appendChild(card);
    });
    out.appendChild(grid);

    if (data.summary) {
      const p = document.createElement('p');
      p.className = 'scsi-muted';
      p.textContent = data.summary;
      out.appendChild(p);
    }

    const diag = data.diagnostics || {};
    if ((diag.checks || []).length) {
      const h = document.createElement('h3');
      h.textContent = 'Diagnostic checks';
      out.appendChild(h);
      (diag.checks || []).forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-admin-row';
        row.innerHTML = '<strong>' + escapeHtml(item.label || item.id) + '</strong><br>' + statusBadge(item.status || 'unknown') + '<small>' + escapeHtml(String(item.value)) + '</small>';
        out.appendChild(row);
      });
    }

    if ((data.modules || []).length) {
      const h2 = document.createElement('h3');
      h2.textContent = 'Modules';
      out.appendChild(h2);
      (data.modules || []).slice(0, 12).forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-admin-row';
        row.innerHTML = '<strong>' + escapeHtml(item.name || item.id) + '</strong><br>' + statusBadge(item.status || 'unknown') + '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.visibility || '') + '</span><small>' + escapeHtml(item.notes || '') + '</small>';
        out.appendChild(row);
      });
    }

    const actions = data.next_actions || data.recommendations || [];
    if (actions.length) {
      const h3 = document.createElement('h3');
      h3.textContent = 'Recommended next actions';
      out.appendChild(h3);
      const list = document.createElement('ul');
      list.className = 'scsi-list';
      actions.forEach(function (rec) {
        const li = document.createElement('li');
        li.textContent = rec;
        list.appendChild(li);
      });
      out.appendChild(list);
    }
  }



  function renderPublicPageBuilder(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const defaults = data.public_defaults || {};
    muted.textContent = (data.summary || 'Public-safe page-builder guidance.') + ' · Mode: ' + (data.mode || 'public_safe_builder');
    out.innerHTML = '';

    const copy = data.editorial_copy || {};
    const hero = document.createElement('div');
    hero.className = 'scsi-public-builder-hero';
    hero.innerHTML = '<p class="scsi-eyebrow">' + escapeHtml(data.eyebrow || 'Public Dashboard Builder') + '</p>' +
      '<h3>' + escapeHtml(data.title || 'Public Flagship Dashboard Page Builder') + '</h3>' +
      '<p>' + escapeHtml(copy.intro || data.summary || '') + '</p>' +
      '<p class="scsi-public-boundary">' + escapeHtml(copy.boundary_note || '') + '</p>';
    out.appendChild(hero);

    const grid = document.createElement('div');
    grid.className = 'scsi-grid scsi-builder-safe-grid';
    [
      ['Raw analytics exposed', defaults.raw_analytics_exposed ? 'Review' : 'No'],
      ['Private reports exposed', defaults.private_reports_exposed ? 'Review' : 'No'],
      ['Admin diagnostics exposed', defaults.admin_diagnostics_exposed ? 'Review' : 'No'],
      ['Live external calls required', defaults.live_external_calls_required ? 'Yes' : 'No'],
      ['Public dashboards enabled', defaults.public_dashboards_enabled ? 'Yes' : 'Review']
    ].forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat scsi-public-polish-card';
      card.innerHTML = '<strong>' + escapeHtml(item[1]) + '</strong><span>' + escapeHtml(item[0]) + '</span>';
      grid.appendChild(card);
    });
    out.appendChild(grid);

    const flagship = document.createElement('div');
    flagship.className = 'scsi-page-row scsi-shortcode-row scsi-flagship-copy-row';
    flagship.innerHTML = '<strong>Recommended public flagship shortcode</strong><br><code>' + escapeHtml(data.flagship_shortcode || '[sc_site_intelligence_public_flagship]') + '</code>' +
      '<button type="button" class="scsi-copy-button" data-scsi-copy="' + escapeHtml(data.flagship_shortcode || '[sc_site_intelligence_public_flagship]') + '">Copy</button>';
    out.appendChild(flagship);

    const h = document.createElement('h3');
    h.textContent = 'Page presets';
    out.appendChild(h);
    (data.page_presets || []).forEach(function (preset) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-public-preset-row';
      row.innerHTML = '<strong>' + escapeHtml(preset.name || preset.id) + '</strong><br>' +
        statusBadge(preset.status || 'ready') + '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(preset.visibility || '') + '</span>' +
        '<small>' + escapeHtml(preset.description || '') + '</small>' +
        '<code>' + escapeHtml(preset.shortcode || '') + '</code>' +
        '<button type="button" class="scsi-copy-button" data-scsi-copy="' + escapeHtml(preset.shortcode || '') + '">Copy</button>';
      out.appendChild(row);
    });

    const s = document.createElement('h3');
    s.textContent = 'Flagship section order';
    out.appendChild(s);
    (data.layout_sections || []).forEach(function (section) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-public-section-row';
      row.innerHTML = '<strong>' + formatNumber(section.order || 0) + '. ' + escapeHtml(section.title || '') + '</strong><br>' +
        statusBadge(section.status || 'ready') + '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(section.visibility || '') + '</span>' +
        '<code>' + escapeHtml(section.shortcode || '') + '</code>' +
        '<small>' + escapeHtml(section.purpose || '') + '</small>';
      out.appendChild(row);
    });

    const list = document.createElement('ul');
    list.className = 'scsi-list scsi-release-checklist';
    (data.release_checklist || []).forEach(function (item) { const li = document.createElement('li'); li.textContent = item; list.appendChild(li); });
    if ((data.release_checklist || []).length) {
      const c = document.createElement('h3');
      c.textContent = 'Release checklist';
      out.appendChild(c);
      out.appendChild(list);
    }
  }

  function renderPublicShortcodeBundles(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = data.summary || 'Copy-ready public dashboard bundles.';
    out.innerHTML = '';
    (data.bundles || []).forEach(function (bundle) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-shortcode-bundle-row';
      const sections = (bundle.sections || []).map(function (item) { return '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item) + '</span>'; }).join('');
      row.innerHTML = '<strong>' + escapeHtml(bundle.name || bundle.id) + '</strong><br>' +
        '<span class="scsi-badge">' + escapeHtml(bundle.visibility || 'public') + '</span>' +
        '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(bundle.recommended_page_type || '') + '</span>' +
        '<small>' + escapeHtml(bundle.notes || '') + '</small>' +
        '<pre class="scsi-shortcode-pre">' + escapeHtml(bundle.shortcode || '') + '</pre>' +
        '<button type="button" class="scsi-copy-button" data-scsi-copy="' + escapeHtml(bundle.shortcode || '') + '">Copy bundle</button>' +
        '<div class="scsi-mini-badges">' + sections + '</div>';
      out.appendChild(row);
    });
  }

  function renderPublicVisualQa(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = (data.summary || 'Public dashboard QA guidance.') + ' · Status: ' + (data.status || 'review');
    out.innerHTML = '';

    const hero = document.createElement('div');
    hero.className = 'scsi-public-qa-hero';
    hero.innerHTML = '<p class="scsi-eyebrow">' + escapeHtml(data.eyebrow || 'Public Flagship QA') + '</p>' +
      '<h3>' + escapeHtml(data.title || 'Public Dashboard Visual QA') + '</h3>' +
      '<p>' + escapeHtml(data.summary || '') + '</p>' +
      '<div class="scsi-mini-badges">' + statusBadge(data.status || 'review') + '<span class="scsi-badge scsi-badge-soft">Score ' + formatNumber(data.score || 0) + '%</span></div>';
    out.appendChild(hero);

    const copy = data.public_page_copy || {};
    const copyBox = document.createElement('div');
    copyBox.className = 'scsi-page-row scsi-public-copy-box';
    copyBox.innerHTML = '<strong>Suggested public page copy</strong>' +
      '<small><b>Title:</b> ' + escapeHtml(copy.suggested_title || '') + '</small>' +
      '<small><b>Excerpt:</b> ' + escapeHtml(copy.suggested_excerpt || '') + '</small>' +
      '<small><b>Meta:</b> ' + escapeHtml(copy.suggested_meta_description || '') + '</small>' +
      '<code>' + escapeHtml(data.recommended_public_shortcode || '[sc_site_intelligence_public_flagship]') + '</code>';
    out.appendChild(copyBox);

    const checksTitle = document.createElement('h3');
    checksTitle.textContent = 'QA checks';
    out.appendChild(checksTitle);
    (data.checks || []).forEach(function (check) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-public-qa-row';
      row.innerHTML = '<strong>' + escapeHtml(check.label || check.id) + '</strong><br>' +
        statusBadge(check.status || 'review') +
        '<small>' + escapeHtml(check.detail || '') + '</small>' +
        '<small><b>Review note:</b> ' + escapeHtml(check.recommendation || '') + '</small>';
      out.appendChild(row);
    });

    [['Copy polish guidance', data.copy_guidelines || []], ['Visual review guidance', data.visual_guidelines || []], ['Launch notes', data.launch_notes || []]].forEach(function (group) {
      if (!group[1].length) return;
      const h = document.createElement('h3');
      h.textContent = group[0];
      out.appendChild(h);
      const ul = document.createElement('ul');
      ul.className = 'scsi-list scsi-public-qa-list';
      group[1].forEach(function (item) { const li = document.createElement('li'); li.textContent = item; ul.appendChild(li); });
      out.appendChild(ul);
    });
  }


  function renderPublicTopicDirectory(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = (data.summary || 'Public-safe dashboard directory.') + ' · Status: ' + (data.public_status || 'review');
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid scsi-public-topic-grid';
    (data.dashboards || []).forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat scsi-public-topic-card';
      card.innerHTML = '<span class="scsi-public-label">' + escapeHtml(item.eyebrow || item.slug || '') + '</span>' +
        '<strong>' + escapeHtml(item.title || '') + '</strong>' +
        '<small>' + escapeHtml(item.summary || '') + '</small>' +
        '<code>' + escapeHtml(item.shortcode || '') + '</code>' +
        '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.public_status || 'review') + '</span>';
      grid.appendChild(card);
    });
    out.appendChild(grid);
    const notes = document.createElement('ul');
    notes.className = 'scsi-list scsi-public-notes';
    (data.review_notes || []).forEach(function (note) { const li = document.createElement('li'); li.textContent = note; notes.appendChild(li); });
    out.appendChild(notes);
  }

  function renderPublicTopicDashboard(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = (data.summary || '') + ' · Status: ' + (data.public_status || 'review') + ' · Source mode: ' + (data.source_mode || 'public_safe');
    out.innerHTML = '';

    const grid = document.createElement('div');
    grid.className = 'scsi-grid scsi-public-topic-grid';
    (data.cards || []).forEach(function (card) {
      const el = document.createElement('div');
      el.className = 'scsi-stat scsi-public-topic-card';
      el.innerHTML = '<span class="scsi-public-label">' + escapeHtml(card.label || '') + '</span>' +
        '<strong>' + escapeHtml(card.value || '') + '</strong>' +
        '<small>' + escapeHtml(card.note || '') + '</small>';
      grid.appendChild(el);
    });
    out.appendChild(grid);

    if ((data.recommended_sections || []).length) {
      const h = document.createElement('h3');
      h.textContent = 'Recommended public page sections';
      out.appendChild(h);
      const pipeline = document.createElement('ol');
      pipeline.className = 'scsi-public-topic-pipeline';
      (data.recommended_sections || []).forEach(function (item, index) {
        const li = document.createElement('li');
        li.innerHTML = '<strong>Section ' + (index + 1) + '</strong>' + escapeHtml(item || '');
        pipeline.appendChild(li);
      });
      out.appendChild(pipeline);
    }

    const methodology = data.methodology || {};
    if ((methodology.shown || []).length || (methodology.hidden || []).length) {
      const wrap = document.createElement('div');
      wrap.className = 'scsi-public-topic-methodology';
      wrap.innerHTML = '<div><h4>Shown</h4><ul class="scsi-list">' + (methodology.shown || []).map(function (item) { return '<li>' + escapeHtml(item) + '</li>'; }).join('') + '</ul></div>' +
        '<div><h4>Hidden</h4><ul class="scsi-list">' + (methodology.hidden || []).map(function (item) { return '<li>' + escapeHtml(item) + '</li>'; }).join('') + '</ul></div>';
      out.appendChild(wrap);
    }

    if ((data.ctas || []).length) {
      const cta = document.createElement('div');
      cta.className = 'scsi-public-cta-row';
      (data.ctas || []).forEach(function (item) {
        const a = document.createElement('a');
        a.className = 'scsi-public-cta';
        a.href = item.url || '#';
        a.textContent = item.label || 'Open';
        if ((item.url || '').indexOf('http') === 0) { a.target = '_blank'; a.rel = 'noopener'; }
        cta.appendChild(a);
      });
      out.appendChild(cta);
    }

    const notes = document.createElement('ul');
    notes.className = 'scsi-list scsi-public-notes';
    (data.review_notes || []).forEach(function (note) { const li = document.createElement('li'); li.textContent = note; notes.appendChild(li); });
    out.appendChild(notes);
  }

  function renderPublicSourceMethodology(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = (data.summary || 'Public source methodology.') + ' · Status: ' + (data.public_status || 'review');
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid scsi-public-topic-grid';
    (data.principles || []).forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat scsi-public-topic-card';
      card.innerHTML = '<span class="scsi-public-label">' + escapeHtml(item.label || '') + '</span>' +
        '<strong>' + escapeHtml(item.title || '') + '</strong>' +
        '<small>' + escapeHtml(item.detail || '') + '</small>';
      grid.appendChild(card);
    });
    out.appendChild(grid);

    const h = document.createElement('h3');
    h.textContent = 'Source families';
    out.appendChild(h);
    (data.source_families || []).forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-public-source-row';
      row.innerHTML = '<strong>' + escapeHtml(item.family || '') + '</strong><br>' +
        '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.examples || '') + '</span>' +
        '<small>' + escapeHtml(item.public_use || '') + '</small>';
      out.appendChild(row);
    });
  }


  function normalizePath(path) {
    try {
      const url = path.indexOf('http') === 0 ? new URL(path) : new URL(path, window.location.origin);
      let pathname = url.pathname || '/';
      if (!pathname.endsWith('/')) pathname += '/';
      return pathname;
    } catch (e) {
      return String(path || '').replace(/[#?].*$/, '').replace(/\/$/, '') + '/';
    }
  }

  function renderPublicDashboardNavigation(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const current = root.dataset.current || data.current_slug || '';
    muted.textContent = data.summary || 'Public dashboard navigation.';
    out.innerHTML = '';
    const nav = document.createElement('div');
    nav.className = 'scsi-public-nav-row';
    (data.items || []).forEach(function (item) {
      const a = document.createElement('a');
      a.href = item.path || item.url || '#';
      a.textContent = (item.label || item.slug || 'Dashboard') + ' →';
      a.className = 'scsi-public-nav-link';
      if (item.active || (current && item.slug === current)) a.className += ' scsi-active-link';
      nav.appendChild(a);
    });
    out.appendChild(nav);
  }

  function renderPublicTopicPageTemplates(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = data.summary || 'Copy-ready metadata, shortcode, and section guidance.';
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid scsi-public-topic-grid';
    (data.templates || []).forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat scsi-public-topic-card scsi-template-card';
      card.innerHTML = '<span class="scsi-public-label">' + escapeHtml(item.slug || '') + '</span>' +
        '<strong>' + escapeHtml(item.title || '') + '</strong>' +
        '<small><b>Path:</b> ' + escapeHtml(item.canonical_path || '') + '</small>' +
        '<small><b>Excerpt:</b> ' + escapeHtml(item.excerpt || '') + '</small>' +
        '<small><b>Meta:</b> ' + escapeHtml(item.meta_description || '') + '</small>' +
        '<code>' + escapeHtml(item.shortcode || '') + '</code>';
      grid.appendChild(card);
    });
    out.appendChild(grid);
  }

  function renderPublicTopicPageVisualQa(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = (data.summary || 'Public topic page QA.') + ' · Score: ' + formatNumber(data.score || 0) + '%';
    out.innerHTML = '';
    (data.checks || []).forEach(function (check) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-public-qa-row';
      row.innerHTML = '<strong>' + escapeHtml(check.label || check.id || '') + '</strong><br>' +
        statusBadge(check.status || 'review') +
        '<small>' + escapeHtml(check.detail || '') + '</small>';
      out.appendChild(row);
    });
    const notes = document.createElement('ul');
    notes.className = 'scsi-list scsi-public-notes';
    (data.review_notes || []).forEach(function (note) { const li = document.createElement('li'); li.textContent = note; notes.appendChild(li); });
    out.appendChild(notes);
  }


  function sourcePanelEndpoint(panel) {
    const map = {
      'api-sources': '/public-api-sources',
      'source-health': '/public-source-health',
      'development-indicators': '/public-development-indicators',
      'research-metadata': '/public-research-metadata',
      'publication-metadata': '/public-publication-metadata',
      'repository-intelligence': '/public-repository-intelligence',
      'indicator-overview': '/public-indicator-overview',
      'sustainability-indicators': '/public-sustainability-indicators'
    };
    return map[panel] || '/public-api-sources';
  }

  function renderPublicSourcePanel(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = (data.summary || 'Public source panel.') + ' · Status: ' + (data.public_status || data.version_scope || 'review');
    out.innerHTML = '';

    if (data.counts) {
      const grid = document.createElement('div');
      grid.className = 'scsi-grid scsi-public-source-health-grid';
      Object.keys(data.counts).forEach(function (key) {
        const card = document.createElement('div');
        card.className = 'scsi-stat scsi-public-source-status-card';
        card.innerHTML = '<span class="scsi-public-label">' + escapeHtml(key) + '</span>' +
          '<strong>' + formatNumber(data.counts[key]) + '</strong>' +
          '<small>' + escapeHtml((data.status_definitions || {})[key] || 'Source family count.') + '</small>';
        grid.appendChild(card);
      });
      out.appendChild(grid);
    }

    const families = data.source_families || [];
    if (families.length) {
      const h = document.createElement('h3');
      h.textContent = 'Source families';
      out.appendChild(h);
      families.forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-public-source-row';
        const examples = (item.source_examples || []).join(', ');
        row.innerHTML = '<strong>' + escapeHtml(item.label || item.slug || '') + '</strong><br>' +
          statusBadge(item.status || 'planned') + '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.source_mode || 'public_context') + '</span>' +
          '<small><b>Sources:</b> ' + escapeHtml(examples) + '</small>' +
          '<small><b>Public use:</b> ' + escapeHtml(item.public_use || '') + '</small>' +
          '<small><b>Safe display:</b> ' + escapeHtml(item.safe_display || '') + '</small>';
        out.appendChild(row);
      });
    }

    const groups = data.indicator_groups || data.metadata_groups || data.repository_groups || [];
    if (groups.length) {
      const h = document.createElement('h3');
      h.textContent = data.indicator_groups ? 'Indicator groups' : data.metadata_groups ? 'Metadata groups' : 'Repository groups';
      out.appendChild(h);
      groups.forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-public-source-row';
        const examples = item.indicator_examples || item.metadata_examples || [];
        row.innerHTML = '<strong>' + escapeHtml(item.group || '') + '</strong><br>' +
          statusBadge(item.status || 'planned') + '<span class="scsi-badge scsi-badge-soft">' + escapeHtml((item.sources || []).join(', ')) + '</span>' +
          '<small>' + escapeHtml((examples || []).join(', ')) + '</small>' +
          '<small><b>Dashboard use:</b> ' + escapeHtml(item.dashboard_use || '') + '</small>';
        out.appendChild(row);
      });
    }

    const indicators = data.indicators || [];
    if (indicators.length) {
      const h = document.createElement('h3');
      h.textContent = 'Public indicators';
      out.appendChild(h);
      indicators.forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-public-source-row';
        row.innerHTML = '<strong>' + escapeHtml(item.label || '') + '</strong><br>' +
          statusBadge(item.status || 'planned') + '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.source_family || '') + '</span>' +
          '<small>' + escapeHtml(item.public_note || '') + '</small>';
        out.appendChild(row);
      });
    }

    [['Methodology', data.methodology || []], ['Hidden from public pages', data.hidden || []], ['Review notes', data.review_notes || []]].forEach(function (group) {
      if (!group[1].length) return;
      const h = document.createElement('h3');
      h.textContent = group[0];
      out.appendChild(h);
      const ul = document.createElement('ul');
      ul.className = 'scsi-list scsi-public-notes';
      group[1].forEach(function (item) { const li = document.createElement('li'); li.textContent = item; ul.appendChild(li); });
      out.appendChild(ul);
    });
  }



  function indicatorChartPanelEndpoint(panel) {
    const map = {
      'directory': '/public-indicator-chart-panel?panel=directory',
      'sustainability': '/public-indicator-chart-panel?panel=sustainability',
      'development': '/public-indicator-chart-panel?panel=development',
      'source-health': '/public-indicator-chart-panel?panel=source-health',
      'research': '/public-indicator-chart-panel?panel=research',
      'repository': '/public-indicator-chart-panel?panel=repository',
      'gallery': '/public-indicator-chart-panel?panel=gallery',
      'visual-qa': '/public-indicator-chart-panel?panel=visual-qa'
    };
    return map[panel] || '/public-indicator-chart-panel?panel=directory';
  }

  function renderSimpleChartSpec(spec) {
    const card = document.createElement('div');
    card.className = 'scsi-public-chart-card';
    const title = ((spec.meta || {}).title || 'Public chart');
    const desc = ((spec.meta || {}).description || 'Public-safe indicator chart.');
    card.innerHTML = '<h3>' + escapeHtml(title) + '</h3><p>' + escapeHtml(desc) + '</p>';
    const data = spec.data || [];
    const series = (spec.series || [])[0] || {};
    const valueKey = series.dataKey || spec.valueKey || 'value';
    const xKey = spec.xKey || spec.nameKey || 'label';
    const max = Math.max.apply(null, data.map(function (row) { return Number(row[valueKey] || 0); }).concat([1]));
    const chart = document.createElement('div');
    chart.className = 'scsi-public-chart-body scsi-public-chart-' + escapeHtml(spec.chartType || 'bar');
    if ((spec.chartType || 'bar') === 'line') {
      const points = data.map(function (row, index) {
        const x = data.length <= 1 ? 0 : (index / (data.length - 1)) * 100;
        const y = 100 - ((Number(row[valueKey] || 0) / max) * 90 + 5);
        return x + ',' + y;
      }).join(' ');
      chart.innerHTML = '<svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><polyline points="' + escapeHtml(points) + '" fill="none" stroke="currentColor" stroke-width="3" vector-effect="non-scaling-stroke"></polyline></svg>';
    } else {
      data.forEach(function (row) {
        const label = row[xKey] || row.name || row.status || row.connector || '';
        const value = Number(row[valueKey] || 0);
        const pct = Math.max(4, Math.round((value / max) * 100));
        const line = document.createElement('div');
        line.className = 'scsi-public-chart-bar-row';
        line.innerHTML = '<span>' + escapeHtml(label) + '</span><div><i style="width:' + pct + '%"></i></div><strong>' + formatNumber(value) + (series.valueSuffix || '') + '</strong>';
        chart.appendChild(line);
      });
    }
    card.appendChild(chart);
    return card;
  }

  function renderPublicIndicatorChartPanel(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = (data.summary || 'Public indicator chart panel.') + ' · Status: ' + (data.public_status || data.version_scope || 'review');
    out.innerHTML = '';

    const dashboards = data.dashboards || [];
    if (dashboards.length) {
      const grid = document.createElement('div');
      grid.className = 'scsi-grid scsi-public-indicator-dashboard-grid';
      dashboards.forEach(function (item) {
        const card = document.createElement('div');
        card.className = 'scsi-page-row scsi-public-indicator-dashboard-card';
        card.innerHTML = '<strong>' + escapeHtml(item.title || item.slug || '') + '</strong><br>' +
          '<span class="scsi-badge scsi-badge-soft">' + formatNumber(item.chart_count || 0) + ' charts</span>' +
          '<small>' + escapeHtml(item.summary || '') + '</small>' +
          '<small><b>Shortcode:</b> ' + escapeHtml(item.recommended_shortcode || '') + '</small>';
        grid.appendChild(card);
      });
      out.appendChild(grid);
    }

    const specs = data.chart_specs || [];
    if (specs.length) {
      const h = document.createElement('h3');
      h.textContent = 'Chart-ready public indicators';
      out.appendChild(h);
      specs.forEach(function (spec) {
        out.appendChild(renderSimpleChartSpec(spec));
      });
    }

    const checks = data.checks || [];
    if (checks.length) {
      const h = document.createElement('h3');
      h.textContent = 'Visual QA checks';
      out.appendChild(h);
      checks.forEach(function (check) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-public-qa-row';
        row.innerHTML = '<strong>' + escapeHtml(check.label || check.id || '') + '</strong><br>' +
          statusBadge(check.status || 'review') + '<small>' + escapeHtml(check.detail || '') + '</small>';
        out.appendChild(row);
      });
    }

    [['Methodology', data.methodology || []], ['Hidden from public pages', data.hidden || []], ['Review notes', data.review_notes || []]].forEach(function (group) {
      if (!group[1].length) return;
      const h = document.createElement('h3');
      h.textContent = group[0];
      out.appendChild(h);
      const ul = document.createElement('ul');
      ul.className = 'scsi-list scsi-public-notes';
      group[1].forEach(function (item) { const li = document.createElement('li'); li.textContent = item; ul.appendChild(li); });
      out.appendChild(ul);
    });
  }




  function sourceAwareBriefPanelEndpoint(panel) {
    const map = {
      'directory': '/public-source-aware-brief-panel?panel=directory',
      'site-intelligence': '/public-source-aware-brief-panel?panel=site-intelligence',
      'indicator': '/public-source-aware-brief-panel?panel=indicator',
      'source-health': '/public-source-aware-brief-panel?panel=source-health'
    };
    return map[panel] || '/public-source-aware-brief-panel?panel=directory';
  }

  function dashboardExportPanelEndpoint(panel) {
    const map = {
      'manifest': '/public-dashboard-export-panel?panel=manifest',
      'site-intelligence': '/public-dashboard-export-panel?panel=site-intelligence',
      'indicator': '/public-dashboard-export-panel?panel=indicator',
      'source-health': '/public-dashboard-export-panel?panel=source-health',
      'visual-qa': '/public-dashboard-export-panel?panel=visual-qa'
    };
    return map[panel] || '/public-dashboard-export-panel?panel=manifest';
  }

  function renderPublicSourceAwareBriefPanel(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = (data.summary || 'Public source-aware brief.') + ' · Status: ' + (data.public_status || 'review');
    out.innerHTML = '';

    const briefs = data.briefs || [];
    if (briefs.length) {
      const grid = document.createElement('div');
      grid.className = 'scsi-grid scsi-public-brief-grid';
      briefs.forEach(function (item) {
        const card = document.createElement('div');
        card.className = 'scsi-page-row scsi-public-brief-card';
        card.innerHTML = '<strong>' + escapeHtml(item.title || item.slug || '') + '</strong><br>' +
          '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.recommended_shortcode || '') + '</span>' +
          '<small>' + escapeHtml(item.summary || '') + '</small>' +
          '<small><b>Path:</b> ' + escapeHtml(item.brief_path || '') + '</small>';
        grid.appendChild(card);
      });
      out.appendChild(grid);
    }

    const findings = data.key_findings || [];
    if (findings.length) {
      const h = document.createElement('h3');
      h.textContent = 'Key findings';
      out.appendChild(h);
      const ul = document.createElement('ul');
      ul.className = 'scsi-list scsi-public-notes';
      findings.forEach(function (item) { const li = document.createElement('li'); li.textContent = item; ul.appendChild(li); });
      out.appendChild(ul);
    }

    const actions = data.recommended_actions || [];
    if (actions.length) {
      const h = document.createElement('h3');
      h.textContent = 'Recommended actions';
      out.appendChild(h);
      const ul = document.createElement('ul');
      ul.className = 'scsi-list scsi-public-notes';
      actions.forEach(function (item) { const li = document.createElement('li'); li.textContent = item; ul.appendChild(li); });
      out.appendChild(ul);
    }

    const citations = data.source_citations || [];
    if (citations.length) {
      const h = document.createElement('h3');
      h.textContent = 'Public source endpoints';
      out.appendChild(h);
      citations.forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-public-source-citation-row';
        row.innerHTML = '<strong>' + escapeHtml(item.title || '') + '</strong><br>' +
          '<code>' + escapeHtml(item.endpoint || '') + '</code>' +
          '<small>' + escapeHtml(item.note || '') + '</small>';
        out.appendChild(row);
      });
    }

    [['Citation policy', data.citation_policy || []], ['Hidden from public pages', data.hidden || []]].forEach(function (group) {
      if (!group[1].length) return;
      const h = document.createElement('h3');
      h.textContent = group[0];
      out.appendChild(h);
      const ul = document.createElement('ul');
      ul.className = 'scsi-list scsi-public-notes';
      group[1].forEach(function (item) { const li = document.createElement('li'); li.textContent = item; ul.appendChild(li); });
      out.appendChild(ul);
    });
  }

  function renderPublicDashboardExportPanel(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = (data.summary || 'Public dashboard export.') + ' · Status: ' + (data.public_status || 'review');
    out.innerHTML = '';

    const exports = data.exports || [];
    if (exports.length) {
      const grid = document.createElement('div');
      grid.className = 'scsi-grid scsi-public-export-grid';
      exports.forEach(function (item) {
        const card = document.createElement('div');
        card.className = 'scsi-page-row scsi-public-export-card';
        card.innerHTML = '<strong>' + escapeHtml(item.title || item.slug || '') + '</strong><br>' +
          '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.recommended_shortcode || '') + '</span>' +
          '<small>' + escapeHtml(item.summary || '') + '</small>' +
          '<small><b>Endpoint:</b> ' + escapeHtml(item.endpoint || '') + '</small>';
        grid.appendChild(card);
      });
      out.appendChild(grid);
    }

    const bundle = data.export_bundle || {};
    if (bundle.json) {
      const h = document.createElement('h3');
      h.textContent = 'Export summary';
      out.appendChild(h);
      const box = document.createElement('div');
      box.className = 'scsi-page-row scsi-public-export-summary';
      const findings = (bundle.json.key_findings || []).slice(0, 4).map(function (item) { return '<li>' + escapeHtml(item) + '</li>'; }).join('');
      box.innerHTML = '<strong>' + escapeHtml(bundle.json.title || data.title || '') + '</strong><p>' + escapeHtml(bundle.json.summary || '') + '</p><ul>' + findings + '</ul>';
      out.appendChild(box);
    }

    if (bundle.markdown) {
      const h = document.createElement('h3');
      h.textContent = 'Copy-ready Markdown';
      out.appendChild(h);
      const pre = document.createElement('pre');
      pre.className = 'scsi-public-export-markdown';
      pre.textContent = bundle.markdown;
      out.appendChild(pre);
    }

    const citations = data.source_citations || [];
    if (citations.length) {
      const h = document.createElement('h3');
      h.textContent = 'Public source endpoints';
      out.appendChild(h);
      citations.forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-public-source-citation-row';
        row.innerHTML = '<strong>' + escapeHtml(item.title || '') + '</strong><br>' +
          '<code>' + escapeHtml(item.endpoint || '') + '</code>' +
          '<small>' + escapeHtml(item.note || '') + '</small>';
        out.appendChild(row);
      });
    }

    const checks = data.checks || [];
    if (checks.length) {
      const h = document.createElement('h3');
      h.textContent = 'Export QA checks';
      out.appendChild(h);
      checks.forEach(function (check) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-public-qa-row';
        row.innerHTML = '<strong>' + escapeHtml(check.label || check.id || '') + '</strong><br>' +
          statusBadge(check.status || 'review') + '<small>' + escapeHtml(check.detail || '') + '</small>';
        out.appendChild(row);
      });
    }
  }

  function connectorPanelEndpoint(panel, root) {
    const map = {
      'connector-status': '/public-connector-status',
      'connector-operations': '/public-connector-operations',
      'temporal-intelligence': '/public-temporal-intelligence',
      'spatial-evidence': '/public-spatial-evidence',
      'comparable-series': '/public-comparable-series',
      'model-forecasts': '/public-model-forecasts',
      'monitoring-digests': '/public-monitoring-digests',
      'institutional-workspaces': '/public-institutional-workspaces',
      'cross-platform-workflows': '/public-cross-platform-workflows',
      'institutional-data-exchange': '/public-institutional-data-exchange',
      'production-governance': '/public-production-governance',
      'connected-intelligence': '/connected-public-intelligence',
      'cache-status': '/public-cache-status',
      'source-freshness': '/public-source-freshness',
      'connector-reliability': '/public-connector-reliability',
      'connector-status-polish': '/public-connector-status-polish',
      'world-bank': '/public-connector-detail?slug=world-bank',
      'openalex': '/public-connector-detail?slug=openalex',
      'crossref': '/public-connector-detail?slug=crossref',
      'github': '/public-connector-detail?slug=github',
      'environmental': '/public-connector-detail?slug=environmental',
      'sustainable-development-sources': '/public-sustainable-development-sources',
      'sustainable-development-families': '/public-sustainable-development-families',
      'planetary-boundaries': '/public-planetary-boundaries-registry',
      'sustainable-development-health': '/public-sustainable-development-source-health',
      'sustainable-development-methodology': '/public-sustainable-development-methodology',
      'sustainable-development-reliability': '/public-sustainable-development-connector-reliability',
      'sustainable-development-freshness': '/public-sustainable-development-freshness',
      'sustainable-development-schema-validation': '/public-sustainable-development-schema-validation',
      'sustainable-development-cache': '/public-sustainable-development-cache-status',
      'planetary-boundaries-observatory': '/public-planetary-boundaries-observatory',
      'planetary-boundary-sources': '/public-planetary-boundary-sources',
      'planetary-boundary-methodology': '/public-planetary-boundary-methodology',
      'planetary-boundary-export': '/public-planetary-boundary-export',
      'planetary-boundary-detail': '/public-planetary-boundary',
      'planetary-boundary-trend': '/public-planetary-boundary-trend',
      'humanitarian-intelligence': '/public-humanitarian-intelligence',
      'humanitarian-crisis-map': '/public-humanitarian-crisis-map',
      'humanitarian-reports': '/public-humanitarian-reports',
      'displacement-context': '/public-displacement-context',
      'humanitarian-sources': '/public-humanitarian-intelligence-sources',
      'humanitarian-methodology': '/public-humanitarian-intelligence-methodology',
      'humanitarian-export': '/public-humanitarian-intelligence-export',
      'human-development': '/public-human-development',
      'human-development-sources': '/public-human-development-sources',
      'human-development-domain': '/public-human-development-domain',
      'human-development-country-profile': '/public-human-development-country-profile',
      'human-development-inequalities': '/public-human-development-inequalities',
      'human-development-methodology': '/public-human-development-methodology',
      'human-development-export': '/public-human-development-export',
      'international-law': '/public-international-law',
      'international-law-sources': '/public-international-law-sources',
      'international-law-sanctions': '/public-international-law-sanctions',
      'international-law-events': '/public-international-law-events',
      'international-law-monitor': '/public-international-law-monitor',
      'international-law-methodology': '/public-international-law-methodology',
      'international-law-export': '/public-international-law-export',
      'human-security': '/public-human-security',
      'human-security-sources': '/public-human-security-sources',
      'human-security-events': '/public-human-security-events',
      'human-security-monitor': '/public-human-security-monitor',
      'human-security-displacement': '/public-human-security-displacement',
      'human-security-modeled-risk': '/public-human-security-modeled-risk',
      'human-security-methodology': '/public-human-security-methodology',
      'human-security-export': '/public-human-security-export',
      'cross-domain-dashboard-studio': '/public-cross-domain-dashboards',
      'dashboard-launch-manifest': '/public-dashboard-launch-manifest',
      'dashboard-launch-readiness': '/public-dashboard-launch-readiness',
      'dashboard-public-navigation': '/public-dashboard-studio-navigation',
      'cross-domain-dashboard-directory': '/public-cross-domain-dashboards',
      'cross-domain-dashboard': '/public-cross-domain-dashboard',
      'cross-domain-dashboard-sources': '/public-cross-domain-dashboard-sources',
      'cross-domain-dashboard-export': '/public-cross-domain-dashboard-export',
      'country-intelligence': '/public-country-intelligence',
      'cross-domain-comparison': '/public-cross-domain-comparison'
    };
    let endpoint = map[panel] || '/public-connector-status';
    const boundaryId = root && root.dataset ? (root.dataset.boundaryId || '') : '';
    if (boundaryId && (panel === 'planetary-boundary-detail' || panel === 'planetary-boundary-trend')) endpoint += '?id=' + encodeURIComponent(boundaryId);
    const domainId = root && root.dataset ? (root.dataset.domainId || '') : '';
    const country = root && root.dataset ? (root.dataset.country || '') : '';
    if (domainId && panel === 'human-development-domain') endpoint += '?id=' + encodeURIComponent(domainId);
    if (country && panel === 'human-development-country-profile') endpoint += '?country=' + encodeURIComponent(country);
    var monitorId = root && root.getAttribute ? (root.getAttribute('data-monitor-id') || '') : '';
    var eventType = root && root.getAttribute ? (root.getAttribute('data-event-type') || '') : '';
    var jurisdiction = root && root.getAttribute ? (root.getAttribute('data-jurisdiction') || '') : '';
    if (monitorId && panel === 'international-law-monitor') endpoint += '?id=' + encodeURIComponent(monitorId);
    if (monitorId && panel === 'human-security-monitor') endpoint += '?id=' + encodeURIComponent(monitorId);
    if (panel === 'human-security-events') {
      var humanParams = [];
      var recordType = root.getAttribute('data-record-type') || '';
      var humanCountry = root.getAttribute('data-country') || '';
      if (recordType) humanParams.push('record_type=' + encodeURIComponent(recordType));
      if (humanCountry) humanParams.push('country=' + encodeURIComponent(humanCountry));
      if (humanParams.length) endpoint += '?' + humanParams.join('&');
    }
    if (panel.indexOf('cross-domain') === 0 || panel === 'country-intelligence') {
      var crossParams = [];
      var dashboardId = root.getAttribute('data-dashboard-id') || '';
      var crossCountry = root.getAttribute('data-country') || '';
      var crossRegion = root.getAttribute('data-region') || '';
      var crossCompare = root.getAttribute('data-compare') || '';
      var crossView = root.getAttribute('data-view') || '';
      if (dashboardId) crossParams.push('id=' + encodeURIComponent(dashboardId));
      if (crossCountry) crossParams.push('country=' + encodeURIComponent(crossCountry));
      if (crossRegion) crossParams.push('region=' + encodeURIComponent(crossRegion));
      if (crossCompare) crossParams.push('compare=' + encodeURIComponent(crossCompare));
      if (crossView) crossParams.push('view=' + encodeURIComponent(crossView));
      if (crossParams.length) endpoint += '?' + crossParams.join('&');
    }
    if (panel === 'international-law-events') {
      var query = [];
      if (eventType) query.push('event_type=' + encodeURIComponent(eventType));
      if (jurisdiction) query.push('jurisdiction=' + encodeURIComponent(jurisdiction));
      if (query.length) endpoint += '?' + query.join('&');
    }
    return endpoint;
  }

  function renderConnectorRuntime(item) {
    const runtime = item.runtime || {};
    const reliability = item.reliability || {};
    const bits = [];
    if (runtime.status_label) bits.push('<span class="scsi-badge scsi-badge-soft">' + escapeHtml(runtime.status_label) + '</span>');
    if (runtime.reliability_level) bits.push('<span class="scsi-badge scsi-badge-' + escapeHtml(runtime.reliability_level) + '">' + escapeHtml(runtime.reliability_level) + '</span>');
    if (runtime.display_mode) bits.push('<span class="scsi-badge scsi-badge-soft">' + escapeHtml(runtime.display_mode) + '</span>');
    if (runtime.cache_state) bits.push('<small><b>Cache state:</b> ' + escapeHtml(runtime.cache_state) + '</small>');
    if (runtime.freshness_state) bits.push('<small><b>Freshness state:</b> ' + escapeHtml(runtime.freshness_state) + '</small>');
    if (runtime.cache_ttl_seconds) bits.push('<small><b>Cache TTL:</b> ' + formatNumber(runtime.cache_ttl_seconds) + ' seconds</small>');
    if (runtime.next_refresh_after) bits.push('<small><b>Next refresh after:</b> ' + escapeHtml(runtime.next_refresh_after) + '</small>');
    if (item.freshness_window) bits.push('<small><b>Freshness:</b> ' + escapeHtml(item.freshness_window) + '</small>');
    if (reliability.public_message) bits.push('<small><b>Public status:</b> ' + escapeHtml(reliability.public_message) + '</small>');
    if (runtime.recovery_action) bits.push('<small><b>Display guidance:</b> ' + escapeHtml(runtime.recovery_action) + '</small>');
    return bits.join('');
  }



  function setPublicConnectorLoading(root, isLoading) {
    if (!root) return;
    root.classList.toggle('scsi-is-loading', Boolean(isLoading));
    root.setAttribute('aria-busy', isLoading ? 'true' : 'false');

    if (!isLoading) {
      const loadingShell = root.querySelector('.scsi-loading-shell');
      if (loadingShell) {
        loadingShell.hidden = true;
        loadingShell.setAttribute('aria-hidden', 'true');
        loadingShell.remove();
      }
    }
  }

  function finishPublicConnectorLoading(root) {
    setPublicConnectorLoading(root, false);
  }

  function publicStateLabel(data) {
    const state = String(data.origin_state || data.data_state || '').toLowerCase();
    if (state.indexOf('fallback') !== -1) return 'Local fallback';
    if (state.indexOf('stale') !== -1) return 'Last-known-good data';
    if (state.indexOf('cache') !== -1) return 'Cached public data';
    if (state.indexOf('backend') !== -1 || state.indexOf('live') !== -1) return 'Connected public sources';
    return 'Source-aware public view';
  }

  function sourceChips(sources) {
    if (!sources || !sources.length) return '';
    return '<div class="scsi-source-chips">' + sources.slice(0, 5).map(function (source) {
      return '<span>' + escapeHtml(source) + '</span>';
    }).join('') + '</div>';
  }

  function renderCountryPublic(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const country = data.country_name || data.country_code || 'Selected country';
    muted.textContent = publicStateLabel(data) + (data.generated_at ? ' · Updated ' + data.generated_at : '');
    out.innerHTML = '';

    const hero = document.createElement('div');
    hero.className = 'scsi-country-public-hero';
    hero.innerHTML = '<div><span class="scsi-public-label">Country profile</span><h3>' + escapeHtml(country) + '</h3>' +
      '<p>' + escapeHtml(data.summary || 'Cross-domain public evidence and source context.') + '</p></div>' +
      '<div class="scsi-country-code">' + escapeHtml(data.country_code || '') + '</div>';
    out.appendChild(hero);

    const controls = document.createElement('div');
    controls.className = 'scsi-country-controls';
    controls.innerHTML = '<label>Country<select data-scsi-country-select><option value="KEN">Kenya</option><option value="GHA">Ghana</option><option value="USA">United States</option></select></label>' +
      '<button type="button" class="scsi-public-action" data-scsi-load-country>Load profile</button>';
    const select = controls.querySelector('select');
    if (select && data.country_code) select.value = data.country_code;
    controls.querySelector('[data-scsi-load-country]').addEventListener('click', function () {
      const code = select.value;
      root.setAttribute('data-country', code);
      setPublicConnectorLoading(root, true);
      fetchJson(cfg.restBase + '/public-country-intelligence?country=' + encodeURIComponent(code))
        .then(function (payload) { renderPublicConnectorPanel(root, payload); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load country profile.'); })
        .finally(function () { finishPublicConnectorLoading(root); });
    });
    out.appendChild(controls);

    const grid = document.createElement('div');
    grid.className = 'scsi-public-domain-grid';
    (data.evidence_items || data.domains || []).forEach(function (item) {
      const card = document.createElement('article');
      card.className = 'scsi-public-domain-card';
      card.innerHTML = '<span class="scsi-public-label">' + escapeHtml(item.label || item.domain || 'Evidence domain') + '</span>' +
        '<h4>' + escapeHtml(item.description || 'Public evidence and source context') + '</h4>' +
        '<p class="scsi-domain-state">' + (item.value_status ? escapeHtml(item.value_status) : 'Validated values appear when available.') + '</p>' +
        sourceChips(item.sources || []);
      grid.appendChild(card);
    });
    out.appendChild(grid);

    const note = document.createElement('div');
    note.className = 'scsi-public-callout';
    note.innerHTML = '<strong>Interpretation</strong><p>Country profiles are evidence summaries, not rankings. Missing values remain visible and are not silently imputed.</p>';
    out.appendChild(note);
  }

  function renderDashboardPublic(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = publicStateLabel(data) + (data.generated_at ? ' · Updated ' + data.generated_at : '');
    out.innerHTML = '';
    const intro = document.createElement('div');
    intro.className = 'scsi-public-dashboard-intro';
    intro.innerHTML = '<span class="scsi-public-label">Cross-domain dashboard</span><h3>' + escapeHtml(data.title || 'Public Intelligence Dashboard') + '</h3><p>' + escapeHtml(data.summary || '') + '</p>';
    out.appendChild(intro);
    const grid = document.createElement('div'); grid.className = 'scsi-public-domain-grid';
    (data.evidence_items || []).forEach(function(item){
      const card=document.createElement('article'); card.className='scsi-public-domain-card';
      card.innerHTML='<span class="scsi-public-label">'+escapeHtml(item.label || item.domain)+'</span><h4>'+escapeHtml(item.description || '')+'</h4><p class="scsi-domain-state">'+escapeHtml(item.value_status || 'Validated values appear when available.')+'</p>'+sourceChips(item.sources || []);
      grid.appendChild(card);
    });
    out.appendChild(grid);
    const summary=data.source_summary || {};
    const footer=document.createElement('div'); footer.className='scsi-public-summary-strip';
    footer.innerHTML='<div><strong>'+escapeHtml(summary.domains || (data.evidence_items||[]).length)+'</strong><span>domains</span></div><div><strong>'+escapeHtml(summary.registered_sources || 0)+'</strong><span>registered sources</span></div><div><strong>'+escapeHtml(summary.freshness || 'source dependent')+'</strong><span>freshness</span></div>';
    out.appendChild(footer);
  }

  function renderComparisonPublic(root, data) {
    const out=root.querySelector('.scsi-output'); const muted=root.querySelector('.scsi-muted');
    muted.textContent=publicStateLabel(data)+(data.generated_at?' · Updated '+data.generated_at:''); out.innerHTML='';
    const countries=data.countries || [];
    const intro=document.createElement('div'); intro.className='scsi-public-dashboard-intro';
    intro.innerHTML='<span class="scsi-public-label">Country comparison</span><h3>'+escapeHtml((countries[0]||'Country A')+' and '+(countries[1]||'Country B'))+'</h3><p>'+escapeHtml(data.normalization_rule || data.summary || '')+'</p>';
    out.appendChild(intro);
    const table=document.createElement('div'); table.className='scsi-comparison-table';
    table.innerHTML='<div class="scsi-comparison-head"><span>Dimension</span><span>'+escapeHtml(countries[0]||'Country A')+'</span><span>'+escapeHtml(countries[1]||'Country B')+'</span></div>';
    (data.comparison_rows || []).forEach(function(row){
      const left=row.left||{}, right=row.right||{}; const el=document.createElement('div'); el.className='scsi-comparison-line';
      el.innerHTML='<strong>'+escapeHtml(String(row.dimension||'').replace(/-/g,' '))+'</strong><span>'+escapeHtml(left.value == null ? 'No validated public value is currently available.' : left.value)+'</span><span>'+escapeHtml(right.value == null ? 'No validated public value is currently available.' : right.value)+'</span>';
      table.appendChild(el);
    }); out.appendChild(table);
  }

  function renderCuratedDirectory(root, data) {
    const out=root.querySelector('.scsi-output'); const muted=root.querySelector('.scsi-muted');
    muted.textContent='Curated public navigation'; out.innerHTML='';
    const groups=[
      ['Flagship dashboards', [
        ['Climate and Human Vulnerability','/platform/site-intelligence/dashboard-studio/climate-human-vulnerability/'],
        ['Conflict and Human Development','/platform/site-intelligence/dashboard-studio/conflict-human-development/'],
        ['International Law and Humanitarian Conditions','/platform/site-intelligence/dashboard-studio/international-law-humanitarian-conditions/']]],
      ['Country tools', [['Country Intelligence','/platform/site-intelligence/country-intelligence/'],['Cross-Domain Comparison','/platform/site-intelligence/cross-domain-comparison/']]],
      ['Observatories', [['Climate + Energy','/platform/site-intelligence/climate-energy/'],['Planetary Boundaries','/platform/site-intelligence/planetary-boundaries/'],['Humanitarian Intelligence','/platform/site-intelligence/humanitarian-intelligence/'],['Human Development','/platform/site-intelligence/human-development/'],['International Law + Governance','/platform/site-intelligence/international-law-global-governance/'],['Conflict + Displacement','/platform/site-intelligence/conflict-displacement-human-security/']]],
      ['Methods', [['Source Methodology','/platform/site-intelligence/source-methodology/'],['Launch Readiness','/platform/site-intelligence/launch-readiness/']]]
    ];
    groups.forEach(function(group){
      const section=document.createElement('section'); section.className='scsi-directory-group'; section.innerHTML='<h3>'+escapeHtml(group[0])+'</h3>';
      const grid=document.createElement('div'); grid.className='scsi-directory-grid';
      group[1].forEach(function(item){ const a=document.createElement('a'); a.href=item[1]; a.className='scsi-directory-link'; a.innerHTML='<strong>'+escapeHtml(item[0])+'</strong><span>Open view →</span>'; grid.appendChild(a); });
      section.appendChild(grid); out.appendChild(section);
    });
  }

  function renderPublicConnectorPanel(root, data) {
    finishPublicConnectorLoading(root);
    root.classList.add('scsi-is-ready');
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const origin = data.origin_state || data.data_state || data.public_status || data.version_scope || 'review';
    muted.textContent = (data.summary || data.title || 'Source-aware public intelligence view.') + ' · Data state: ' + origin;
    out.innerHTML = '';

    const publicPanel = root.dataset.connectorPanel || '';
    if (publicPanel === 'country-intelligence') { renderCountryPublic(root, data); return; }
    if (publicPanel === 'cross-domain-dashboard') { renderDashboardPublic(root, data); return; }
    if (publicPanel === 'cross-domain-comparison') { renderComparisonPublic(root, data); return; }
    if (publicPanel === 'cross-domain-dashboard-directory' || publicPanel === 'cross-domain-dashboard-studio') { renderCuratedDirectory(root, data); return; }

    if (data.evidence_items || data.comparison_rows) {
      if (data.country_name || data.countries) {
        const heading = document.createElement('div');
        heading.className = 'scsi-page-row scsi-public-summary-row';
        heading.innerHTML = '<strong>' + escapeHtml(data.country_name || (data.countries || []).join(' compared with ')) + '</strong>' +
          '<small>Generated: ' + escapeHtml(data.generated_at || 'not supplied') + '</small>';
        out.appendChild(heading);
      }
      if (data.source_summary) {
        const stats = document.createElement('div');
        stats.className = 'scsi-grid scsi-public-connector-health-grid';
        [['Domains', data.source_summary.domains], ['Registered sources', data.source_summary.registered_sources], ['Freshness', data.source_summary.freshness]].forEach(function (item) {
          if (typeof item[1] === 'undefined') return;
          const card = document.createElement('div'); card.className = 'scsi-stat scsi-public-connector-status-card';
          card.innerHTML = '<span class="scsi-public-label">' + escapeHtml(item[0]) + '</span><strong>' + escapeHtml(item[1]) + '</strong>';
          stats.appendChild(card);
        });
        if (stats.children.length) out.appendChild(stats);
      }
      (data.evidence_items || []).forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-public-evidence-row';
        const sources = (item.sources || []).slice(0, 6).join(', ');
        row.innerHTML = '<strong>' + escapeHtml(item.label || item.domain || 'Evidence domain') + '</strong>' +
          '<small>' + escapeHtml(item.description || '') + '</small>' +
          '<small><b>Data state:</b> ' + escapeHtml(item.data_state || 'source-dependent') + ' · <b>Freshness:</b> ' + escapeHtml(item.freshness || 'unknown') + '</small>' +
          (sources ? '<small><b>Sources:</b> ' + escapeHtml(sources) + '</small>' : '') +
          (item.value_status ? '<small>' + escapeHtml(item.value_status) + '</small>' : '');
        out.appendChild(row);
      });
      (data.comparison_rows || []).forEach(function (item) {
        const row = document.createElement('div'); row.className = 'scsi-page-row scsi-public-comparison-row';
        const left = item.left || {}, right = item.right || {};
        row.innerHTML = '<strong>' + escapeHtml(item.dimension || 'Comparison dimension') + '</strong>' +
          '<small>' + escapeHtml(left.country || '') + ': ' + escapeHtml(left.value === null || typeof left.value === 'undefined' ? left.data_state || 'unavailable' : left.value) +
          ' · ' + escapeHtml(right.country || '') + ': ' + escapeHtml(right.value === null || typeof right.value === 'undefined' ? right.data_state || 'unavailable' : right.value) + '</small>' +
          '<small>' + escapeHtml(item.display_note || '') + '</small>';
        out.appendChild(row);
      });
      (data.notes || data.governance || []).forEach(function (note) { const row=document.createElement('div'); row.className='scsi-page-row'; row.innerHTML='<small>'+escapeHtml(note)+'</small>'; out.appendChild(row); });
      return;
    }

    if (data.summary_cards || data.domains || data.comparison_dimensions) {
      const grid = document.createElement('div');
      grid.className = 'scsi-grid scsi-public-connector-health-grid';
      (data.summary_cards || data.domains || []).forEach(function (item) {
        const card = document.createElement('div');
        card.className = 'scsi-stat scsi-public-connector-status-card';
        card.innerHTML = '<span class="scsi-public-label">' + escapeHtml(item.domain || item.label || 'Domain') + '</span>' +
          '<strong>' + escapeHtml(item.status || item.display_state || 'available') + '</strong>' +
          '<small><b>Freshness:</b> ' + escapeHtml(item.freshness || 'mixed') + '</small>';
        grid.appendChild(card);
      });
      if (grid.children.length) out.appendChild(grid);
      (data.notes || data.governance || []).forEach(function (note) { const row=document.createElement('div'); row.className='scsi-page-row'; row.innerHTML='<small>'+escapeHtml(note)+'</small>'; out.appendChild(row); });
      return;
    }

    if (typeof data.score !== 'undefined' || data.counts) {
      const grid = document.createElement('div');
      grid.className = 'scsi-grid scsi-public-connector-health-grid';
      if (typeof data.score !== 'undefined') {
        const score = document.createElement('div');
        score.className = 'scsi-stat scsi-public-connector-status-card';
        score.innerHTML = '<span class="scsi-public-label">Readiness</span><strong>' + formatNumber(data.score || 0) + '%</strong><small>Public-safe connector readiness score.</small>';
        grid.appendChild(score);
      }
      Object.keys(data.counts || {}).forEach(function (key) {
        const card = document.createElement('div');
        card.className = 'scsi-stat scsi-public-connector-status-card';
        card.innerHTML = '<span class="scsi-public-label">' + escapeHtml(key) + '</span>' +
          '<strong>' + formatNumber(data.counts[key]) + '</strong>' +
          '<small>' + escapeHtml((data.status_definitions || {})[key] || 'Connector count.') + '</small>';
        grid.appendChild(card);
      });
      out.appendChild(grid);
    }

    if (data.reliability_counts) {
      const hRel = document.createElement('h3');
      hRel.textContent = 'Reliability labels';
      out.appendChild(hRel);
      const relGrid = document.createElement('div');
      relGrid.className = 'scsi-grid scsi-public-connector-health-grid scsi-public-reliability-grid';
      Object.keys(data.reliability_counts || {}).forEach(function (key) {
        const card = document.createElement('div');
        card.className = 'scsi-stat scsi-public-connector-status-card';
        card.innerHTML = '<span class="scsi-public-label">' + escapeHtml(key) + '</span>' +
          '<strong>' + formatNumber(data.reliability_counts[key]) + '</strong>' +
          '<small>' + escapeHtml((data.reliability_definitions || {})[key] || 'Public reliability count.') + '</small>';
        relGrid.appendChild(card);
      });
      out.appendChild(relGrid);
    }

    const statusCards = data.status_cards || [];
    if (statusCards.length) {
      const hCards = document.createElement('h3');
      hCards.textContent = 'Public status cards';
      out.appendChild(hCards);
      statusCards.forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-public-connector-row scsi-public-status-card-row';
        row.innerHTML = '<strong>' + escapeHtml(item.label || item.slug || '') + '</strong><br>' +
          statusBadge(item.status || 'planned') + '<span class="scsi-badge scsi-badge-' + escapeHtml(item.reliability_level || 'planned') + '">' + escapeHtml(item.reliability_level || 'planned') + '</span>' +
          '<small><b>Display mode:</b> ' + escapeHtml(item.display_mode || '') + '</small>' +
          '<small><b>Cache state:</b> ' + escapeHtml(item.cache_state || '') + '</small>' +
          '<small><b>Freshness state:</b> ' + escapeHtml(item.freshness_state || '') + '</small>' +
          '<small><b>Recovery action:</b> ' + escapeHtml(item.recovery_action || '') + '</small>';
        out.appendChild(row);
      });
    }

    const connectors = data.connectors || (data.connector ? [data.connector] : []);
    if (connectors.length) {
      const h = document.createElement('h3');
      h.textContent = data.connector ? 'Connector detail' : 'Connector families';
      out.appendChild(h);
      connectors.forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-public-connector-row';
        row.innerHTML = '<strong>' + escapeHtml(item.label || item.name || item.slug || item.connector_id || '') + '</strong><br>' +
          statusBadge(item.operational_status || item.status || item.public_status || 'planned') + '<span class="scsi-badge scsi-badge-soft">' + escapeHtml(item.source_mode || item.family || 'public_connector') + '</span>' +
          '<small><b>Family:</b> ' + escapeHtml(item.family || '') + '</small>' +
          (item.provider ? '<small><b>Provider:</b> ' + escapeHtml(item.provider) + '</small>' : '') +
          (item.freshness_state ? '<small><b>Freshness:</b> ' + escapeHtml(item.freshness_state) + '</small>' : '') +
          (item.last_success_at ? '<small><b>Last success:</b> ' + escapeHtml(item.last_success_at) + '</small>' : '') +
          '<small><b>Public use:</b> ' + escapeHtml(item.public_use || item.public_note || '') + '</small>' +
          (item.safe_display ? '<small><b>Safe display:</b> ' + escapeHtml(item.safe_display) + '</small>' : '') +
          (item.fallback_reason ? '<small><b>Fallback:</b> ' + escapeHtml(item.fallback_reason) + '</small>' : '') +
          renderConnectorRuntime(item);
        out.appendChild(row);
      });
    }

    const policies = data.policies || [];
    if (policies.length) {
      const h = document.createElement('h3');
      h.textContent = 'Cache policies';
      out.appendChild(h);
      policies.forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-public-connector-row';
        row.innerHTML = '<strong>' + escapeHtml(item.label || item.slug || '') + '</strong><br>' +
          '<small><b>Display mode:</b> ' + escapeHtml(item.display_mode || '') + '</small>' +
          '<small><b>Reliability:</b> ' + escapeHtml(item.reliability_level || '') + '</small>' +
          '<small><b>Cache state:</b> ' + escapeHtml(item.cache_state || '') + '</small>' +
          '<small><b>Cache TTL:</b> ' + formatNumber(item.cache_ttl_seconds || 0) + ' seconds</small>' +
          '<small><b>Stale TTL:</b> ' + formatNumber(item.stale_ttl_seconds || 0) + ' seconds</small>' +
          '<small><b>Next refresh after:</b> ' + escapeHtml(item.next_refresh_after || '') + '</small>' +
          '<small><b>Recovery action:</b> ' + escapeHtml(item.recovery_action || '') + '</small>';
        out.appendChild(row);
      });
    }

    const freshness = data.freshness || [];
    if (freshness.length) {
      const h = document.createElement('h3');
      h.textContent = 'Freshness labels';
      out.appendChild(h);
      freshness.forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-public-connector-row';
        row.innerHTML = '<strong>' + escapeHtml(item.label || item.slug || '') + '</strong><br>' +
          statusBadge(item.status || 'planned') +
          '<small><b>Freshness:</b> ' + escapeHtml(item.freshness_window || '') + '</small>' +
          '<small><b>Reliability:</b> ' + escapeHtml(item.reliability_level || '') + '</small>' +
          '<small><b>Freshness state:</b> ' + escapeHtml(item.freshness_state || '') + '</small>' +
          '<small><b>Next refresh after:</b> ' + escapeHtml(item.next_refresh_after || '') + '</small>' +
          '<small>' + escapeHtml(item.public_note || '') + '</small>';
        out.appendChild(row);
      });
    }

    const subconnectors = data.subconnectors || [];
    if (subconnectors.length) {
      const h = document.createElement('h3');
      h.textContent = 'Environmental subconnectors';
      out.appendChild(h);
      subconnectors.forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'scsi-page-row scsi-public-connector-row';
        row.innerHTML = '<strong>' + escapeHtml(item.label || '') + '</strong><br>' +
          statusBadge(item.status || 'planned') + '<span class="scsi-badge scsi-badge-soft">Credential: ' + escapeHtml(String(item.credential_required)) + '</span>' +
          '<small>' + escapeHtml(item.public_use || '') + '</small>';
        out.appendChild(row);
      });
    }

    const families = data.families || [];
    if (families.length) {
      const h = document.createElement('h3'); h.textContent = 'Connector families'; out.appendChild(h);
      families.forEach(function (item) { const row=document.createElement('div'); row.className='scsi-page-row'; row.innerHTML='<strong>'+escapeHtml(item.family||'')+'</strong><small><b>Sources:</b> '+escapeHtml((item.sources||[]).join(', '))+'</small>'; out.appendChild(row); });
    }
    const boundaries = data.boundaries || (data.boundary ? [data.boundary] : []);
    if (boundaries.length) {
      const h = document.createElement('h3'); h.textContent = data.boundary ? 'Boundary detail' : 'Planetary boundaries'; out.appendChild(h);
      boundaries.forEach(function (item) {
        const controls=(item.control_variables||[]).map(function(v){ return typeof v === 'string' ? v : (v.label || v.id || ''); });
        const sources=(item.sources||[]).map(function(v){ return v.title || v.source_id || ''; });
        const row=document.createElement('div'); row.className='scsi-page-row scsi-planetary-boundary-row';
        row.innerHTML='<strong>'+escapeHtml(item.label||item.boundary_id||'')+'</strong><br>'+statusBadge(item.status||item.assessment_status||'planned')+
          '<span class="scsi-badge scsi-badge-soft">'+escapeHtml(item.status_label||item.scientific_status_label||'')+'</span>'+
          '<small>'+escapeHtml(item.summary||'')+'</small><small><b>Coverage:</b> '+escapeHtml(item.coverage||item.assessment_status||'')+'</small>'+
          '<small><b>Control variables:</b> '+escapeHtml(controls.join(', '))+'</small><small><b>Sources:</b> '+escapeHtml((sources.length?sources:(item.source_mappings||[])).join(', '))+'</small>'+
          '<small><b>SDGs:</b> '+escapeHtml((item.sdg_goals||[]).join(', '))+'</small>';
        out.appendChild(row);
      });
    }
    const milestones = data.milestones || [];
    if (milestones.length) {
      const h=document.createElement('h3'); h.textContent='Assessment milestones'; out.appendChild(h);
      milestones.forEach(function(item){ const row=document.createElement('div'); row.className='scsi-page-row'; row.innerHTML='<strong>'+escapeHtml(String(item.year||''))+' · '+escapeHtml(item.label||'')+'</strong><small>'+escapeHtml(item.note||'')+'</small>'; out.appendChild(row); });
    }
    const references = data.references || [];
    if (references.length) {
      const h=document.createElement('h3'); h.textContent='Scientific references'; out.appendChild(h);
      references.forEach(function(item){ const row=document.createElement('div'); row.className='scsi-page-row'; row.innerHTML='<strong>'+escapeHtml(item.title||'')+'</strong><small>'+escapeHtml(item.organization||'')+' · '+escapeHtml(item.role||'')+'</small>'; out.appendChild(row); });
    }
    if (data.observation_schema) {
      const row=document.createElement('div'); row.className='scsi-page-row'; row.innerHTML='<strong>Normalized observation schema</strong><small>'+escapeHtml(data.observation_schema.schema||'')+'</small><small><b>Required fields:</b> '+escapeHtml((data.observation_schema.required||[]).join(', '))+'</small>'; out.appendChild(row);
    }

    [['Methodology', data.methodology || []], ['Display guidance', data.display_guidance || []], ['Review notes', data.review_notes || []], ['Hidden from public pages', data.hidden || []]].forEach(function (group) {
      if (!group[1].length) return;
      const h = document.createElement('h3');
      h.textContent = group[0];
      out.appendChild(h);
      const ul = document.createElement('ul');
      ul.className = 'scsi-list scsi-public-notes';
      group[1].forEach(function (item) { const li = document.createElement('li'); li.textContent = item; ul.appendChild(li); });
      out.appendChild(ul);
    });
  }

  function renderPublicSourcePageDirectory(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = (data.summary || 'Public source page directory.') + ' · ' + (data.version_scope || 'v1.5.0');
    out.innerHTML = '';
    const nav = document.createElement('div');
    nav.className = 'scsi-public-nav-row scsi-public-source-nav-row';
    (data.navigation || []).forEach(function (item) {
      const a = document.createElement('a');
      a.href = item.path || item.url || '#';
      a.textContent = (item.label || item.slug || 'Source page') + ' →';
      a.className = 'scsi-public-nav-link scsi-public-source-link';
      nav.appendChild(a);
    });
    out.appendChild(nav);
    const grid = document.createElement('div');
    grid.className = 'scsi-grid scsi-public-source-page-grid';
    (data.pages || []).forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat scsi-public-source-page-card';
      card.innerHTML = '<span class="scsi-public-label">' + escapeHtml(item.eyebrow || item.public_status || '') + '</span>' +
        '<strong>' + escapeHtml(item.title || '') + '</strong>' +
        '<small>' + escapeHtml(item.summary || item.excerpt || '') + '</small>' +
        '<code>' + escapeHtml(item.shortcode || '') + '</code>' +
        '<a class="scsi-mini-link" href="' + escapeHtml(item.canonical_path || '#') + '">Open page →</a>';
      grid.appendChild(card);
    });
    out.appendChild(grid);
    if ((data.review_notes || []).length) {
      const ul = document.createElement('ul');
      ul.className = 'scsi-list scsi-public-notes';
      (data.review_notes || []).forEach(function (note) { const li = document.createElement('li'); li.textContent = note; ul.appendChild(li); });
      out.appendChild(ul);
    }
  }

  function renderPublicSourceNavigation(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    const current = data.current_slug || root.dataset.current || '';
    muted.textContent = data.summary || 'Public source navigation.';
    out.innerHTML = '';
    const nav = document.createElement('div');
    nav.className = 'scsi-public-nav-row scsi-public-source-nav-row';
    (data.items || []).forEach(function (item) {
      const a = document.createElement('a');
      a.href = item.path || item.url || '#';
      a.textContent = (item.label || item.slug || 'Source page') + ' →';
      a.className = 'scsi-public-nav-link scsi-public-source-link';
      if (item.active || (current && item.slug === current)) a.className += ' scsi-active-link';
      nav.appendChild(a);
    });
    out.appendChild(nav);
  }

  function renderPublicSourcePageTemplates(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = (data.summary || 'Copy-ready public source page templates.') + ' · ' + (data.version_scope || 'v1.5.0');
    out.innerHTML = '';
    const grid = document.createElement('div');
    grid.className = 'scsi-grid scsi-public-source-page-grid';
    (data.templates || []).forEach(function (item) {
      const card = document.createElement('div');
      card.className = 'scsi-stat scsi-public-source-page-card scsi-template-card';
      card.innerHTML = '<span class="scsi-public-label">' + escapeHtml(item.slug || '') + '</span>' +
        '<strong>' + escapeHtml(item.title || '') + '</strong>' +
        '<small><b>Path:</b> ' + escapeHtml(item.canonical_path || '') + '</small>' +
        '<small><b>Excerpt:</b> ' + escapeHtml(item.excerpt || '') + '</small>' +
        '<small><b>Meta:</b> ' + escapeHtml(item.meta_description || '') + '</small>' +
        '<code>' + escapeHtml(item.navigation_shortcode || '') + '</code>' +
        '<code>' + escapeHtml(item.shortcode || '') + '</code>';
      grid.appendChild(card);
    });
    out.appendChild(grid);
  }

  function renderPublicSourcePageVisualQa(root, data) {
    const out = root.querySelector('.scsi-output');
    const muted = root.querySelector('.scsi-muted');
    muted.textContent = (data.summary || 'Public source page QA.') + ' · Score: ' + formatNumber(data.score || 0) + '%';
    out.innerHTML = '';
    (data.checks || []).forEach(function (check) {
      const row = document.createElement('div');
      row.className = 'scsi-page-row scsi-public-qa-row';
      row.innerHTML = '<strong>' + escapeHtml(check.label || check.id || '') + '</strong><br>' +
        statusBadge(check.status || 'review') +
        '<small>' + escapeHtml(check.detail || '') + '</small>';
      out.appendChild(row);
    });
    const notes = document.createElement('ul');
    notes.className = 'scsi-list scsi-public-notes';
    (data.review_notes || []).forEach(function (note) { const li = document.createElement('li'); li.textContent = note; notes.appendChild(li); });
    out.appendChild(notes);
  }
  function fetchDashboards() {
    if (!cfg.restBase) return;
    document.querySelectorAll('[data-scsi-admin-control]').forEach(function (root) {
      const type = root.dataset.adminType || 'overview';
      fetchJson(cfg.restBase + adminEndpoint(type))
        .then(function (data) { renderAdminControl(root, data, type); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Site Intelligence admin control plane.'); });
    });
    document.querySelectorAll('[data-scsi-ai-status]').forEach(function (root) {
      fetchJson(cfg.restBase + '/ai-status')
        .then(function (data) { renderAiStatus(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load AI brief status.'); });
    });

    document.querySelectorAll('[data-scsi-ai-brief]').forEach(function (root) {
      const type = root.dataset.briefType || 'site-intelligence';
      fetchJson(cfg.restBase + aiBriefEndpoint(type) + queryFromDataset(root, ['startDate', 'endDate', 'priorStartDate', 'priorEndDate', 'limit', 'mode', 'useAi', 'live']))
        .then(function (data) { renderAiBrief(root, data); })
        .catch(function (err) {
          if (type === 'public-dashboard') {
            renderAiBrief(root, publicDashboardBriefFallback());
            return;
          }
          showError(root, err && err.message ? err.message : 'Unable to load AI-assisted brief.');
        });
    });
    document.querySelectorAll('[data-scsi-report]').forEach(function (root) {
      const type = root.dataset.reportType || 'site-intelligence';
      fetchJson(cfg.restBase + reportEndpoint(type) + queryFromDataset(root, ['startDate', 'endDate', 'priorStartDate', 'priorEndDate', 'limit', 'latitude', 'longitude', 'country', 'start', 'end', 'year', 'live', 'report']))
        .then(function (data) { renderReport(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load report generator.'); });
    });

    document.querySelectorAll('[data-scsi-dashboard]').forEach(function (root) {
      fetchJson(cfg.restBase + '/dashboard')
        .then(function (data) { renderDashboard(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Site Intelligence backend.'); });
    });
    document.querySelectorAll('[data-scsi-page]').forEach(function (root) {
      fetchJson(cfg.restBase + '/page?path=' + encodeURIComponent(window.location.pathname))
        .then(function (data) { renderPage(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load page intelligence.'); });
    });
    document.querySelectorAll('[data-scsi-unmapped]').forEach(function (root) {
      fetchJson(cfg.restBase + '/unmapped?limit=20')
        .then(function (data) { renderUnmapped(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load registry mapping report.'); });
    });
    document.querySelectorAll('[data-scsi-events]').forEach(function (root) {
      fetchJson(cfg.restBase + '/events')
        .then(function (data) { renderEvents(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load event diagnostics.'); });
    });
    document.querySelectorAll('[data-scsi-opportunities]').forEach(function (root) {
      fetchJson(cfg.restBase + '/opportunities?limit=20')
        .then(function (data) { renderOpportunities(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load conversion opportunities.'); });
    });
    document.querySelectorAll('[data-scsi-external-health]').forEach(function (root) {
      fetchJson(cfg.restBase + '/external-health')
        .then(function (data) { renderExternalHealth(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load external connector health.'); });
    });

    document.querySelectorAll('[data-scsi-external-cache]').forEach(function (root) {
      fetchJson(cfg.restBase + '/external-cache')
        .then(function (data) { renderExternalCache(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load external cache status.'); });
    });
    document.querySelectorAll('[data-scsi-climate-energy]').forEach(function (root) {
      fetchJson(cfg.restBase + '/climate-energy' + queryFromDataset(root, ['latitude', 'longitude', 'country', 'start', 'end', 'year', 'live']))
        .then(function (data) { renderClimateEnergy(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Climate + Energy Intelligence.'); });
    });
    document.querySelectorAll('[data-scsi-search-intelligence]').forEach(function (root) {
      fetchJson(cfg.restBase + '/search-intelligence' + queryFromDataset(root, ['start', 'end']))
        .then(function (data) { renderSearchIntelligence(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Search Intelligence.'); });
    });
    document.querySelectorAll('[data-scsi-search-opportunities]').forEach(function (root) {
      fetchJson(cfg.restBase + '/search-opportunities' + queryFromDataset(root, ['start', 'end', 'limit']))
        .then(function (data) { renderSearchOpportunities(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Search Opportunities.'); });
    });
    document.querySelectorAll('[data-scsi-metadata-intelligence]').forEach(function (root) {
      fetchJson(cfg.restBase + '/metadata-intelligence' + queryFromDataset(root, ['start', 'end', 'limit']))
        .then(function (data) { renderMetadataIntelligence(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Metadata Intelligence.'); });
    });
    document.querySelectorAll('[data-scsi-internal-link-intelligence]').forEach(function (root) {
      fetchJson(cfg.restBase + '/internal-link-intelligence' + queryFromDataset(root, ['start', 'end', 'limit']))
        .then(function (data) { renderInternalLinkIntelligence(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Internal Link Intelligence.'); });
    });
    document.querySelectorAll('[data-scsi-seo-recommendations]').forEach(function (root) {
      fetchJson(cfg.restBase + '/seo-recommendations' + queryFromDataset(root, ['start', 'end', 'limit']))
        .then(function (data) { renderSeoRecommendations(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load SEO Recommendation Intelligence.'); });
    });
    document.querySelectorAll('[data-scsi-indexing-intelligence]').forEach(function (root) {
      fetchJson(cfg.restBase + '/indexing-intelligence' + queryFromDataset(root, ['start', 'end']))
        .then(function (data) { renderIndexingIntelligence(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Indexing Intelligence.'); });
    });
    document.querySelectorAll('[data-scsi-sitemap-coverage]').forEach(function (root) {
      fetchJson(cfg.restBase + '/sitemap-coverage')
        .then(function (data) { renderSitemapCoverage(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Sitemap Coverage.'); });
    });
    document.querySelectorAll('[data-scsi-404-intelligence]').forEach(function (root) {
      fetchJson(cfg.restBase + '/404-intelligence' + queryFromDataset(root, ['start', 'end', 'limit']))
        .then(function (data) { render404Intelligence(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load 404 Intelligence.'); });
    });
    document.querySelectorAll('[data-scsi-content-strategy]').forEach(function (root) {
      fetchJson(cfg.restBase + '/content-strategy' + queryFromDataset(root, ['start', 'end', 'priorStart', 'priorEnd', 'limit']))
        .then(function (data) { renderContentStrategy(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Content Strategy Intelligence.'); });
    });
    document.querySelectorAll('[data-scsi-topic-momentum]').forEach(function (root) {
      fetchJson(cfg.restBase + '/topic-momentum' + queryFromDataset(root, ['start', 'end', 'priorStart', 'priorEnd', 'limit']))
        .then(function (data) { renderTopicMomentum(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Topic Momentum.'); });
    });
    document.querySelectorAll('[data-scsi-update-priorities]').forEach(function (root) {
      fetchJson(cfg.restBase + '/update-priorities' + queryFromDataset(root, ['start', 'end', 'priorStart', 'priorEnd', 'limit']))
        .then(function (data) { renderUpdatePriorities(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Update Priorities.'); });
    });
    document.querySelectorAll('[data-scsi-publishing-opportunities]').forEach(function (root) {
      fetchJson(cfg.restBase + '/publishing-opportunities' + queryFromDataset(root, ['start', 'end', 'priorStart', 'priorEnd', 'limit']))
        .then(function (data) { renderPublishingOpportunities(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Publishing Opportunities.'); });
    });


    document.querySelectorAll('[data-scsi-advanced-external-health]').forEach(function (root) {
      fetchJson(cfg.restBase + '/advanced-external-health')
        .then(function (data) { renderExternalHealth(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load advanced external connector health.'); });
    });
    document.querySelectorAll('[data-scsi-environmental-monitoring]').forEach(function (root) {
      fetchJson(cfg.restBase + '/environmental-monitoring' + queryFromDataset(root, ['latitude', 'longitude', 'state', 'county', 'forceRefresh']))
        .then(function (data) { renderAdvancedExternalDashboard(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Environmental Monitoring Intelligence.'); });
    });
    document.querySelectorAll('[data-scsi-urban-resilience]').forEach(function (root) {
      fetchJson(cfg.restBase + '/urban-resilience' + queryFromDataset(root, ['latitude', 'longitude', 'country', 'state', 'county', 'forceRefresh']))
        .then(function (data) { renderAdvancedExternalDashboard(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Urban Resilience Intelligence.'); });
    });
    document.querySelectorAll('[data-scsi-biodiversity-land-use]').forEach(function (root) {
      fetchJson(cfg.restBase + '/biodiversity-land-use' + queryFromDataset(root, ['latitude', 'longitude', 'country', 'forceRefresh']))
        .then(function (data) { renderAdvancedExternalDashboard(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Biodiversity and Land Use Intelligence.'); });
    });
    document.querySelectorAll('[data-scsi-energy-systems]').forEach(function (root) {
      fetchJson(cfg.restBase + '/energy-systems' + queryFromDataset(root, ['latitude', 'longitude', 'country', 'state', 'start', 'end', 'forceRefresh']))
        .then(function (data) { renderAdvancedExternalDashboard(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load Energy Systems Data Intelligence.'); });
    });



    document.querySelectorAll('[data-scsi-public-dashboard-directory]').forEach(function (root) {
      fetchJson(cfg.restBase + '/public-dashboard-directory')
        .then(function (data) { renderPublicTopicDirectory(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public topic dashboard directory.'); });
    });
    document.querySelectorAll('[data-scsi-public-topic-dashboard]').forEach(function (root) {
      const topic = root.dataset.topic || 'knowledge-system';
      fetchJson(cfg.restBase + '/public-topic-dashboard?topic=' + encodeURIComponent(topic))
        .then(function (data) { renderPublicTopicDashboard(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public topic dashboard.'); });
    });
    document.querySelectorAll('[data-scsi-public-source-methodology]').forEach(function (root) {
      fetchJson(cfg.restBase + '/public-source-methodology')
        .then(function (data) { renderPublicSourceMethodology(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public source methodology.'); });
    });

    document.querySelectorAll('[data-scsi-public-dashboard-navigation]').forEach(function (root) {
      const current = root.dataset.current || '';
      fetchJson(cfg.restBase + '/public-dashboard-navigation' + (current ? '?current=' + encodeURIComponent(current) : ''))
        .then(function (data) { renderPublicDashboardNavigation(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public dashboard navigation.'); });
    });
    document.querySelectorAll('[data-scsi-public-topic-page-templates]').forEach(function (root) {
      const slug = root.dataset.slug || '';
      fetchJson(cfg.restBase + '/public-topic-page-templates' + (slug ? '?slug=' + encodeURIComponent(slug) : ''))
        .then(function (data) { renderPublicTopicPageTemplates(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public topic page templates.'); });
    });
    document.querySelectorAll('[data-scsi-public-topic-page-visual-qa]').forEach(function (root) {
      fetchJson(cfg.restBase + '/public-topic-page-visual-qa')
        .then(function (data) { renderPublicTopicPageVisualQa(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public topic page visual QA.'); });
    });


    document.querySelectorAll('[data-scsi-public-source-page-directory]').forEach(function (root) {
      fetchJson(cfg.restBase + '/public-source-pages')
        .then(function (data) { renderPublicSourcePageDirectory(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public source page directory.'); });
    });
    document.querySelectorAll('[data-scsi-public-source-navigation]').forEach(function (root) {
      const current = root.dataset.current || '';
      fetchJson(cfg.restBase + '/public-source-navigation' + (current ? '?current=' + encodeURIComponent(current) : ''))
        .then(function (data) { renderPublicSourceNavigation(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public source navigation.'); });
    });
    document.querySelectorAll('[data-scsi-public-source-page-templates]').forEach(function (root) {
      const slug = root.dataset.slug || '';
      fetchJson(cfg.restBase + '/public-source-page-templates' + (slug ? '?slug=' + encodeURIComponent(slug) : ''))
        .then(function (data) { renderPublicSourcePageTemplates(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public source page templates.'); });
    });
    document.querySelectorAll('[data-scsi-public-source-page-visual-qa]').forEach(function (root) {
      fetchJson(cfg.restBase + '/public-source-page-visual-qa')
        .then(function (data) { renderPublicSourcePageVisualQa(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public source page visual QA.'); });
    });
    document.querySelectorAll('[data-scsi-public-source-panel]').forEach(function (root) {
      const panel = root.dataset.sourcePanel || 'api-sources';
      fetchJson(cfg.restBase + sourcePanelEndpoint(panel))
        .then(function (data) { renderPublicSourcePanel(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public source panel.'); });
    });

    document.querySelectorAll('[data-scsi-public-connector-panel]').forEach(function (root) {
      const panel = root.dataset.connectorPanel || 'connector-status';
      setPublicConnectorLoading(root, true);
      fetchJson(cfg.restBase + connectorPanelEndpoint(panel, root))
        .then(function (data) { renderPublicConnectorPanel(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public connector panel.'); })
        .finally(function () { finishPublicConnectorLoading(root); });
    });

    document.querySelectorAll('[data-scsi-public-indicator-chart-panel]').forEach(function (root) {
      const panel = root.dataset.indicatorChartPanel || 'directory';
      fetchJson(cfg.restBase + indicatorChartPanelEndpoint(panel))
        .then(function (data) { renderPublicIndicatorChartPanel(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public indicator chart panel.'); });
    });



    document.querySelectorAll('[data-scsi-public-source-aware-brief-panel]').forEach(function (root) {
      const panel = root.dataset.sourceBriefPanel || 'directory';
      fetchJson(cfg.restBase + sourceAwareBriefPanelEndpoint(panel))
        .then(function (data) { renderPublicSourceAwareBriefPanel(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public source-aware brief panel.'); });
    });

    document.querySelectorAll('[data-scsi-public-dashboard-export-panel]').forEach(function (root) {
      const panel = root.dataset.dashboardExportPanel || 'manifest';
      fetchJson(cfg.restBase + dashboardExportPanelEndpoint(panel))
        .then(function (data) { renderPublicDashboardExportPanel(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public dashboard export panel.'); });
    });

    document.querySelectorAll('[data-scsi-public-page-builder]').forEach(function (root) {
      fetchJson(cfg.restBase + '/public-page-builder')
        .then(function (data) { renderPublicPageBuilder(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public page builder.'); });
    });
    document.querySelectorAll('[data-scsi-public-shortcode-bundle]').forEach(function (root) {
      fetchJson(cfg.restBase + '/public-page-builder-shortcodes')
        .then(function (data) { renderPublicShortcodeBundles(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public shortcode bundles.'); });
    });
    document.querySelectorAll('[data-scsi-public-visual-qa]').forEach(function (root) {
      fetchJson(cfg.restBase + '/public-page-builder-visual-qa')
        .then(function (data) { renderPublicVisualQa(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public dashboard visual QA.'); });
    });
    document.querySelectorAll('[data-scsi-public-landing]').forEach(function (root) {
      fetchJson(cfg.restBase + '/public-landing-page')
        .then(function (data) { renderPublicLanding(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public dashboard landing page.'); });
    });
    document.querySelectorAll('[data-scsi-public-dashboard]').forEach(function (root) {
      fetchJson(cfg.restBase + '/public-dashboard' + queryFromDataset(root, ['start', 'end']))
        .then(function (data) { renderPublicDashboard(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public Site Intelligence.'); });
    });
    document.querySelectorAll('[data-scsi-public-knowledge-overview]').forEach(function (root) {
      fetchJson(cfg.restBase + '/public-knowledge-overview' + queryFromDataset(root, ['start', 'end']))
        .then(function (data) { renderPublicKnowledgeOverview(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public knowledge overview.'); });
    });
    document.querySelectorAll('[data-scsi-public-climate-energy]').forEach(function (root) {
      fetchJson(cfg.restBase + '/public-climate-energy-summary' + queryFromDataset(root, ['latitude', 'longitude', 'country', 'start', 'end', 'year', 'live']))
        .then(function (data) { renderPublicClimateEnergy(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public climate and energy summary.'); });
    });
    document.querySelectorAll('[data-scsi-public-methodology]').forEach(function (root) {
      fetchJson(cfg.restBase + '/public-methodology')
        .then(function (data) { renderPublicMethodology(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public methodology.'); });
    });
    document.querySelectorAll('[data-scsi-public-readiness]').forEach(function (root) {
      fetchJson(cfg.restBase + '/public-readiness' + queryFromDataset(root, ['start', 'end']))
        .then(function (data) { renderPublicReadiness(root, data); })
        .catch(function (err) { showError(root, err && err.message ? err.message : 'Unable to load public readiness report.'); });
    });
  }

  function setupLaunchActions() {
    document.querySelectorAll('[data-scsi-copy-view]').forEach(function (button) {
      button.addEventListener('click', function () {
        var url = window.location.href;
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(function () {
            button.textContent = 'Link copied';
            window.setTimeout(function () { button.textContent = 'Copy view link'; }, 1800);
          });
        }
      });
    });
    document.querySelectorAll('[data-scsi-print-view]').forEach(function (button) {
      button.addEventListener('click', function () { window.print(); });
    });
  }


  function loadLeaflet() {
    if (window.L) return Promise.resolve(window.L);
    return new Promise(function(resolve, reject) {
      if (!document.querySelector('link[data-scsi-leaflet]')) {
        var link=document.createElement('link'); link.rel='stylesheet'; link.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'; link.setAttribute('data-scsi-leaflet','1'); document.head.appendChild(link);
      }
      var existing=document.querySelector('script[data-scsi-leaflet]');
      if (existing) { existing.addEventListener('load',function(){resolve(window.L);}); return; }
      var script=document.createElement('script'); script.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'; script.async=true; script.setAttribute('data-scsi-leaflet','1'); script.onload=function(){resolve(window.L);}; script.onerror=reject; document.head.appendChild(script);
    });
  }

  function geoTableHtml(features) {
    var rows=(features||[]).slice(0,100).map(function(f){var p=f.properties||{}, c=(f.geometry||{}).coordinates||[]; return '<tr><td>'+escapeHtml(p.title||'Event')+'</td><td>'+escapeHtml(p.category||'')+'</td><td>'+escapeHtml(p.source||'')+'</td><td>'+escapeHtml(p.observed_at||'Not supplied')+'</td><td>'+escapeHtml(c[1])+'</td><td>'+escapeHtml(c[0])+'</td></tr>';}).join('');
    return '<div class="scsi-table-wrap"><table class="scsi-geo-data-table"><thead><tr><th>Event</th><th>Category</th><th>Source</th><th>Observed</th><th>Latitude</th><th>Longitude</th></tr></thead><tbody>'+rows+'</tbody></table></div>';
  }

  function initGeospatialMap(root) {
    var mapEl=root.querySelector('.scsi-geo-map'), status=root.querySelector('.scsi-geo-status'), legend=root.querySelector('.scsi-geo-legend');
    Promise.all([loadLeaflet(), fetchJson(cfg.restBase+'/public-geospatial-layers'), fetchJson(cfg.restBase+'/public-geospatial-events'), fetchJson(cfg.restBase+'/public-geospatial-heatmap')]).then(function(values){
      var L=values[0], manifest=values[1], events=values[2], heat=values[3];
      var map=L.map(mapEl,{worldCopyJump:true}).setView([Number(root.dataset.latitude||12),Number(root.dataset.longitude||20)],Number(root.dataset.zoom||2));
      var base=L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(map);
      var currentRaster=null, markerLayer=L.layerGroup().addTo(map), heatLayer=L.layerGroup();
      var select=root.querySelector('[data-scsi-geo-layer]'), dateInput=root.querySelector('[data-scsi-geo-date]');
      (manifest.satellite_layers||[]).forEach(function(layer){var option=document.createElement('option'); option.value=layer.id; option.textContent=layer.title; select.appendChild(option);});
      select.value=root.dataset.layer||'true-color';
      function drawRaster(){var id=select.value, selected=(manifest.satellite_layers||[]).find(function(x){return x.id===id;}); if(currentRaster){map.removeLayer(currentRaster);currentRaster=null;} if(!selected)return; var url=selected.tile_url.replace('{time}',dateInput.value||new Date().toISOString().slice(0,10)); currentRaster=L.tileLayer(url,{opacity:selected.default_opacity||0.7,maxZoom:9,attribution:selected.attribution||selected.source}).addTo(map); currentRaster.bringToBack(); legend.innerHTML='<strong>'+escapeHtml(selected.title)+'</strong><span>'+escapeHtml(selected.description||'')+'</span><small>'+escapeHtml(selected.source||'')+' · '+escapeHtml(dateInput.value||'latest')+'</small>';}
      function drawEvents(){markerLayer.clearLayers(); (events.features||[]).forEach(function(f){var c=(f.geometry||{}).coordinates||[],p=f.properties||{}; if(c.length<2)return; var marker=L.circleMarker([c[1],c[0]],{radius:6,weight:1,fillOpacity:.78}); marker.bindPopup('<strong>'+escapeHtml(p.title||'Event')+'</strong><br>'+escapeHtml(p.category||'')+'<br><small>'+escapeHtml(p.source||'')+' · '+escapeHtml(p.observed_at||'date unavailable')+'</small>'); marker.addTo(markerLayer);});}
      function drawHeat(){heatLayer.clearLayers(); (heat.points||[]).forEach(function(pt){L.circle([pt[0],pt[1]],{radius:Math.max(45000,pt[2]*160000),stroke:false,fillOpacity:.14}).addTo(heatLayer);});}
      drawRaster(); drawEvents(); drawHeat();
      select.addEventListener('change',drawRaster); dateInput.addEventListener('change',drawRaster);
      root.querySelector('[data-scsi-geo-events]').addEventListener('change',function(){this.checked?map.addLayer(markerLayer):map.removeLayer(markerLayer);});
      root.querySelector('[data-scsi-geo-heat]').addEventListener('change',function(){this.checked?map.addLayer(heatLayer):map.removeLayer(heatLayer);});
      root.querySelector('[data-scsi-geo-refresh]').addEventListener('click',function(){window.location.reload();});
      root.querySelector('[data-scsi-geo-fullscreen]').addEventListener('click',function(){if(root.requestFullscreen)root.requestFullscreen();});
      root.querySelector('.scsi-geo-table').innerHTML=geoTableHtml(events.features||[]);
      status.textContent=(events.data_state==='live'?'Live public events':'Demonstration fallback events')+' · '+(events.count||0)+' records · Generated '+(events.generated_at||'');
      setTimeout(function(){map.invalidateSize();},250);
    }).catch(function(err){showError(root,err&&err.message?err.message:'Unable to load geospatial map.');});
  }

  function initGeospatialExtras() {
    document.querySelectorAll('[data-scsi-geospatial-map]').forEach(initGeospatialMap);
    document.querySelectorAll('[data-scsi-geospatial-table]').forEach(function(root){fetchJson(cfg.restBase+'/public-geospatial-events').then(function(data){root.querySelector('.scsi-muted').textContent=(data.count||0)+' public event records'; root.querySelector('.scsi-output').innerHTML=geoTableHtml(data.features||[]);}).catch(function(err){showError(root,err.message);});});
    document.querySelectorAll('[data-scsi-geospatial-layers]').forEach(function(root){fetchJson(cfg.restBase+'/public-geospatial-layers').then(function(data){root.querySelector('.scsi-muted').textContent='Satellite, event, heat, and boundary layers'; var out=root.querySelector('.scsi-output'); out.innerHTML='<div class="scsi-directory-grid">'+(data.satellite_layers||[]).concat(data.vector_layers||[]).map(function(x){return '<article class="scsi-directory-link"><strong>'+escapeHtml(x.title)+'</strong><span>'+escapeHtml(x.description||x.source||x.kind)+'</span><small>'+escapeHtml(x.source||'')+'</small></article>';}).join('')+'</div>';}).catch(function(err){showError(root,err.message);});});
  }

  function setupResponsiveEmbeds() {
    var frames = Array.prototype.slice.call(document.querySelectorAll('[data-scsi-embed-frame], .scsi-standalone-app iframe, .scsi-app-shell iframe, .scsi-embed iframe'));
    if (!frames.length) return;
    var records = frames.map(function (frame) {
      var wrapper = frame.closest('.scsi-standalone-app, .scsi-app-shell, .scsi-embed') || frame.parentElement;
      var origin = '';
      try { origin = new URL(frame.src, window.location.href).origin; } catch (error) { origin = ''; }
      frame.setAttribute('loading', frame.getAttribute('loading') || 'lazy');
      frame.setAttribute('referrerpolicy', frame.getAttribute('referrerpolicy') || 'strict-origin-when-cross-origin');
      if (!frame.getAttribute('allow')) frame.setAttribute('allow', 'fullscreen; clipboard-write');
      frame.dataset.scsiEmbedFrame = '1';
      var fallback = wrapper ? wrapper.querySelector('.scsi-embed-fallback') : null;
      if (wrapper && !fallback) {
        fallback = document.createElement('p');
        fallback.className = 'scsi-embed-fallback';
        var link = document.createElement('a');
        link.href = frame.src;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.textContent = 'Open Site Intelligence in a new tab';
        fallback.appendChild(link);
        wrapper.appendChild(fallback);
      }
      var record = {
        frame: frame,
        wrapper: wrapper,
        origin: origin,
        minimum: Number(frame.dataset.scsiMinHeight || 620),
        mobileMinimum: Number(frame.dataset.scsiMobileMinHeight || 760),
        maximum: Number(frame.dataset.scsiMaxHeight || 2600),
        loaded: false
      };
      frame.addEventListener('load', function () {
        record.loaded = true;
        if (wrapper) wrapper.classList.add('is-loaded');
        try { frame.contentWindow.postMessage({type: 'SC_SI_REQUEST_HEIGHT', hostVersion: cfg.version || ''}, origin || '*'); } catch (error) {}
      });
      window.setTimeout(function () {
        if (!record.loaded && wrapper) wrapper.classList.add('scsi-embed-delayed');
      }, 20000);
      return record;
    });

    function minimumFor(record) {
      return window.matchMedia('(max-width: 760px)').matches ? record.mobileMinimum : record.minimum;
    }
    function applyHeight(record, value) {
      var parsed = Number.parseInt(value, 10);
      if (!Number.isFinite(parsed) || parsed <= 0) return;
      var height = Math.max(minimumFor(record), Math.min(record.maximum, parsed + 8));
      record.frame.style.height = height + 'px';
      record.frame.setAttribute('height', String(height));
      if (record.wrapper) record.wrapper.style.setProperty('--scsi-embed-height', height + 'px');
    }
    window.addEventListener('message', function (event) {
      if (!event.data || event.data.type !== 'scsi-height') return;
      records.forEach(function (record) {
        if (!record.origin || event.origin !== record.origin) return;
        if (event.source !== record.frame.contentWindow) return;
        applyHeight(record, event.data.height);
      });
    });
    window.addEventListener('resize', function () {
      records.forEach(function (record) {
        var current = Number.parseInt(record.frame.style.height || record.frame.getAttribute('height') || 0, 10);
        if (current) applyHeight(record, current);
      });
    }, {passive: true});
  }

  function setupLiveIntelligence() {
    document.querySelectorAll('[data-scsi-live-intelligence]').forEach(function (root) {
      const viewport = root.querySelector('.scsi-live-intelligence__viewport');
      const track = root.querySelector('.scsi-live-intelligence__track');
      const pause = root.querySelector('.scsi-live-intelligence__pause');
      const deliveryOutput = root.querySelector('[data-scsi-live-delivery]');
      const mobileControls = root.querySelector('.scsi-live-intelligence__mobile-controls');
      const previous = root.querySelector('.scsi-live-intelligence__previous');
      const next = root.querySelector('.scsi-live-intelligence__next');
      const position = root.querySelector('.scsi-live-intelligence__position');
      if (!viewport || !track || !cfg.restBase) return;

      const category = root.dataset.category || '';
      const channel = root.dataset.channel || 'global';
      const region = root.dataset.region || '';
      const country = root.dataset.country || '';
      const limit = Math.max(1, Math.min(24, Number(root.dataset.limit || 16)));
      const feeds = root.dataset.feeds || '';
      const exclude = root.dataset.exclude || '';
      const maxPerSource = Math.max(1, Math.min(5, Number(root.dataset.maxPerSource || 2)));
      const showSources = root.dataset.showSources !== '0';
      const showUpdated = root.dataset.showUpdated !== '0';
      const showFreshness = root.dataset.showFreshness !== '0';
      const showClusterSources = root.dataset.showClusterSources !== '0';
      const showSelectionContext = root.dataset.selectionContext !== '0';
      const detailLinks = root.dataset.detailLinks !== '0';
      const contextBase = String(root.dataset.contextBase || '');
      const compactSources = root.dataset.compactSources !== '0';
      const textLimit = Math.max(48, Math.min(220, Number(root.dataset.textLimit || 120)));
      const refreshInterval = Math.max(60, Math.min(1800, Number(root.dataset.refreshSeconds || 300))) * 1000;
      const mobileMode = ['rotator', 'marquee', 'hidden'].includes(root.dataset.mobileMode) ? root.dataset.mobileMode : 'rotator';
      const mobileInterval = Math.max(4, Math.min(30, Number(root.dataset.mobileInterval || 7))) * 1000;
      const mobileQuery = window.matchMedia('(max-width: 760px)');
      const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
      const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
      let signals = [];
      let currentIndex = 0;
      let rotationTimer = 0;
      let touchStartX = null;
      let renderedMobile = null;
      let categoryLabels = {};
      try { categoryLabels = JSON.parse(root.dataset.categoryLabels || '{}'); } catch (error) { categoryLabels = {}; }

      const params = new URLSearchParams({limit: String(limit), max_per_source: String(maxPerSource)});
      if (category) params.set('category', category);
      if (channel) params.set('channel', channel);
      if (region) params.set('region', region);
      if (country) params.set('country', country);
      if (feeds) params.set('feeds', feeds);
      if (exclude) params.set('exclude', exclude);
      const endpoint = cfg.restBase + '/live-intelligence?' + params.toString();

      const relativeTime = function (value) {
        const stamp = Date.parse(value || '');
        if (!Number.isFinite(stamp)) return '';
        const minutes = Math.max(0, Math.round((Date.now() - stamp) / 60000));
        if (minutes < 1) return 'UPDATED NOW';
        if (minutes < 60) return 'UPDATED ' + minutes + 'M AGO';
        const hours = Math.round(minutes / 60);
        if (hours < 48) return 'UPDATED ' + hours + 'H AGO';
        return 'UPDATED ' + Math.round(hours / 24) + 'D AGO';
      };
      const shorten = function (value, maximum) {
        const clean = String(value || '').replace(/\s+/g, ' ').trim();
        if (clean.length <= maximum) return clean;
        return clean.slice(0, Math.max(1, maximum - 1)).trimEnd() + '…';
      };
      const normalizeDeliveryState = function (data) {
        const delivery = data && data.delivery ? data.delivery : {};
        const proxy = data && data._scsi_delivery ? data._scsi_delivery : {};
        if (proxy.mode === 'stale_cache') return 'stale';
        const state = String(delivery.state || proxy.freshness || 'live').toLowerCase().replace(/\s+/g, '_');
        return ['live', 'recently_updated', 'delayed', 'stale', 'historical', 'empty', 'unavailable'].includes(state) ? state : 'live';
      };
      const setDeliveryState = function (state, label) {
        root.dataset.deliveryState = state;
        root.classList.toggle('is-delayed', state === 'delayed' || state === 'stale');
        root.classList.toggle('has-error', state === 'unavailable');
        root.classList.toggle('is-empty', state === 'empty');
        if (deliveryOutput) deliveryOutput.textContent = String(label || state.replace(/_/g, ' ')).toUpperCase();
      };
      const itemHtml = function (signal, includeSeparator) {
        const metadata = [];
        const sourceName = compactSources && signal.source_short_name ? signal.source_short_name : signal.source_name;
        if (showSources && sourceName) metadata.push(sourceName);
        if (showClusterSources && Number(signal.cluster_source_count || 1) > 1) metadata.push(String(signal.cluster_source_count) + ' SOURCES');
        if (showFreshness && signal.freshness_label) metadata.push(String(signal.freshness_label).toUpperCase());
        if (showUpdated && (signal.observed_at || signal.updated_at)) metadata.push(relativeTime(signal.observed_at || signal.updated_at));
        const contextHref = detailLinks && contextBase && signal.signal_id ? contextBase + encodeURIComponent(signal.signal_id) + '/' : '';
        const href = contextHref || signal.destination_url || signal.context_view_url || '#';
        const categoryId = signal.category || 'signal';
        const categoryLabel = categoryLabels[categoryId] || categoryId.replace(/_/g, ' ');
        const fullValue = signal.value || 'AVAILABLE';
        const reasons = Array.isArray(signal.selection_reasons) ? signal.selection_reasons.join('; ') : '';
        const titleParts = [signal.detail || fullValue || signal.label || ''];
        if (signal.freshness_label) titleParts.push('Freshness: ' + signal.freshness_label);
        if (showSelectionContext && signal.development_state) titleParts.push('State: ' + signal.development_state);
        if (showSelectionContext && reasons) titleParts.push('Selected because: ' + reasons);
        const title = titleParts.filter(Boolean).join(' — ');
        const separator = includeSeparator ? '<span class="scsi-live-intelligence__separator" aria-hidden="true">◆</span>' : '';
        return '<a class="scsi-live-intelligence__signal" data-scsi-event="sc_live_intelligence_context_open" data-scsi-signal-id="' + escapeHtml(signal.signal_id || '') + '" data-freshness-state="' + escapeHtml(signal.freshness_state || 'unknown') + '" href="' + escapeHtml(href) + '" title="' + escapeHtml(title) + '" aria-label="' + escapeHtml(categoryLabel + ': ' + (signal.label || 'Live signal') + ': ' + fullValue + (signal.freshness_label ? '. ' + signal.freshness_label : '')) + '">' +
          '<span class="scsi-live-intelligence__category">' + escapeHtml(categoryLabel.toUpperCase()) + '</span>' +
          '<span class="scsi-live-intelligence__name">' + escapeHtml(shorten(signal.label || 'LIVE SIGNAL', 72)) + '</span>' +
          '<strong class="scsi-live-intelligence__value">' + escapeHtml(shorten(fullValue, textLimit)) + '</strong>' +
          (metadata.length ? '<small>' + escapeHtml(metadata.join(' · ')) + '</small>' : '') + '</a>' + separator;
      };
      const isMobileRotator = function () {
        return mobileQuery.matches && mobileMode === 'rotator';
      };
      const stopRotation = function () {
        if (rotationTimer) window.clearInterval(rotationTimer);
        rotationTimer = 0;
      };
      const updatePosition = function () {
        if (position) position.textContent = signals.length ? (currentIndex + 1) + ' / ' + signals.length : '0 / 0';
      };
      const showMobileSignal = function (index, announce) {
        if (!signals.length) return;
        currentIndex = (index + signals.length) % signals.length;
        track.innerHTML = '<div class="scsi-live-intelligence__mobile-signal">' + itemHtml(signals[currentIndex], false) + '</div>';
        updatePosition();
        if (announce) viewport.setAttribute('aria-label', 'Live Intelligence signal ' + (currentIndex + 1) + ' of ' + signals.length);
      };
      const startRotation = function () {
        stopRotation();
        if (!isMobileRotator() || reducedMotion.matches || root.classList.contains('is-paused') || signals.length < 2 || document.hidden) return;
        rotationTimer = window.setInterval(function () { showMobileSignal(currentIndex + 1, false); }, mobileInterval);
      };
      const renderMode = function () {
        if (!signals.length) return;
        const mobile = mobileQuery.matches;
        root.classList.toggle('is-mobile-rotator', mobile && mobileMode === 'rotator');
        root.classList.toggle('is-mobile-marquee', mobile && mobileMode === 'marquee');
        root.classList.toggle('is-mobile-hidden', mobile && mobileMode === 'hidden');
        if (mobileMode === 'hidden' && mobile) {
          stopRotation();
          return;
        }
        if (isMobileRotator()) {
          if (renderedMobile !== true) currentIndex = 0;
          showMobileSignal(currentIndex, false);
          if (mobileControls) mobileControls.hidden = false;
          renderedMobile = true;
          startRotation();
          return;
        }
        stopRotation();
        if (mobileControls) mobileControls.hidden = true;
        const content = signals.map(function (signal) { return itemHtml(signal, true); }).join('');
        track.innerHTML = '<div class="scsi-live-intelligence__set">' + content + '</div><div class="scsi-live-intelligence__set" aria-hidden="true">' + content + '</div>';
        renderedMobile = false;
      };
      const renderEmpty = function (data) {
        signals = [];
        stopRotation();
        if (mobileControls) mobileControls.hidden = true;
        updatePosition();
        const delivery = data && data.delivery ? data.delivery : {};
        const state = normalizeDeliveryState(data);
        const label = delivery.label || (state === 'empty' ? 'No matching public signals' : 'Temporarily unavailable');
        track.innerHTML = '<span class="scsi-live-intelligence__connecting">' + escapeHtml(String(label).toUpperCase()) + '</span>';
        root.classList.remove('is-ready');
        setDeliveryState(state === 'live' ? 'empty' : state, label);
        viewport.setAttribute('aria-busy', 'false');
      };
      const render = function (data) {
        signals = Array.isArray(data.signals) ? data.signals.filter(function (signal) { return signal && signal.validation_state !== 'invalid'; }) : [];
        if (!signals.length) {
          renderEmpty(data);
          return;
        }
        renderMode();
        const state = normalizeDeliveryState(data);
        const delivery = data.delivery || {};
        const label = delivery.label || (state === 'stale' ? 'Cached' : state.replace(/_/g, ' '));
        root.classList.remove('has-error', 'is-empty');
        root.classList.add('is-ready');
        setDeliveryState(state, label);
        viewport.setAttribute('aria-busy', 'false');
        if (root.dataset.motion === 'off') root.classList.add('is-paused');
      };
      const load = function () {
        viewport.setAttribute('aria-busy', 'true');
        fetchJson(endpoint).then(render).catch(function () {
          viewport.setAttribute('aria-busy', 'false');
          if (root.classList.contains('is-ready')) {
            setDeliveryState('delayed', 'Refresh delayed');
            return;
          }
          signals = [];
          track.innerHTML = '<span class="scsi-live-intelligence__connecting">LIVE INTELLIGENCE TEMPORARILY UNAVAILABLE</span>';
          setDeliveryState('unavailable', 'Unavailable');
        });
      };

      if (finePointer.matches) {
        root.addEventListener('mouseenter', function () { root.classList.add('is-hover-paused'); });
        root.addEventListener('mouseleave', function () { root.classList.remove('is-hover-paused'); });
      }
      root.addEventListener('focusin', function () {
        root.classList.add('is-focus-paused');
        stopRotation();
      });
      root.addEventListener('focusout', function (event) {
        if (!root.contains(event.relatedTarget)) {
          root.classList.remove('is-focus-paused');
          startRotation();
        }
      });
      if (previous) previous.addEventListener('click', function () { showMobileSignal(currentIndex - 1, true); startRotation(); });
      if (next) next.addEventListener('click', function () { showMobileSignal(currentIndex + 1, true); startRotation(); });
      viewport.addEventListener('touchstart', function (event) {
        if (!isMobileRotator() || !event.touches.length) return;
        touchStartX = event.touches[0].clientX;
        stopRotation();
      }, {passive: true});
      viewport.addEventListener('touchend', function (event) {
        if (!isMobileRotator() || touchStartX === null || !event.changedTouches.length) return;
        const distance = event.changedTouches[0].clientX - touchStartX;
        touchStartX = null;
        if (Math.abs(distance) >= 40) showMobileSignal(currentIndex + (distance < 0 ? 1 : -1), true);
        startRotation();
      }, {passive: true});
      if (pause) {
        pause.addEventListener('click', function () {
          const paused = root.classList.toggle('is-paused');
          pause.setAttribute('aria-pressed', paused ? 'true' : 'false');
          pause.setAttribute('aria-label', paused ? 'Resume Live Intelligence ticker' : 'Pause Live Intelligence ticker');
          const icon = pause.querySelector('span');
          if (icon) icon.textContent = paused ? '▶' : 'Ⅱ';
          if (paused) stopRotation(); else startRotation();
        });
      }
      const handleModeChange = function () { renderMode(); };
      if (mobileQuery.addEventListener) mobileQuery.addEventListener('change', handleModeChange); else mobileQuery.addListener(handleModeChange);
      if (reducedMotion.addEventListener) reducedMotion.addEventListener('change', startRotation); else reducedMotion.addListener(startRotation);
      document.addEventListener('visibilitychange', function () { if (document.hidden) stopRotation(); else startRotation(); });
      load();
      window.setInterval(load, refreshInterval);
    });
  }

  function init() {
    setupActivePageLinks();
    setupLaunchActions();
    setupResponsiveEmbeds();
    setupLiveIntelligence();
    fetchDashboards();
    initGeospatialExtras();
  }

  setupClickTracking();
  setupScrollTracking();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
