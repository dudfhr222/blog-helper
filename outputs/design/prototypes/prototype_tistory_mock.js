(function () {
  var PLACEHOLDER_BODY_ID = '[##_body_id_##]';

  if (!document.body || document.body.id !== PLACEHOLDER_BODY_ID) return;

  var blog = {
    title: 'YRBE Lab',
    desc: 'AI, 개발, 여행 기록을 실험적으로 정리하는 기술 블로그',
    link: './prototype_skin.html',
    pageTitle: 'YRBE Lab - Local Preview',
    author: 'YRBE'
  };

  var posts = [
    {
      slug: 'ai-workflow-note',
      title: 'AI 글쓰기 워크플로를 운영 도구처럼 다루기',
      summary: '초안 생성, 품질 검증, 발행 기록을 분리해 블로그 자동화 실패 지점을 줄이는 방법을 정리합니다.',
      category: 'AI',
      date: '2026.05.03',
      thumbnail: 'linear-gradient(135deg, #2563eb, #06b6d4)',
      tags: ['AI', '자동화', '운영'],
      body: [
        '<p>로컬 preview는 티스토리 치환자가 서버에서 처리되기 전에도 레이아웃을 확인하기 위한 mock renderer입니다.</p>',
        '<h2>왜 로컬 mock이 필요한가</h2>',
        '<p>스킨 HTML은 <code>[##_..._##]</code> 치환자와 <code>&lt;s_...&gt;</code> 조건 블록을 포함하므로 파일만 열면 목록과 상세가 동시에 보이거나 링크가 404로 이동할 수 있습니다.</p>',
        '<h2>구현 방향</h2>',
        '<p>원본 치환자는 파일에 남겨두고, placeholder body id 상태에서만 JS가 DOM 텍스트와 링크를 mock 데이터로 바꿉니다.</p>',
        '<h3>라우팅</h3>',
        '<p>게시글 링크는 <code>?post=slug</code>로 이동하며 새로고침과 뒤로가기를 지원합니다.</p>'
      ].join('')
    },
    {
      slug: 'tistory-skin-layout',
      title: '티스토리 스킨 구조를 로컬에서 검증하는 기준',
      summary: '목록, 상세, 사이드바 필수 컴포넌트를 한 파일 안에서 확인하는 최소 mock 구조입니다.',
      category: 'Tistory',
      date: '2026.05.02',
      thumbnail: 'linear-gradient(135deg, #7c3aed, #f43f5e)',
      tags: ['Tistory', 'Skin', 'Preview'],
      body: [
        '<p>티스토리 서버가 없어도 주요 화면 상태를 확인하려면 목록과 상세를 같은 DOM 안에서 명확히 분리해야 합니다.</p>',
        '<h2>보존해야 할 것</h2>',
        '<p>실제 적용 파일로 이어질 수 있도록 <code>[##_title_##]</code>, <code>[##_article_rep_title_##]</code> 같은 원본 치환자는 HTML 파일에서 삭제하지 않습니다.</p>',
        '<h2>검증 포인트</h2>',
        '<p>검색창, 최근글, 인기글, 카테고리, 태그, 페이징이 살아있는지 먼저 확인합니다.</p>'
      ].join('')
    },
    {
      slug: 'local-preview-checklist',
      title: 'Live Server preview 체크리스트',
      summary: 'CSS 연결, mock JS guard, 목록 카드, 상세 본문, 사이드바 링크를 빠르게 점검합니다.',
      category: 'Design',
      date: '2026.05.01',
      thumbnail: 'linear-gradient(135deg, #0891b2, #84cc16)',
      tags: ['Design', 'Checklist'],
      body: [
        '<p>Live Server에서 <code>prototype_skin.html</code>을 열고 홈과 상세 링크를 오가며 레이아웃 상태를 확인합니다.</p>',
        '<h2>기본 확인</h2>',
        '<p>홈 화면에는 목록 카드와 페이징이 보이고, 상세 화면에는 article hero와 본문이 보여야 합니다.</p>',
        '<h2>주의</h2>',
        '<p>이 JS는 body id가 placeholder일 때만 실행되므로 실제 티스토리 렌더링에는 개입하지 않습니다.</p>'
      ].join('')
    }
  ];

  var categories = ['AI', 'Tistory', 'Design', 'Travel'];
  var popularPosts = [posts[1], posts[0], posts[2]];
  var mockData = {
    blogPlaceholders: blog,
    listRep: posts,
    articleRep: posts,
    sidebar: {
      categories: categories,
      tags: ['AI', 'Tistory', 'CSS', 'Automation', 'Preview'],
      recentPosts: posts,
      popularPosts: popularPosts
    },
    routing: {
      postParam: 'post'
    }
  };

  function $(selector, root) {
    return (root || document).querySelector(selector);
  }

  function $all(selector, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(selector));
  }

  function setText(selector, value, root) {
    $all(selector, root).forEach(function (el) {
      el.textContent = value;
    });
  }

  function setAttr(selector, attr, value, root) {
    $all(selector, root).forEach(function (el) {
      el.setAttribute(attr, value);
    });
  }

  function postUrl(post) {
    return '?post=' + encodeURIComponent(post.slug);
  }

  function currentSlug() {
    var params = new URLSearchParams(window.location.search);
    return params.get(mockData.routing.postParam) || '';
  }

  function findPost(slug) {
    return posts.filter(function (post) { return post.slug === slug; })[0] || posts[0];
  }

  function injectLocalBaseStyle() {
    var style = document.createElement('style');
    style.textContent = [
      's_t3,s_list,s_list_rep,s_article_rep,s_permalink_article_rep,s_sidebar,s_sidebar_element,s_paging,s_random_tags,s_rctps_rep,s_rctps_popular_rep,s_tag_label,s_article_next,s_article_prev,s_article_related,s_article_related_rep{display:contents;}',
      's_list_empty,s_article_protected,s_page_rep,s_notice_rep,s_cover_group{display:none!important;}',
      'body[data-local-view="list"] .area-view,body[data-local-view="list"] .yrbe-article-hero,body[data-local-view="list"] .yrbe-side-panel{display:none!important;}',
      'body[data-local-view="list"] .area-common,body[data-local-view="list"] .area-paging{display:block!important;}',
      'body[data-local-view="page"] .hero-index-only,body[data-local-view="page"] .area-common,body[data-local-view="page"] .area-paging{display:none!important;}',
      'body[data-local-view="page"] .area-view,body[data-local-view="page"] .yrbe-article-hero{display:block!important;}',
      'body[data-local-view="page"] .yrbe-side-panel{display:block!important;}'
    ].join('\n');
    document.head.appendChild(style);
  }

  function replaceTextPlaceholders(root, map) {
    var walker = document.createTreeWalker(root || document.body, NodeFilter.SHOW_TEXT);
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function (node) {
      var text = node.nodeValue;
      Object.keys(map).forEach(function (key) {
        text = text.split(key).join(map[key]);
      });
      node.nodeValue = text;
    });
  }

  function replaceAttributePlaceholders(root, map) {
    $all('*', root || document).forEach(function (el) {
      Array.prototype.slice.call(el.attributes || []).forEach(function (attr) {
        var value = attr.value;
        Object.keys(map).forEach(function (key) {
          value = value.split(key).join(map[key]);
        });
        if (value !== attr.value) el.setAttribute(attr.name, value);
      });
    });
  }

  function renderGlobalPlaceholders() {
    var map = {
      '[##_title_##]': blog.title,
      '[##_desc_##]': blog.desc,
      '[##_blog_link_##]': blog.link,
      '[##_page_title_##]': blog.pageTitle,
      '[##_rss_url_##]': './rss',
      '[##_var_headersloguntitle_##]': '읽고 실험하고 기록하는 기술 노트',
      '[##_var_headersloguntext_##]': blog.desc,
      '[##_var_footerCopyright_##]': 'Copyright 2026 YRBE Lab',
      '[##_var_footerAddress_##]': 'Local prototype preview',
      '[##_guest_link_##]': '#guestbook'
    };
    document.title = blog.pageTitle;
    setAttr('meta[name="title"]', 'content', blog.pageTitle + ' :: ' + blog.title);
    setAttr('meta[name="description"]', 'content', blog.desc);
    replaceTextPlaceholders(document.body, map);
    replaceAttributePlaceholders(document, map);
    $all('a[href="' + blog.link + '"]').forEach(function (a) {
      a.addEventListener('click', function (event) {
        event.preventDefault();
        navigateToList();
      });
    });
  }

  function renderList() {
    var list = $('.area-common .post-list');
    var template = list && $('.post-card', list);
    if (!list || !template) return;

    list.innerHTML = '';
    posts.forEach(function (post) {
      var card = template.cloneNode(true);
      card.setAttribute('data-cat', post.category);
      card.setAttribute('data-local-post', post.slug);
      setText('.badge.link-category', post.category, card);
      setText('.post-card__title', post.title, card);
      setText('.post-card__excerpt', post.summary, card);
      setText('.post-card__date', post.date, card);
      setText('.post-card__read-time', '3분 읽기', card);
      $all('.link-article', card).forEach(function (link) {
        link.href = postUrl(post);
        link.classList.add('js-local-post-link');
        link.setAttribute('data-post-slug', post.slug);
      });
      $all('.thumbnail', card).forEach(function (thumb) {
        thumb.style.backgroundImage = post.thumbnail;
        thumb.setAttribute('has-thumbnail', '1');
      });
      $all('.img-thumbnail', card).forEach(function (img) {
        img.removeAttribute('src');
        img.alt = '';
      });
      list.appendChild(card);
    });

    setText('.title-search .archives', '전체 글');
    setText('.title-search span', String(posts.length));
    setText('#stat-post-count', String(posts.length));
  }

  function renderSidebar() {
    var catWrap = $('.cat-tree-wrap');
    if (catWrap) {
      catWrap.innerHTML = mockData.sidebar.categories.map(function (category) {
        return '<a href="#category-' + category.toLowerCase() + '">' + category + '</a>';
      }).join('');
    }

    $all('.tag-cloud.box_tag').forEach(function (cloud) {
      cloud.innerHTML = mockData.sidebar.tags.map(function (tag) {
        return '<a href="#tag-' + tag.toLowerCase() + '" class="tag">#' + tag + '</a>';
      }).join('');
    });

    renderRecentList('.recent-list:not(.list-tab)', mockData.sidebar.recentPosts);
    renderRecentList('.recent-list.list-tab', mockData.sidebar.popularPosts);

    var searchInput = $('.search-sidebar .searchInput');
    if (searchInput) {
      searchInput.placeholder = '로컬 mock 검색어';
      searchInput.addEventListener('keypress', function (event) {
        if (event.keyCode === 13) {
          event.preventDefault();
          navigateToList();
        }
      });
    }
  }

  function renderRecentList(selector, items) {
    var list = $(selector);
    if (!list) return;
    list.innerHTML = items.map(function (post) {
      return [
        '<li><div class="recent-item">',
        '<div class="recent-item__dot"></div><div>',
        '<a href="' + postUrl(post) + '" class="recent-item__title link-recent js-local-post-link" data-post-slug="' + post.slug + '">' + post.title + '</a>',
        '<span class="recent-item__date">' + post.date + '</span>',
        '</div></div></li>'
      ].join('');
    }).join('');
  }

  function renderArticle(post) {
    var map = {
      '[##_article_rep_title_##]': post.title,
      '[##_article_rep_category_##]': post.category,
      '[##_article_rep_author_##]': blog.author,
      '[##_article_rep_date_##]': post.date,
      '[##_article_rep_desc_##]': post.body,
      '[##_article_rep_thumbnail_raw_url_##]': '',
      '[##_article_rep_thumbnail_url_##]': '',
      '[##_article_rep_rp_cnt_##]': '0',
      '[##_article_next_title_##]': nextPost(post).title,
      '[##_article_next_link_##]': postUrl(nextPost(post)),
      '[##_article_prev_title_##]': prevPost(post).title,
      '[##_article_prev_link_##]': postUrl(prevPost(post)),
      '[##_tag_label_rep_##]': post.tags.map(function (tag) {
        return '<a href="#tag-' + tag.toLowerCase() + '">#' + tag + '</a>';
      }).join(' ')
    };
    replaceTextPlaceholders($('.area-view') || document.body, map);
    replaceAttributePlaceholders($('.area-view') || document.body, map);
    replaceTextPlaceholders($('.yrbe-article-hero') || document.body, map);
    replaceAttributePlaceholders($('.yrbe-article-hero') || document.body, map);
    setText('.yrbe-breadcrumb span, .yrbe-badge, .badge--article', post.category);
    setText('.yrbe-article-title, .article__title, .title_post', post.title);
    setText('.yrbe-article-meta span:first-child, .article__meta .writer', blog.author);
    setText('.yrbe-article-meta span:last-child, .article__meta .date, .title_post + .info .date', post.date);
    setText('.yrbe-article-dek', post.summary);

    $all('.yrbe-article-body, .area-view .article__body').forEach(function (body, index) {
      if (index === 0 || body.classList.contains('yrbe-article-body')) body.innerHTML = post.body;
    });
    updateArticleLink('.yrbe-article-nav-block li:first-child a', prevPost(post));
    updateArticleLink('.yrbe-article-nav-block li:last-child a, .yrbe-bottom-next a', nextPost(post));
    $all('.article-header').forEach(function (header) {
      header.style.backgroundImage = post.thumbnail;
    });
    renderToc();
  }

  function nextPost(post) {
    var index = posts.indexOf(post);
    return posts[(index + 1) % posts.length];
  }

  function updateArticleLink(selector, post) {
    $all(selector).forEach(function (link) {
      link.href = postUrl(post);
      link.classList.add('js-local-post-link');
      link.setAttribute('data-post-slug', post.slug);
      var strong = $('strong', link);
      if (strong) {
        strong.textContent = post.title;
      } else {
        link.textContent = post.title;
      }
    });
  }

  function prevPost(post) {
    var index = posts.indexOf(post);
    return posts[(index + posts.length - 1) % posts.length];
  }

  function renderToc() {
    var toc = $('#yrbe-toc');
    if (!toc) return;
    $all('a', toc).forEach(function (a) { a.remove(); });
    $all('.yrbe-article-body h2, .yrbe-article-body h3').forEach(function (heading, index) {
      if (!heading.id) heading.id = 'local-toc-' + index;
      var link = document.createElement('a');
      link.href = '#' + heading.id;
      link.textContent = heading.textContent;
      if (heading.tagName === 'H3') link.style.paddingLeft = '14px';
      toc.appendChild(link);
    });
  }

  function renderRoute() {
    var slug = currentSlug();
    if (slug) {
      document.body.id = 'tt-body-page';
      document.body.setAttribute('data-local-view', 'page');
      renderArticle(findPost(slug));
    } else {
      document.body.id = 'tt-body-index';
      document.body.setAttribute('data-local-view', 'list');
    }
    try {
      window.scrollTo({ top: 0, behavior: 'instant' });
    } catch (error) {
      window.scrollTo(0, 0);
    }
  }

  function navigateToList() {
    history.pushState({}, '', window.location.pathname);
    renderRoute();
  }

  function navigateToPost(slug) {
    history.pushState({ post: slug }, '', postUrl({ slug: slug }));
    renderRoute();
  }

  document.addEventListener('click', function (event) {
    var link = event.target.closest('.js-local-post-link');
    if (!link) return;
    var slug = link.getAttribute('data-post-slug');
    if (!slug) return;
    event.preventDefault();
    navigateToPost(slug);
  });

  window.addEventListener('popstate', renderRoute);

  injectLocalBaseStyle();
  renderGlobalPlaceholders();
  renderList();
  renderSidebar();
  renderRoute();
})();
