/* Maçon Studio — content editor for studiomacon.co
   Auth: Supabase magic link, restricted to the keepers by RLS.
   Saves go straight to Supabase; the site rebuilds on Publish (or within 15 min). */

const CFG_URL = "../supabase-config.json";
let sb, session, products = [], current = null, dirty = false;

const $ = s => document.querySelector(s);
const el = (t, c, h) => { const e = document.createElement(t); if (c) e.className = c; if (h != null) e.innerHTML = h; return e; };

function toast(msg, isErr) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.toggle("err", !!isErr);
  t.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.remove("show"), isErr ? 6000 : 2600);
}

/* small on-page readout so sign-in problems are visible without DevTools */
const BUILD = "2026-08-03h";
function diag(extra) {
  const d = $("#diag");
  if (!d) return;
  let store = "ok";
  try { localStorage.setItem("_t", "1"); localStorage.removeItem("_t"); }
  catch (e) { store = "BLOCKED"; }
  d.textContent = `build ${BUILD} · session ${session ? "yes" : "no"} · storage ${store}`
                + (extra ? ` · ${extra}` : "");
}

/* ---------------- boot ---------------- */
(async function boot() {
  const cfg = await (await fetch(CFG_URL)).json();
  // implicit flow: the token arrives in the URL hash, so the link still works
  // when the email is opened in a different browser than it was requested from
  // (PKCE would need a code_verifier from the originating browser).
  sb = supabase.createClient(cfg.supabase_url, cfg.supabase_anon_key, {
    auth: { flowType: "implicit", detectSessionInUrl: true, persistSession: true,
            autoRefreshToken: true, storageKey: "macon-studio-auth" }
  });

  // surface anything Supabase sent back instead of failing silently
  const hash = new URLSearchParams(location.hash.replace(/^#/, ""));
  const query = new URLSearchParams(location.search);
  const err = hash.get("error_description") || hash.get("error")
           || query.get("error_description") || query.get("error");
  if (err) {
    $("#gateMsg").textContent = decodeURIComponent(err).replace(/\+/g, " ");
    console.warn("[auth]", err);
  }

  // PKCE fallback: if a ?code= ever shows up, exchange it explicitly
  const code = query.get("code");
  if (code) {
    const { error } = await sb.auth.exchangeCodeForSession(code);
    if (error) { $("#gateMsg").textContent = error.message; console.warn("[auth] exchange", error); }
  }

  const { data } = await sb.auth.getSession();
  session = data.session;
  sb.auth.onAuthStateChange((evt, s) => {
    console.log("[auth]", evt, s ? s.user.email : "no session");
    // only SIGNED_OUT should tear down the UI — a late INITIAL_SESSION(null)
    // must not knock an already-signed-in user back to the gate
    if (evt === "SIGNED_OUT") { session = null; render(); return; }
    if (typeof diag === "function") diag("event " + evt);
    if (!s) return;
    session = s;
    history.replaceState(null, "", location.pathname);   // tidy the token out of the URL
    render();
  });
  render();
})();

async function render() {
  diag();
  if (!session) { $("#gate").hidden = false; $("#app").hidden = true; return; }
  $("#gate").hidden = true;
  $("#app").hidden = false;
  $("#who").textContent = session.user?.email || "";
  try {
    await loadProducts();
  } catch (err) {
    console.error("[load]", err);
    toast("Signed in, but loading products failed: " + err.message, true);
  }
}

/* ---------------- auth ---------------- */
/* password sign-in — the keepers already have these from the Archive */
$("#loginForm").addEventListener("submit", async e => {
  e.preventDefault();
  const email = $("#email").value.trim();
  const password = $("#password").value;
  const msg = $("#gateMsg");
  if (!password) { return sendMagicLink(email); }   // empty password -> link flow
  msg.textContent = "Signing in…";
  const { data, error } = await sb.auth.signInWithPassword({ email, password });
  if (error) {
    msg.textContent = error.message;
    console.warn("[auth] password", error);
    diag("error: " + error.message);
    return;
  }
  console.log("[auth] signInWithPassword ok; session:", !!data?.session,
              "user:", data?.user?.email, "mfa:", data?.user?.factors?.length || 0);
  if (!data?.session) {
    msg.textContent = "Signed in, but no session came back — the account may need "
                    + "email confirmation or a second factor.";
    return;
  }
  // don't wait on onAuthStateChange — drive the UI directly
  session = data.session;
  msg.textContent = "";
  diag("signed in");
  await render();
});

/* magic link — fallback; needs this URL allowlisted in Supabase redirect URLs */
async function sendMagicLink(email) {
  const redirect = location.origin + location.pathname;
  const msg = $("#gateMsg");
  msg.textContent = "Sending…";
  const { error } = await sb.auth.signInWithOtp({ email, options: { emailRedirectTo: redirect } });
  if (error) {
    msg.textContent = error.message;
    console.warn("[auth] signInWithOtp", error);
    return;
  }
  msg.innerHTML = "Check your email — the sign-in link is on its way.<br>" +
                  "<span style='opacity:.7'>Open it in this same browser.</span>";
  console.log("[auth] magic link requested, redirect =", redirect);
}

$("#linkInstead").addEventListener("click", () => {
  const email = $("#email").value.trim();
  if (!email) { $("#gateMsg").textContent = "Enter your email first."; return; }
  sendMagicLink(email);
});

$("#signOut").addEventListener("click", async () => {
  await sb.auth.signOut();
  location.reload();
});

/* ---------------- data ---------------- */
async function loadProducts() {
  const rows = $("#rows");
  if (rows) rows.innerHTML = '<div class="empty">Loading…</div>';
  const { data, error, status } = await sb
    .from("store_products")
    .select("*,store_product_images(*)")
    .order("sort_order");
  if (error) {
    console.error("[load]", status, error);
    toast(error.message, true);
    if (rows) rows.innerHTML =
      `<div class="empty">Couldn't load products (HTTP ${status}).<br>` +
      `${escapeHtml(error.message)}<br>` +
      `<span class="empty-hint">${escapeHtml(error.hint || error.details || "")}</span></div>`;
    return;
  }
  products = data || [];
  console.log("[load] products:", products.length);
  drawList();
}

function imgsOf(p) {
  return (p.store_product_images || []).slice().sort((a, b) => a.sort_order - b.sort_order);
}

function publicUrl(u) {
  // migrated rows hold repo-relative paths; uploads hold full Storage URLs
  return u.startsWith("http") ? u : "../" + u;
}

/* ---------------- list ---------------- */
function drawList() {
  const filter = $("#filterCollection").value;
  const rows = $("#rows");
  rows.innerHTML = "";
  if (!products.length) {
    rows.innerHTML = '<div class="empty">No products returned.<br>' +
      '<span class="empty-hint">You are signed in, but the query came back empty — ' +
      'usually a row-level security rule.</span></div>';
    return;
  }
  products
    .filter(p => !filter || p.collection === filter)
    .forEach(p => {
      const imgs = imgsOf(p);
      const r = el("div", "row");
      r.draggable = true;
      r.dataset.id = p.id;
      r.innerHTML = `
        <div class="grip" title="Drag to reorder">⠿</div>
        <img class="row-img" src="${imgs[0] ? publicUrl(imgs[0].url) : ""}" alt="" loading="lazy" decoding="async">
        <div>
          <div class="row-name">${escapeHtml(p.name)}</div>
          <div class="row-slug">/${p.slug} · ${imgs.length} image${imgs.length === 1 ? "" : "s"}</div>
        </div>
        <div class="row-price">${p.price ? "$" + Number(p.price).toLocaleString() : "—"}</div>
        <div><span class="pill ${p.collection}">${p.collection}</span></div>
        <div><span class="pill ${p.status}">${p.status.replace("_", " ")}</span></div>`;
      r.addEventListener("click", ev => { if (!ev.target.closest(".grip")) openEditor(p.id); });
      wireRowDrag(r);
      rows.appendChild(r);
    });
}

$("#filterCollection").addEventListener("change", drawList);

/* drag to reorder products */
let dragRow = null;
function wireRowDrag(r) {
  r.addEventListener("dragstart", e => { dragRow = r; r.classList.add("dragging"); e.dataTransfer.effectAllowed = "move"; });
  r.addEventListener("dragend", () => { r.classList.remove("dragging"); dragRow = null; document.querySelectorAll(".row").forEach(x => x.classList.remove("drop-target")); });
  r.addEventListener("dragover", e => { e.preventDefault(); if (dragRow && dragRow !== r) r.classList.add("drop-target"); });
  r.addEventListener("dragleave", () => r.classList.remove("drop-target"));
  r.addEventListener("drop", async e => {
    e.preventDefault();
    r.classList.remove("drop-target");
    if (!dragRow || dragRow === r) return;
    const ids = [...document.querySelectorAll(".row")].map(x => x.dataset.id);
    const from = ids.indexOf(dragRow.dataset.id), to = ids.indexOf(r.dataset.id);
    ids.splice(to, 0, ids.splice(from, 1)[0]);
    await Promise.all(ids.map((id, i) =>
      sb.from("store_products").update({ sort_order: i }).eq("id", id)));
    ids.forEach((id, i) => { const p = products.find(x => x.id === id); if (p) p.sort_order = i; });
    products.sort((a, b) => a.sort_order - b.sort_order);
    drawList();
    toast("Order saved");
  });
}

/* ---------------- editor ---------------- */
function openEditor(id) {
  current = products.find(p => p.id === id);
  if (!current) return;
  $("#listView").hidden = true;
  $("#editView").hidden = false;
  $("#f_name").value = current.name || "";
  $("#f_slug").value = current.slug || "";
  $("#f_price").value = current.price ?? "";
  $("#f_desc").value = current.description || "";
  $("#f_notes").value = (current.notes || []).join("\n");
  $("#f_collection").value = current.collection || "perennial";
  $("#f_status").value = current.status || "draft";
  $("#f_qty").value = current.quantity ?? "";
  $("#f_release").value = current.release_at ? current.release_at.slice(0, 16) : "";
  toggleRelease();
  drawImages();
  $("#savedAt").textContent = current.updated_at
    ? "Last saved " + new Date(current.updated_at).toLocaleString() : "";
  dirty = false;
  window.scrollTo(0, 0);
}

$("#backBtn").addEventListener("click", () => {
  if (dirty && !confirm("You have unsaved changes. Leave without saving?")) return;
  $("#editView").hidden = true;
  $("#listView").hidden = false;
  current = null;
});

$("#f_status").addEventListener("change", toggleRelease);
function toggleRelease() {
  $("#releaseWrap").hidden = $("#f_status").value !== "scheduled";
}
["f_name","f_slug","f_price","f_desc","f_notes","f_collection","f_status","f_qty","f_release"]
  .forEach(id => $("#" + id).addEventListener("input", () => { dirty = true; }));

$("#saveBtn").addEventListener("click", async () => {
  if (!current) return;
  const btn = $("#saveBtn");
  btn.disabled = true; btn.textContent = "Saving…";
  const notes = $("#f_notes").value.split("\n").map(s => s.trim()).filter(Boolean);
  const patch = {
    name: $("#f_name").value.trim(),
    slug: $("#f_slug").value.trim(),
    price: $("#f_price").value === "" ? null : Number($("#f_price").value),
    description: $("#f_desc").value.trim(),
    notes,
    collection: $("#f_collection").value,
    status: $("#f_status").value,
    quantity: $("#f_qty").value === "" ? null : Number($("#f_qty").value),
    release_at: $("#f_status").value === "scheduled" && $("#f_release").value
      ? new Date($("#f_release").value).toISOString() : null,
  };
  const { error } = await sb.from("store_products").update(patch).eq("id", current.id);
  btn.disabled = false; btn.textContent = "Save";
  if (error) return toast(error.message, true);
  Object.assign(current, patch);
  dirty = false;
  toast("Saved");
  $("#savedAt").textContent = "Last saved just now";
  drawList();
});

$("#deleteBtn").addEventListener("click", async () => {
  if (!current) return;
  if (!confirm(`Delete “${current.name}” and its images? This cannot be undone.`)) return;
  const { error } = await sb.from("store_products").delete().eq("id", current.id);
  if (error) return toast(error.message, true);
  products = products.filter(p => p.id !== current.id);
  current = null;
  $("#editView").hidden = true; $("#listView").hidden = false;
  drawList();
  toast("Deleted");
});

$("#newProduct").addEventListener("click", async () => {
  const name = prompt("Name of the new piece?");
  if (!name) return;
  const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const { data, error } = await sb.from("store_products")
    .insert({ name, slug, status: "draft", collection: "perennial",
              sort_order: products.length })
    .select("*,store_product_images(*)").single();
  if (error) return toast(error.message, true);
  products.push(data);
  drawList();
  openEditor(data.id);
  toast("Created as a draft");
});

/* ---------------- images ---------------- */
function drawImages() {
  const grid = $("#imgGrid");
  grid.innerHTML = "";
  imgsOf(current).forEach((im, i) => {
    const c = el("div", "img-cell");
    c.draggable = true;
    c.dataset.id = im.id;
    const v = im.variant || "untagged";
    const label = v === "hand" ? "In hand" : v === "plain" ? "Plain bg" : "Untagged";
    c.innerHTML = `<img src="${publicUrl(im.url)}" alt="" loading="lazy">
      <button class="rm" title="Remove">×</button>
      <button class="var ${v}" title="Is this the piece held in a hand, or on a plain background? The shop grid alternates the two and swaps between them on hover.">${label}</button>
      ${i === 0 ? '<span class="first">Thumbnail</span>' : ""}`;
    c.querySelector(".var").addEventListener("click", async ev => {
      ev.stopPropagation();
      const next = (im.variant === "hand") ? "plain" : "hand";
      const { error } = await sb.from("store_product_images")
        .update({ variant: next }).eq("id", im.id);
      if (error) return toast(error.message, true);
      im.variant = next;
      drawImages();
      toast(next === "hand" ? "Marked as in-hand shot" : "Marked as plain shot");
    });
    c.querySelector(".rm").addEventListener("click", async ev => {
      ev.stopPropagation();
      if (!confirm("Remove this image?")) return;
      const { error } = await sb.from("store_product_images").delete().eq("id", im.id);
      if (error) return toast(error.message, true);
      current.store_product_images = current.store_product_images.filter(x => x.id !== im.id);
      drawImages(); drawList(); toast("Image removed");
    });
    wireImgDrag(c);
    grid.appendChild(c);
  });
}

let dragImg = null;
function wireImgDrag(c) {
  c.addEventListener("dragstart", e => { dragImg = c; c.classList.add("dragging"); e.dataTransfer.effectAllowed = "move"; });
  c.addEventListener("dragend", () => { c.classList.remove("dragging"); dragImg = null; document.querySelectorAll(".img-cell").forEach(x => x.classList.remove("drop-target")); });
  c.addEventListener("dragover", e => { e.preventDefault(); if (dragImg && dragImg !== c) c.classList.add("drop-target"); });
  c.addEventListener("dragleave", () => c.classList.remove("drop-target"));
  c.addEventListener("drop", async e => {
    e.preventDefault(); c.classList.remove("drop-target");
    if (!dragImg || dragImg === c) return;
    const ids = [...document.querySelectorAll(".img-cell")].map(x => x.dataset.id);
    const from = ids.indexOf(dragImg.dataset.id), to = ids.indexOf(c.dataset.id);
    ids.splice(to, 0, ids.splice(from, 1)[0]);
    await Promise.all(ids.map((id, i) =>
      sb.from("store_product_images").update({ sort_order: i }).eq("id", id)));
    ids.forEach((id, i) => {
      const im = current.store_product_images.find(x => x.id === id);
      if (im) im.sort_order = i;
    });
    drawImages(); drawList(); toast("Image order saved");
  });
}

$(".upload").addEventListener("click", () => $("#fileInput").click());
$("#fileInput").addEventListener("change", async e => {
  const files = [...e.target.files];
  if (!files.length || !current) return;
  const note = el("div", "uploading", `Uploading 0/${files.length}…`);
  $("#imgGrid").after(note);
  let n = 0, start = imgsOf(current).length;
  for (const f of files) {
    const ext = (f.name.split(".").pop() || "jpg").toLowerCase();
    const path = `${current.slug}/${Date.now()}-${Math.random().toString(36).slice(2, 8)}.${ext}`;
    const { error: upErr } = await sb.storage.from("store-media")
      .upload(path, f, { cacheControl: "31536000", upsert: false });
    if (upErr) { toast(upErr.message, true); break; }
    const { data: pub } = sb.storage.from("store-media").getPublicUrl(path);
    const { data: row, error } = await sb.from("store_product_images")
      .insert({ product_id: current.id, url: pub.publicUrl, alt: current.name, sort_order: start + n })
      .select().single();
    if (error) { toast(error.message, true); break; }
    current.store_product_images.push(row);
    note.textContent = `Uploading ${++n}/${files.length}…`;
  }
  note.remove();
  e.target.value = "";
  drawImages(); drawList();
  if (n) toast(`${n} image${n === 1 ? "" : "s"} added`);
});

/* ---------------- publish ---------------- */
$("#publishBtn").addEventListener("click", () => {
  toast("Saved changes go live within 15 minutes.");
});

function escapeHtml(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g,
    m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
}

window.addEventListener("beforeunload", e => {
  if (dirty) { e.preventDefault(); e.returnValue = ""; }
});

/* ================= views ================= */
const VIEWS = {
  products: ["listView"], pages: ["pagesView"], home: ["homeView"],
};
function showView(name) {
  ["listView","editView","pagesView","pageEditView","homeView"].forEach(id => {
    const n = $("#" + id); if (n) n.hidden = true;
  });
  (VIEWS[name] || VIEWS.products).forEach(id => { const n = $("#" + id); if (n) n.hidden = false; });
  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("on", t.dataset.view === name));
  if (name === "pages") loadPages();
  if (name === "home") loadHome();
}
document.querySelectorAll(".tab").forEach(t =>
  t.addEventListener("click", () => showView(t.dataset.view)));

/* ================= pages ================= */
const PAGE_FILES = { story: "story.html", custom: "custom.html",
                     shipping: "shipping.html", contact: "contact.html" };
let pages = [], currentPage = null;

async function loadPages() {
  const list = $("#pageList");
  list.innerHTML = '<div class="empty">Loading…</div>';
  const { data, error } = await sb.from("store_pages").select("*");
  if (error) { list.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`; return; }
  const order = ["story","custom","shipping","contact"];
  pages = (data || []).sort((a,b) => order.indexOf(a.key) - order.indexOf(b.key));
  list.innerHTML = "";
  pages.forEach(pg => {
    const n = (pg.body || []).length;
    const r = el("div", "row row-page");
    r.innerHTML = `<div class="row-name">${escapeHtml(pg.title || pg.key)}</div>
      <div class="row-slug">/${PAGE_FILES[pg.key] || pg.key} · ${n} block${n===1?"":"s"}</div>`;
    r.addEventListener("click", () => openPage(pg.key));
    list.appendChild(r);
  });
}

function openPage(key) {
  currentPage = pages.find(p => p.key === key);
  if (!currentPage) return;
  showView("pages");
  $("#pagesView").hidden = true;
  $("#pageEditView").hidden = false;
  $("#pg_title").value = currentPage.title || "";
  $("#pageView").href = "../" + (PAGE_FILES[key] || "");
  $("#pageSavedAt").textContent = currentPage.updated_at
    ? "Last saved " + new Date(currentPage.updated_at).toLocaleString() : "";
  drawBlocks();
  window.scrollTo(0, 0);
}
$("#pageBack").addEventListener("click", () => { $("#pageEditView").hidden = true; showView("pages"); });

function blockFields(b, i) {
  const T = (label, val, key, rows) => rows
    ? `<label class="bf"><span>${label}</span><textarea rows="${rows}" data-k="${key}">${escapeHtml(val||"")}</textarea></label>`
    : `<label class="bf"><span>${label}</span><input type="text" data-k="${key}" value="${escapeHtml(val||"")}"></label>`;
  switch (b.type) {
    case "h3":      return T("Heading", b.text, "text");
    case "lead":    return T("Lead text", b.text, "text", 3);
    case "p":       return T("Paragraph", b.text, "text", 4);
    case "caption": return T("Caption", b.text, "text");
    case "html":    return T("Text (HTML allowed)", b.html, "html", 3);
    case "img":     return imgField("Image", b.src, "src", i) + T("Alt text", b.alt, "alt");
    case "twoup":   return imgField("Left image", b.src1, "src1", i) + imgField("Right image", b.src2, "src2", i);
    case "steps":   return (b.items||[]).map((s,k) =>
                      `<div class="step-row">${imgField("Step "+(k+1), s.src, "items."+k+".src", i)}
                       <label class="bf"><span>Caption</span><input type="text" data-k="items.${k}.caption" value="${escapeHtml(s.caption||"")}"></label></div>`).join("");
    default:        return "";
  }
}
function imgField(label, src, key, i) {
  return `<div class="bf">
    <span>${label}</span>
    <div class="bimg">
      ${src ? `<img src="${publicUrl(src)}" alt="">` : '<div class="bimg-none">none</div>'}
      <label class="upload sm"><input type="file" accept="image/*" hidden data-imgfor="${key}" data-block="${i}"><span>Replace</span></label>
    </div></div>`;
}

function drawBlocks() {
  const host = $("#blocks");
  host.innerHTML = "";
  (currentPage.body || []).forEach((b, i) => {
    const c = el("div", "block");
    c.dataset.i = i;
    c.draggable = true;
    c.innerHTML = `<div class="block-head">
        <span class="bgrip" title="Drag to reorder">⠿</span>
        <span class="btype">${b.type === "html" ? "text" : b.type}</span>
        <button class="brm" title="Remove block">×</button>
      </div>
      <div class="block-body">${blockFields(b, i)}</div>`;
    c.querySelector(".brm").addEventListener("click", () => {
      if (!confirm("Remove this block?")) return;
      currentPage.body.splice(i, 1); drawBlocks();
    });
    c.querySelectorAll("[data-k]").forEach(inp =>
      inp.addEventListener("input", () => setBlockValue(i, inp.dataset.k, inp.value)));
    c.querySelectorAll("[data-imgfor]").forEach(inp =>
      inp.addEventListener("change", ev => uploadBlockImage(ev, i, inp.dataset.imgfor)));
    wireBlockDrag(c);
    host.appendChild(c);
  });
  if (!(currentPage.body || []).length)
    host.innerHTML = '<div class="empty">No blocks yet — add one below.</div>';
}

function setBlockValue(i, key, val) {
  const b = currentPage.body[i];
  if (key.includes(".")) {
    const [arr, idx, field] = key.split(".");
    b[arr][+idx][field] = val;
  } else b[key] = val;
}

let dragBlock = null;
function wireBlockDrag(c) {
  c.addEventListener("dragstart", e => {
    if (!e.target.closest(".bgrip") && e.target !== c) { e.preventDefault(); return; }
    dragBlock = c; c.classList.add("dragging");
  });
  c.addEventListener("dragend", () => { c.classList.remove("dragging"); dragBlock = null;
    document.querySelectorAll(".block").forEach(x => x.classList.remove("drop-target")); });
  c.addEventListener("dragover", e => { e.preventDefault(); if (dragBlock && dragBlock !== c) c.classList.add("drop-target"); });
  c.addEventListener("dragleave", () => c.classList.remove("drop-target"));
  c.addEventListener("drop", e => {
    e.preventDefault(); c.classList.remove("drop-target");
    if (!dragBlock || dragBlock === c) return;
    const from = +dragBlock.dataset.i, to = +c.dataset.i;
    const [m] = currentPage.body.splice(from, 1);
    currentPage.body.splice(to, 0, m);
    drawBlocks();
  });
}

document.querySelectorAll(".add").forEach(btn => btn.addEventListener("click", () => {
  const t = btn.dataset.add;
  const blank = { h3:{type:"h3",text:""}, lead:{type:"lead",text:""}, p:{type:"p",text:""},
                  caption:{type:"caption",text:""}, img:{type:"img",src:"",alt:""},
                  twoup:{type:"twoup",src1:"",alt1:"",src2:"",alt2:""} }[t];
  currentPage.body = currentPage.body || [];
  currentPage.body.push(JSON.parse(JSON.stringify(blank)));
  drawBlocks();
  $("#blocks").lastElementChild?.scrollIntoView({ block: "center", behavior: "smooth" });
}));

async function uploadBlockImage(ev, i, key) {
  const f = ev.target.files[0]; if (!f) return;
  const url = await uploadToStorage(f, "pages/" + currentPage.key);
  if (!url) return;
  setBlockValue(i, key, url);
  drawBlocks();
  toast("Image added — remember to save");
}

$("#pageSave").addEventListener("click", async () => {
  const btn = $("#pageSave"); btn.disabled = true; btn.textContent = "Saving…";
  const { error } = await sb.from("store_pages")
    .update({ title: $("#pg_title").value.trim(), body: currentPage.body || [] })
    .eq("key", currentPage.key);
  btn.disabled = false; btn.textContent = "Save page";
  if (error) return toast(error.message, true);
  currentPage.title = $("#pg_title").value.trim();
  $("#pageSavedAt").textContent = "Last saved just now";
  toast("Page saved");
});

/* ================= homepage ================= */
let settings = {};
async function loadHome() {
  const { data, error } = await sb.from("store_settings").select("*");
  if (error) return toast(error.message, true);
  settings = Object.fromEntries((data || []).map(s => [s.key, s.value]));
  $("#hp_tagline").value = settings.tagline || "";
  drawHero();
}
function drawHero() {
  const src = settings.hero_image || "";
  $("#heroPreview").innerHTML = src
    ? `<img src="${publicUrl(src)}" alt="">`
    : '<div class="bimg-none">none</div>';
}
$("#heroFile").addEventListener("change", async ev => {
  const f = ev.target.files[0]; if (!f) return;
  const url = await uploadToStorage(f, "home");
  if (!url) return;
  settings.hero_image = url;
  drawHero();
  toast("Hero updated — remember to save");
});
$("#homeSave").addEventListener("click", async () => {
  const btn = $("#homeSave"); btn.disabled = true; btn.textContent = "Saving…";
  const rows = [
    { key: "tagline", value: $("#hp_tagline").value.trim() },
    { key: "hero_image", value: settings.hero_image || "assets/hero.png" },
  ];
  let err = null;
  for (const r of rows) {
    const { error } = await sb.from("store_settings")
      .upsert({ key: r.key, value: r.value }, { onConflict: "key" });
    if (error) err = error;
  }
  btn.disabled = false; btn.textContent = "Save homepage";
  if (err) return toast(err.message, true);
  $("#homeSavedAt").textContent = "Last saved just now";
  toast("Homepage saved");
});

/* shared uploader */
async function uploadToStorage(file, folder) {
  const ext = (file.name.split(".").pop() || "jpg").toLowerCase();
  const path = `${folder}/${Date.now()}-${Math.random().toString(36).slice(2,8)}.${ext}`;
  const { error } = await sb.storage.from("store-media")
    .upload(path, file, { cacheControl: "31536000", upsert: false });
  if (error) { toast(error.message, true); return null; }
  return sb.storage.from("store-media").getPublicUrl(path).data.publicUrl;
}
