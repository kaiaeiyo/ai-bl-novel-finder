const API_BASE = location.protocol === "file:" ? "http://localhost:8620" : "";

let books = [
  {
    id: "po-yun",
    title: "破云",
    author: "淮上",
    tags: ["刑侦", "强强", "美强惨", "悬疑", "正剧"],
    color: "red",
    short: "破\n云",
    hook: "刑侦线和双强对峙一起往前推，关系感不是硬凑出来的。",
    oneLine: "现代都市刑侦悬疑，圆满结局",
    summary: "现代刑侦悬疑文，痞帅刑警严峫×美强惨高智商江停。旧案追查、彼此试探和双向奔赴一起推进，剧情线有分量，感情线也够浓。",
    intro: "城市天空，诡云奔涌。三年前恭州市的缉毒行动中，因总指挥江停判断失误，现场发生连环爆炸。三年后，本应早已殉职的江停奇迹般醒来，重新卷入旧案真相。",
    progress: 154,
  },
  {
    id: "tun-hai",
    title: "破云2吞海",
    author: "淮上",
    tags: ["刑侦", "救赎", "强强", "悬疑"],
    color: "dark",
    short: "吞\n海",
    hook: "冷淡和隐忍不是卖惨，重点是伤口被一点点看见。",
    oneLine: "那些窥探藏在浪潮之下",
    summary: "刑侦悬疑续作，冷静学院派刑警×深渊归来的受。案件推进密，人物关系带着克制和救赎感。",
    intro: "那些窥探的触角隐藏在互联网浪潮中，无处不在，生生不息，正逐渐将现代社会的每个角落淹没至顶。",
    progress: 88,
  },
  {
    id: "mengyan",
    title: "欢迎进入梦魇直播间",
    author: "桑沃",
    tags: ["无限流", "疯批", "直播", "高能"],
    color: "blue",
    short: "梦\n魇",
    hook: "副本压力会把人物关系逼出来，紧张感和感情线能一起走。",
    oneLine: "欢迎来到梦魇直播间",
    summary: "无限流直播副本，主角在高压规则里不断拆局。节奏快、反转密，适合想看刺激和上头感的人。",
    intro: "温简言是一名欺诈师，某天被迫成为梦魇直播间的新人主播。观众以为他马上会翻车，结果他一路骗过副本规则。",
    progress: 211,
  },
  {
    id: "zhengjing",
    title: "我这儿是正经店",
    author: "忘却的悠",
    tags: ["萌宠", "甜文", "日常", "异能"],
    color: "green",
    short: "正\n经",
    hook: "日常互动比较软，甜点藏在相处细节里，适合想放松的时候看。",
    oneLine: "这里真的是正经店",
    summary: "现代异能甜文，温柔店主受×神秘兽医攻。萌宠日常托住感情线，治愈轻松。",
    intro: "一家规矩和其他地方不太一样的店，迎来一位能听懂小动物说话的店主，也迎来一段温柔又奇妙的关系。",
    progress: 42,
  },
  {
    id: "tianguan",
    title: "天官赐福",
    author: "墨香铜臭",
    tags: ["古风", "仙侠", "宿命感", "慢热"],
    color: "green",
    short: "天\n官",
    hook: "宿命感不是一句设定，而是有人跨过很久很久仍然选择你。",
    oneLine: "为你，所向披靡",
    summary: "古风仙侠，神明与信徒、重逢与守候。适合想看长线感情和浓烈宿命感的时候。",
    intro: "为你，所向披靡。八百年后再次飞升的谢怜，遇见了神秘红衣少年花城。",
    progress: 203,
  },
  {
    id: "mou-mou",
    title: "某某",
    author: "木苏里",
    tags: ["校园", "少年感", "酸涩", "慢热"],
    color: "blue",
    short: "某\n某",
    hook: "酸涩不靠硬虐，靠少年心事和没说出口的偏爱。",
    oneLine: "人间骄阳正好，风过林梢",
    summary: "校园文，少年关系从别扭到靠近。节奏干净，后劲落在人和时间里。",
    intro: "人间骄阳正好，风过林梢，彼时他们正当年少。",
    progress: 96,
  },
];

async function apiGet(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) throw new Error("api failed");
  return response.json();
}

async function apiPost(path, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error("api failed");
  return response.json();
}

async function loadServerBooks() {
  try {
    const data = await apiGet("/api/books");
    if (Array.isArray(data.items) && data.items.length) {
      books = data.items;
    }
  } catch {
    // Keep the built-in demo data when the local server is not running.
  }
}

const pageRoot = document.querySelector("#page-root");
const dialog = document.querySelector("#book-dialog");
const dialogContent = document.querySelector("#dialog-content");
const sideTitle = document.querySelector("#side-title");
const sideHook = document.querySelector("#side-hook");
const sideProgress = document.querySelector("#side-progress");
const sideLabel = document.querySelector("#side-label");
const appShell = document.querySelector(".app-shell");

let state = {
  page: "home",
  query: "",
  squareIndex: 0,
  collectionIndex: 0,
  homeCollectionIndex: 0,
  chat: [
    { role: "ai", text: "你可以直接说想看的感觉，不用想标签。比如“想看攻很高高在上但最后彻底栽了”，我会帮你慢慢缩小到具体文。" },
  ],
  wheelBook: null,
};

const collections = [
  {
    title: "强强互探合集",
    keyword: "强强",
    label: "新书专题",
    desc: "那些表面冷静，实际已经被对方牵着走的关系感。",
  },
  {
    title: "酸涩后劲合集",
    keyword: "酸涩",
    label: "后劲专题",
    desc: "不靠硬虐取胜，但读完会在心里慢慢回潮的关系。",
  },
  {
    title: "高能副本合集",
    keyword: "无限流",
    label: "高能专题",
    desc: "规则、副本和危机一起压上来，越读越停不下来的文。",
  },
];

const getFavorites = () => JSON.parse(localStorage.getItem("bl-favorites") || "[]");
const setFavorites = (ids) => localStorage.setItem("bl-favorites", JSON.stringify(ids));
const isFav = (id) => getFavorites().includes(id);
const zhText = (value = "") => String(value)
  .replace(/\bCP\b/g, "感情线")
  .replace(/\bHE\b/g, "圆满结局")
  .replace(/BKing|Bking|bking/g, "拽王");

function clipText(text = "", limit = 100) {
  const clean = String(text || "").trim();
  if (clean.length <= limit) return clean || "暂无简介。";
  return `${clean.slice(0, limit)}...`;
}

function foldedText(text = "", key = "intro", limit = 100) {
  const clean = String(text || "暂无简介。").trim();
  if (clean.length <= limit) return `<p class="plain-intro">${clean}</p>`;
  const preview = clean.slice(0, limit);
  const rest = clean.slice(limit);
  const id = `fold-${String(key).replace(/[^a-zA-Z0-9_-]/g, "-")}`;
  return `
    <div class="fold-text">
      <input id="${id}" type="checkbox" />
      <p>
        <span class="fold-preview">${preview}</span><span class="fold-ellipsis">...</span><span class="fold-rest">${rest}</span><label for="${id}"></label>
      </p>
    </div>
  `;
}

function originalLink(book) {
  if (!book.link) return `<button class="start-button disabled" type="button">暂无原站链接</button>`;
  return `<a class="start-button" href="${book.link}" data-go-link="${book.link}" rel="noreferrer">去原站阅读 ↗</a>`;
}

function matchesCollection(book, keyword = "强强") {
  const text = `${book.title} ${book.author} ${(book.tags || []).join(" ")} ${book.hook} ${book.summary}`;
  return text.includes(keyword);
}

function toggleFavorite(id) {
  const current = getFavorites();
  const favored = !current.includes(id);
  const next = favored ? [id, ...current] : current.filter((item) => item !== id);
  setFavorites(next);
  return favored;
}

function syncFavoriteButtons(id) {
  const favored = isFav(id);
  document.querySelectorAll(`[data-fav="${CSS.escape(id)}"]`).forEach((button) => {
    button.classList.toggle("is-fav", favored);
    if (button.classList.contains("fav-button")) {
      button.innerHTML = `<span>${favored ? "♥" : "♡"}</span> ${favored ? "已收藏" : "收藏"}`;
    } else {
      button.textContent = favored ? "♥" : "♡";
    }
  });
}

function scoreBook(book, query) {
  const text = `${book.title} ${book.author} ${book.tags.join(" ")} ${book.hook} ${book.summary}`;
  return query.split(/\s+|，|、/).filter(Boolean).reduce((score, word) => score + (text.includes(word) ? 3 : 0), 0);
}

function searchBooks(query) {
  if (!query.trim()) return books.slice(0, 4);
  return books
    .map((book) => ({ book, score: scoreBook(book, query) }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .map((item) => item.book);
}

async function serverRecommend(query) {
  try {
    const data = await apiPost("/api/recommend", { query });
    return Array.isArray(data.items) && data.items.length ? data.items : searchBooks(query);
  } catch {
    return searchBooks(query);
  }
}

function updateSide(book, label = "精准匹配") {
  sideLabel.textContent = label;
  sideTitle.textContent = `《${book.title}》`;
  sideHook.textContent = `“${book.hook}”`;
  sideProgress.textContent = book.progress;
}

function tile(book) {
  return `
    <article class="book-tile ${book.color}" data-open="${book.id}">
      <div class="book-cover"><span>${zhText(book.oneLine || book.hook)}</span></div>
      <h3>《${book.title}》</h3>
      <p>${book.tags.slice(0, 2).map(zhText).join(" · ")}</p>
    </article>
  `;
}

function card(book) {
  const favored = isFav(book.id);
  return `
    <article class="result-card" data-open="${book.id}">
      <div class="result-head">
        <div>
          <p class="eyebrow">${book.author}</p>
          <h3>《${book.title}》</h3>
        </div>
        <button class="fav-button ${favored ? "is-fav" : ""}" data-fav="${book.id}"><span>${favored ? "♥" : "♡"}</span> ${favored ? "已收藏" : "收藏"}</button>
      </div>
      <p class="result-hook">${zhText(book.hook)}</p>
      <p class="result-summary">${zhText(book.summary)}</p>
      <div class="tag-row">${book.tags.map((tag) => `<span>${zhText(tag)}</span>`).join("")}</div>
    </article>
  `;
}

function showcase(book) {
  const tags = book.tags || [];
  const favored = isFav(book.id);
  return `
    <section class="book-showcase" data-open="${book.id}">
      <div class="showcase-arrows">
        <button data-flip="-1">↑</button>
        <button data-flip="1" class="circle">↓</button>
      </div>
      <div class="showcase-cover ${book.color}">
        <div class="showcase-cover-text">${zhText(book.oneLine || book.hook)}</div>
      </div>
      <div class="showcase-main">
        <p class="eyebrow">${tags.slice(0, 2).map(zhText).join(" / ") || "智能推荐"}</p>
        <h1>${book.title}</h1>
        <h3>${book.author || "佚名"}</h3>
        <p class="showcase-hook">${zhText(book.hook)}</p>
        <div class="showcase-actions">
          ${originalLink(book)}
          <button class="round-action ${favored ? "is-fav" : ""}" data-fav="${book.id}">${favored ? "♥" : "♡"}</button>
          <button class="round-action">⌁</button>
          <button class="round-action">↓</button>
        </div>
      </div>
      <div class="showcase-details">
        <article>
          <h3>简介</h3>
          <p>${zhText(book.summary)}</p>
          ${foldedText(zhText(book.intro), `showcase-${book.id}`, 100)}
          <div class="reader-note">
            <div class="mini-avatar"></div>
            <div><strong>搜文搭子</strong><p>${zhText(book.hook)}</p></div>
          </div>
        </article>
        <aside>
          <h3>标签</h3>
          <p>${tags.map(zhText).join("、") || "暂无标签"}</p>
          <h3>作者</h3>
          <p>${book.author || "暂无"}</p>
          <h3>原站链接</h3>
          <p>${book.link ? `<a href="${book.link}" data-go-link="${book.link}" rel="noreferrer">去原站阅读</a>` : "暂无链接"}</p>
        </aside>
      </div>
    </section>
  `;
}

function renderHome(results = books.slice(0, 4)) {
  const collection = collections[state.homeCollectionIndex % collections.length];
  pageRoot.innerHTML = `
    <section class="hero-grid">
      <div class="hero-copy">
        <p class="eyebrow">智能搜文助手</p>
        <h1>今晚想看点什么？</h1>
        <p class="hero-text">说出你想看的氛围、人设和避雷点，我来把“那个感觉”翻译成小说。</p>
        <div class="search-card">
          <input id="home-query" value="${state.query}" placeholder="想看攻后面越来越爱老婆的 / 酸涩但别太虐" />
          <button id="home-search">开始找文</button>
        </div>
      </div>
      <div class="open-book fortune-bookmark-card" data-open="${results[0].id}" aria-label="今日签文">
        <div class="bookmark-hole"></div>
        <div class="bookmark-copy">
          <small>今日签文</small>
          <h2>《${results[0].title}》</h2>
          <p>${clipText(zhText(results[0].summary), 92)}</p>
        </div>
      </div>
    </section>
    <section class="book-section">
      <div class="section-title-row">
        <h2>${state.query ? "为你找到" : "热门书架"}</h2>
        <button class="text-button" id="shuffle-books">换一批</button>
      </div>
      <div class="book-shelf">${results.map(tile).join("")}</div>
    </section>
    <section class="collection-card">
      <button class="collection-nav prev" data-home-collection-flip="-1" aria-label="上一个合集">‹</button>
      <div class="stacked-covers"><span></span><span></span><span></span></div>
      <div><p class="eyebrow">${collection.label}</p><h2>${collection.title}</h2><p>${collection.desc}</p></div>
      <button class="open-collection" data-collection="${collection.keyword}" data-collection-title="${collection.title}">打开合集</button>
      <button class="collection-nav next" data-home-collection-flip="1" aria-label="下一个合集">›</button>
    </section>
  `;
}

function renderSquare() {
  const book = books[state.squareIndex % books.length];
  const favored = isFav(book.id);
  pageRoot.innerHTML = `
    <section class="square-view">
      <article class="flat-reader">
        <button class="flat-turn left" data-flip="-1">‹</button>
        <div class="flat-main">
          <p class="eyebrow">${(book.tags || []).slice(0, 2).map(zhText).join(" / ") || "智能推荐"}</p>
          <h1>${book.title}</h1>
          <h3>${book.author || "佚名"}</h3>
          <p class="flat-hook">${zhText(book.hook)}</p>
          <div class="flat-actions">
            ${originalLink(book)}
            <button class="round-action ${favored ? "is-fav" : ""}" data-fav="${book.id}">${favored ? "♥" : "♡"}</button>
          </div>
        </div>
        <div class="flat-details">
          <h3>简介</h3>
          <p>${zhText(book.summary)}</p>
          ${foldedText(zhText(book.intro), `square-${book.id}`, 100)}
          <h3>标签</h3>
          <div class="tag-row">${(book.tags || []).map((tag) => `<span>${zhText(tag)}</span>`).join("")}</div>
        </div>
        <button class="flat-turn right" data-flip="1">›</button>
      </article>
      <div class="square-footer-meta">
        <span>广场发现</span>
        <span>第 ${state.squareIndex + 1} / ${books.length} 本</span>
      </div>
    </section>
  `;
  updateSide(book, "广场推荐");
}

function replyFor(text) {
  if (text.includes("酸") || text.includes("虐")) return { text: "你要的更像有拉扯、有后劲，但不是把人虐到喘不过气。我先给你捞一本校园酸涩向。", picks: [books.find((b) => b.id === "mou-mou")] };
  if (text.includes("疯") || text.includes("无限")) return { text: "这个方向我懂，重点不是乱疯，而是高压环境里人物关系被逼出来。先看这本。", picks: [books.find((b) => b.id === "mengyan")] };
  if (text.includes("刑") || text.includes("案") || text.includes("破")) return { text: "你应该会更吃剧情线有分量、感情张力跟着案件一起走的类型。", picks: [books[0], books[1]] };
  return { text: "我先理解成：你想要关系感明确、读起来有抓力的文。你也可以再补一句题材，比如现代、古耽、无限流或校园。", picks: [books[0]] };
}

async function serverReplyFor(text) {
  try {
    const data = await apiPost("/api/chat", { text });
    return {
      text: data.reply || replyFor(text).text,
      picks: Array.isArray(data.items) ? data.items : [],
    };
  } catch {
    return replyFor(text);
  }
}

async function serverDrawBook() {
  try {
    return await apiGet("/api/wheel");
  } catch {
    return books[Math.floor(Math.random() * books.length)];
  }
}

function renderChat() {
  pageRoot.innerHTML = `
    <section class="chat-phone">
      <div class="chat-phone-body ${state.chat.length <= 1 ? "empty" : ""}">
        ${state.chat.length <= 1 ? `
          <h1>想找什么文？</h1>
          <div class="starter-bubbles">
            <button data-chat-prompt="想看攻后面越来越爱老婆的">攻越来越爱老婆</button>
            <button data-chat-prompt="想看酸涩一点但别太虐">酸涩但别太虐</button>
          </div>
        ` : `
          <div class="chat-list">
            ${state.chat.map((msg) => `<div class="bubble ${msg.role}">${msg.text}</div>${msg.cards ? `<div class="chat-cards">${msg.cards.map(card).join("")}</div>` : ""}`).join("")}
          </div>
        `}
      </div>
      <div class="chat-input">
        <input id="chat-text" placeholder="说说你想看的感觉" />
        <button id="chat-send" aria-label="发送">↑</button>
      </div>
      <p class="chat-tip">搜文搭子会帮你把感觉慢慢缩小到具体文。</p>
    </section>
  `;
}

function renderWheel() {
  const book = state.wheelBook;
  pageRoot.innerHTML = `
    <section class="wheel-view">
      <p class="eyebrow">找文求签</p>
      <h1 class="page-title">今天适合看哪一本？</h1>
      <div class="fortune-stage qian-stage">
        <button class="qian-tube-button" id="draw-lot" aria-label="点击签筒抽签">
          <img src="assets/fortune-tube.png?v=2" alt="签筒" />
        </button>
        <p>点击求签</p>
      </div>
    </section>
  `;
  if (book) updateSide(book, "今日签文");
}

function renderProfile() {
  const favs = getFavorites().map((id) => books.find((book) => book.id === id)).filter(Boolean);
  pageRoot.innerHTML = `
    <section class="profile-view">
      <p class="eyebrow">我的</p>
      <h1 class="page-title">我的收藏</h1>
      ${favs.length ? `<div class="result-grid">${favs.map(card).join("")}</div>` : `<div class="empty-state">还没有收藏的文。遇到喜欢的文时，点一下小书签。</div>`}
    </section>
  `;
}

function render() {
  appShell.classList.toggle("no-reader", ["square", "wheel", "profile"].includes(state.page));
  document.querySelectorAll("[data-page]").forEach((button) => button.classList.toggle("active", button.dataset.page === state.page));
  if (state.page === "home") renderHome(searchBooks(state.query));
  if (state.page === "square") renderSquare();
  if (state.page === "chat") renderChat();
  if (state.page === "wheel") renderWheel();
  if (state.page === "profile") renderProfile();
}

function openCollection(keyword = "强强", title = "强强互探合集") {
  const items = books.filter((book) => matchesCollection(book, keyword));
  const pool = items.length ? items : books;
  const idx = state.collectionIndex % pool.length;
  const book = pool[idx];
  const favored = isFav(book.id);
  dialogContent.innerHTML = `
    <button class="close-dialog" id="close-dialog">×</button>
    <section class="drawer-sheet">
      <div class="drawer-head">
        <div>
          <p class="eyebrow">合集：${keyword}</p>
          <h2>${title}</h2>
        </div>
        <span>${idx + 1} / ${pool.length}</span>
      </div>
      <article class="flat-reader drawer-reader">
        <button class="flat-turn left" data-collection-flip="-1" data-keyword="${keyword}" data-title="${title}">‹</button>
        <div class="flat-main">
          <p class="eyebrow">${(book.tags || []).slice(0, 2).map(zhText).join(" / ") || "智能推荐"}</p>
          <h1>${book.title}</h1>
          <h3>${book.author || "佚名"}</h3>
          <p class="flat-hook">${zhText(book.hook)}</p>
          <div class="flat-actions">${originalLink(book)}<button class="round-action ${favored ? "is-fav" : ""}" data-fav="${book.id}">${favored ? "♥" : "♡"}</button></div>
        </div>
        <div class="flat-details">
          <h3>简介</h3>
          <p>${zhText(book.summary)}</p>
          ${foldedText(zhText(book.intro), `drawer-${book.id}`, 100)}
          <h3>标签</h3>
          <div class="tag-row">${(book.tags || []).map((tag) => `<span>${zhText(tag)}</span>`).join("")}</div>
        </div>
        <button class="flat-turn right" data-collection-flip="1" data-keyword="${keyword}" data-title="${title}">›</button>
      </article>
    </section>
  `;
  dialog.classList.add("drawer-dialog");
  dialog.showModal();
}

function openBook(id) {
  const book = books.find((item) => item.id === id);
  if (!book) return;
  updateSide(book, "正在查看");
  dialog.classList.add("drawer-dialog");
  const favored = isFav(book.id);
  dialogContent.innerHTML = `
    <button class="close-dialog" id="close-dialog">×</button>
    <section class="drawer-sheet">
      <div class="drawer-head">
        <div>
          <p class="eyebrow">书籍详情</p>
        </div>
      </div>
      <article class="flat-reader drawer-reader">
        <div class="flat-main">
          <p class="eyebrow">${(book.tags || []).slice(0, 2).map(zhText).join(" / ") || "智能推荐"}</p>
          <h1>${book.title}</h1>
          <h3>${book.author || "佚名"}</h3>
          <p class="flat-hook">${zhText(book.hook)}</p>
          <div class="flat-actions">${originalLink(book)}<button class="round-action ${favored ? "is-fav" : ""}" data-fav="${book.id}">${favored ? "♥" : "♡"}</button></div>
        </div>
        <div class="flat-details">
          <h3>简介</h3>
          <p>${zhText(book.summary)}</p>
          ${foldedText(zhText(book.intro), `book-${book.id}`, 100)}
          <h3>标签</h3>
          <div class="tag-row">${(book.tags || []).map((tag) => `<span>${zhText(tag)}</span>`).join("")}</div>
        </div>
      </article>
    </section>
  `;
  dialog.showModal();
}

document.addEventListener("click", async (event) => {
  const goLink = event.target.closest("[data-go-link]");
  if (goLink) {
    event.preventDefault();
    window.location.href = goLink.dataset.goLink;
    return;
  }
  const pageButton = event.target.closest("[data-page], [data-page-jump]");
  if (pageButton) {
    state.page = pageButton.dataset.page || pageButton.dataset.pageJump;
    render();
    return;
  }
  const homeCollectionFlip = event.target.closest("[data-home-collection-flip]");
  if (homeCollectionFlip) {
    state.homeCollectionIndex = (state.homeCollectionIndex + Number(homeCollectionFlip.dataset.homeCollectionFlip) + collections.length) % collections.length;
    render();
    return;
  }
  const collectionButton = event.target.closest("[data-collection]");
  if (collectionButton) {
    state.collectionIndex = 0;
    openCollection(collectionButton.dataset.collection, collectionButton.dataset.collectionTitle);
    return;
  }
  const collectionFlip = event.target.closest("[data-collection-flip]");
  if (collectionFlip) {
    const keyword = collectionFlip.dataset.keyword || "强强";
    const title = collectionFlip.dataset.title || "强强互探合集";
    const poolLength = books.filter((book) => matchesCollection(book, keyword)).length || books.length;
    state.collectionIndex = (state.collectionIndex + Number(collectionFlip.dataset.collectionFlip) + poolLength) % poolLength;
    dialog.close();
    openCollection(keyword, title);
    return;
  }
  const openTarget = event.target.closest("[data-open]");
  const openButton = event.target.closest(".start-button[data-open]");
  if (openButton) {
    openBook(openButton.dataset.open);
    return;
  }
  if (openTarget && !event.target.closest("button") && !event.target.closest("a")) openBook(openTarget.dataset.open);
  const favTarget = event.target.closest("[data-fav]");
  if (favTarget) {
    event.stopPropagation();
    toggleFavorite(favTarget.dataset.fav);
    syncFavoriteButtons(favTarget.dataset.fav);
    if (state.page === "profile") render();
    return;
  }
  const flip = event.target.closest("[data-flip]");
  if (flip) {
    state.squareIndex = (state.squareIndex + Number(flip.dataset.flip) + books.length) % books.length;
    render();
  }
  if (event.target.id === "home-search") {
    state.query = document.querySelector("#home-query").value.trim();
    appShell.classList.remove("no-reader");
    renderHome(await serverRecommend(state.query));
  }
  if (event.target.id === "shuffle-books") {
    books.push(books.shift());
    render();
  }
  if (event.target.id === "chat-send") {
    const input = document.querySelector("#chat-text");
    const text = input.value.trim();
    if (!text) return;
    const reply = await serverReplyFor(text);
    state.chat.push({ role: "user", text }, { role: "ai", text: reply.text, cards: reply.picks });
    render();
  }
  const chatPrompt = event.target.closest("[data-chat-prompt]");
  if (chatPrompt) {
    const text = chatPrompt.dataset.chatPrompt;
    const reply = await serverReplyFor(text);
    state.chat.push({ role: "user", text }, { role: "ai", text: reply.text, cards: reply.picks });
    render();
  }
  const drawLot = event.target.closest("#draw-lot");
  if (drawLot) {
    drawLot.classList.add("shaking");
    await new Promise((resolve) => setTimeout(resolve, 720));
    state.wheelBook = await serverDrawBook();
    render();
    openBook(state.wheelBook.id);
  }
  if (event.target.id === "close-dialog") {
    dialog.classList.remove("drawer-dialog");
    dialog.close();
  }
});

document.querySelector("#global-search").addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    state.query = event.target.value.trim();
    state.page = "home";
    appShell.classList.remove("no-reader");
    document.querySelectorAll("[data-page]").forEach((button) => button.classList.toggle("active", button.dataset.page === "home"));
    serverRecommend(state.query).then(renderHome);
  }
});

loadServerBooks().then(render);
