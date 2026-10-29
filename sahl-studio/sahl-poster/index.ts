// Sahl Digital Auto Poster: posts one approved post a day to the Sahl Digital Facebook Page
// (and Instagram once linked), then adds the WhatsApp link as the first comment.
// Called hourly by pg_cron (job 'sahl-poster-hourly') with header x-cron-key; posts only
// from settings.post_hour (local time, settings.tz). A 'pending' post counts as approved
// once its approve_by time has passed (the weekly "no answer = approved" rule).
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const V = "v26.0";
const GRAPH = `https://graph.facebook.com/${V}`;
const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data, null, 2), { status, headers: { "Content-Type": "application/json" } });

async function graph(path: string, token: string, init: { method?: string; params?: Record<string, string> } = {}) {
  const method = init.method ?? "GET";
  const body = new URLSearchParams(init.params ?? {});
  const url = method === "GET" ? `${GRAPH}/${path}${body.toString() ? "?" + body : ""}` : `${GRAPH}/${path}`;
  const res = await fetch(url, {
    method,
    headers: { Authorization: `Bearer ${token}`, ...(method === "GET" ? {} : { "Content-Type": "application/x-www-form-urlencoded" }) },
    body: method === "GET" ? undefined : body,
  });
  const data = await res.json();
  if (!res.ok || data.error) throw new Error(`Graph ${method} ${path}: ${JSON.stringify(data.error ?? data)}`);
  return data;
}

async function settings() {
  const { data, error } = await sb.from("sahl_settings").select("*").eq("id", 1).single();
  if (error) throw error;
  return data;
}

// Finds the Sahl Page among the pages the long-lived user token (secret META_USER_TOKEN) can manage,
// stores its id and a non-expiring Page token.
async function pageToken(s: any): Promise<{ token: string; pageId: string; igId: string | null }> {
  if (s.page_token && s.page_id) return { token: s.page_token, pageId: s.page_id, igId: s.ig_user_id };
  const userToken = Deno.env.get("META_USER_TOKEN");
  if (!userToken) throw new Error("META_USER_TOKEN secret is not set");
  const acc = await graph("me/accounts", userToken, { params: { fields: "id,name,access_token,instagram_business_account", limit: "100" } });
  const pages = acc.data ?? [];
  const page = s.page_id ? pages.find((p: any) => p.id === s.page_id) : pages.find((p: any) => /sahl|سهل/i.test(p.name));
  if (!page) throw new Error(`Sahl Page not found in /me/accounts (pages visible: ${pages.map((p: any) => p.name).join(", ") || "none"})`);
  const igId = page.instagram_business_account?.id ?? s.ig_user_id ?? null;
  await sb.from("sahl_settings").update({ page_id: page.id, page_token: page.access_token, ig_user_id: igId, updated_at: new Date().toISOString() }).eq("id", 1);
  return { token: page.access_token, pageId: page.id, igId };
}

function localNow(tz: string) {
  const parts = new Intl.DateTimeFormat("en-CA", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", hourCycle: "h23" })
    .formatToParts(new Date());
  const get = (t: string) => parts.find((p) => p.type === t)!.value;
  return { date: `${get("year")}-${get("month")}-${get("day")}`, hour: Number(get("hour")) };
}

async function postReel(pageId: string, token: string, p: any): Promise<string> {
  try {
    const start = await graph(`${pageId}/video_reels`, token, { method: "POST", params: { upload_phase: "start" } });
    const up = await fetch(`https://rupload.facebook.com/video-upload/${V}/${start.video_id}`, {
      method: "POST",
      headers: { Authorization: `OAuth ${token}`, file_url: p.media_urls[0] },
    });
    const upj = await up.json();
    if (!up.ok || upj.error) throw new Error(`upload: ${JSON.stringify(upj)}`);
    await graph(`${pageId}/video_reels`, token, { method: "POST", params: { upload_phase: "finish", video_id: start.video_id, video_state: "PUBLISHED", description: p.caption } });
    return start.video_id;
  } catch (e) {
    // Fallback: a normal Page video (Facebook still shows short vertical videos as Reels)
    const r = await graph(`${pageId}/videos`, token, { method: "POST", params: { file_url: p.media_urls[0], description: p.caption } });
    console.log("reels API failed, posted as video:", String(e));
    return r.id;
  }
}

async function postToFacebook(pageId: string, token: string, p: any): Promise<string> {
  if (p.kind === "video") return await postReel(pageId, token, p);
  if (p.kind === "carousel") {
    const ids: string[] = [];
    for (const url of p.media_urls) {
      const ph = await graph(`${pageId}/photos`, token, { method: "POST", params: { url, published: "false" } });
      ids.push(ph.id);
    }
    const params: Record<string, string> = { message: p.caption };
    ids.forEach((id, i) => (params[`attached_media[${i}]`] = JSON.stringify({ media_fbid: id })));
    const r = await graph(`${pageId}/feed`, token, { method: "POST", params });
    return r.id;
  }
  if (p.kind === "image") {
    const r = await graph(`${pageId}/photos`, token, { method: "POST", params: { url: p.media_urls[0], message: p.caption } });
    return r.post_id ?? r.id;
  }
  const r = await graph(`${pageId}/feed`, token, { method: "POST", params: { message: p.caption } });
  return r.id;
}

async function waitIg(token: string, id: string) {
  for (let i = 0; i < 30; i++) {
    const st = await graph(id, token, { params: { fields: "status_code" } });
    if (st.status_code === "FINISHED") return;
    if (st.status_code === "ERROR") throw new Error("Instagram container failed");
    await new Promise((r) => setTimeout(r, 4000));
  }
}

async function postToInstagram(igId: string | null, token: string, p: any): Promise<string | null> {
  if (!igId || !p.media_urls?.length) return null;
  let creation: string;
  if (p.kind === "carousel") {
    const kids: string[] = [];
    for (const url of p.media_urls) {
      const c = await graph(`${igId}/media`, token, { method: "POST", params: { image_url: url, is_carousel_item: "true" } });
      kids.push(c.id);
    }
    const c = await graph(`${igId}/media`, token, { method: "POST", params: { media_type: "CAROUSEL", children: kids.join(","), caption: p.caption } });
    creation = c.id;
  } else if (p.kind === "video") {
    const c = await graph(`${igId}/media`, token, { method: "POST", params: { media_type: "REELS", video_url: p.media_urls[0], caption: p.caption } });
    creation = c.id;
  } else {
    const c = await graph(`${igId}/media`, token, { method: "POST", params: { image_url: p.media_urls[0], caption: p.caption } });
    creation = c.id;
  }
  await waitIg(token, creation);
  const pub = await graph(`${igId}/media_publish`, token, { method: "POST", params: { creation_id: creation } });
  return pub.id;
}

async function firstComment(objectId: string, token: string, text: string | null) {
  if (!text) return null;
  try { await graph(`${objectId}/comments`, token, { method: "POST", params: { message: text } }); return null; }
  catch (e) { return String(e); }
}

async function run(code?: string) {
  const s = await settings();
  const now = localNow(s.tz);
  if (!code) {
    if (s.paused) return { posted: false, reason: "paused" };
    if (now.hour < s.post_hour) return { posted: false, reason: `before ${s.post_hour}:00 local (${now.hour}:00)` };
    const { count } = await sb.from("sahl_posts").select("id", { count: "exact", head: true })
      .eq("status", "posted").gte("posted_at", new Date(Date.now() - 20 * 3600 * 1000).toISOString());
    if ((count ?? 0) > 0) return { posted: false, reason: "already posted in the last 20 hours" };
  }
  let q = sb.from("sahl_posts").select("*");
  if (code) q = q.eq("code", code);
  else q = q.lte("post_date", now.date).or(`status.eq.approved,and(status.eq.pending,approve_by.lt.${new Date().toISOString()})`).order("post_date", { ascending: true });
  const { data: rows, error } = await q.limit(1);
  if (error) throw error;
  const p = rows?.[0];
  if (!p) return { posted: false, reason: `nothing approved for ${now.date}` };
  if (["posted", "posting", "rejected"].includes(p.status)) return { posted: false, reason: `${p.code} is ${p.status}` };

  const { token, pageId, igId } = await pageToken(s);
  await sb.from("sahl_posts").update({ status: "posting", approved_at: p.approved_at ?? new Date().toISOString() }).eq("id", p.id);
  let fbId: string;
  try {
    fbId = await postToFacebook(pageId, token, p);
  } catch (e) {
    await sb.from("sahl_posts").update({ status: "failed", error: String(e) }).eq("id", p.id);
    return { posted: false, code: p.code, error: String(e) };
  }
  const errors: string[] = [];
  const c1 = await firstComment(fbId, token, p.first_comment); if (c1) errors.push("fb comment: " + c1);
  let igMedia: string | null = null;
  try { igMedia = await postToInstagram(igId, token, p); } catch (e) { errors.push("ig: " + String(e)); }
  if (igMedia) { const c2 = await firstComment(igMedia, token, p.first_comment); if (c2) errors.push("ig comment: " + c2); }
  await sb.from("sahl_posts").update({ status: "posted", fb_post_id: fbId, ig_media_id: igMedia, error: errors.join(" | ") || null, posted_at: new Date().toISOString() }).eq("id", p.id);
  return { posted: true, code: p.code, fb_post_id: fbId, ig_media_id: igMedia, warnings: errors };
}

// Pulls simple public numbers for posted posts (comments, shares, reach where available).
async function insights() {
  const s = await settings();
  const { token } = await pageToken(s);
  const { data: rows } = await sb.from("sahl_posts").select("id,code,fb_post_id,kind").eq("status", "posted").not("fb_post_id", "is", null);
  const out: any[] = [];
  for (const r of rows ?? []) {
    const upd: Record<string, unknown> = {};
    try {
      const f = await graph(r.fb_post_id, token, { params: { fields: r.kind === "video" ? "comments.summary(true)" : "shares,comments.summary(true)" } });
      if (f.shares?.count != null) upd.shares = f.shares.count;
    } catch (_) { /* metric not available for this object */ }
    try {
      const m = await graph(`${r.fb_post_id}/insights`, token, { params: { metric: r.kind === "video" ? "post_video_views" : "post_impressions_unique" } });
      const v = m.data?.[0]?.values?.[0]?.value; if (typeof v === "number") upd.reach = v;
    } catch (_) { /* insights need more page history */ }
    if (Object.keys(upd).length) await sb.from("sahl_posts").update(upd).eq("id", r.id);
    out.push({ code: r.code, ...upd });
  }
  return out;
}

// One-time Page setup: profile picture, cover and About text from public image URLs.
async function setupPage(body: any) {
  const s = await settings();
  const { token, pageId } = await pageToken(s);
  const done: Record<string, unknown> = {};
  if (body.picture_url) { try { await graph(`${pageId}/picture`, token, { method: "POST", params: { picture: body.picture_url } }); done.picture = "ok"; } catch (e) { done.picture = String(e); } }
  if (body.cover_url) {
    try {
      const ph = await graph(`${pageId}/photos`, token, { method: "POST", params: { url: body.cover_url, published: "false" } });
      await graph(pageId, token, { method: "POST", params: { cover: ph.id } });
      done.cover = "ok";
    } catch (e) { done.cover = String(e); }
  }
  const fields: Record<string, string> = {};
  for (const k of ["about", "description", "website", "phone", "emails"]) if (body[k]) fields[k] = body[k];
  if (Object.keys(fields).length) { try { await graph(pageId, token, { method: "POST", params: fields }); done.fields = "ok"; } catch (e) { done.fields = String(e); } }
  return done;
}

async function status() {
  const s = await settings();
  try {
    const { token, pageId, igId } = await pageToken(s);
    const page = await graph(pageId, token, { params: { fields: "id,name,link,followers_count,fan_count" } });
    return { page, ig_user_id: igId, local: localNow(s.tz), post_hour: s.post_hour, paused: s.paused };
  } catch (e) {
    return { connected: false, error: String(e), local: localNow(s.tz) };
  }
}

Deno.serve(async (req) => {
  const url = new URL(req.url);
  const s = await settings();
  if (req.headers.get("x-cron-key") !== s.cron_key) return json({ error: "unauthorized" }, 401);
  try {
    if (url.pathname.endsWith("/cron")) return json(await run());
    if (url.pathname.endsWith("/post-now")) return json(await run(url.searchParams.get("code") ?? undefined));
    if (url.pathname.endsWith("/insights")) return json(await insights());
    if (url.pathname.endsWith("/setup-page")) return json(await setupPage(await req.json()));
    if (url.pathname.endsWith("/refresh-token")) {
      await sb.from("sahl_settings").update({ page_token: null }).eq("id", 1);
      return json(await status());
    }
    return json(await status());
  } catch (e) {
    return json({ error: String(e) }, 500);
  }
});
