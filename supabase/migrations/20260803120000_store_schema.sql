-- Studio Maçon — store content schema ("Maçon Studio" editor)
-- Runs in the SAME Supabase project as macon-archive (berdrzxjoejirbhdgjer).
-- Tables are prefixed `store_` to stay clearly separate from the CRM
-- (collectors / bureau_todos / messages).
--
-- Run once: Supabase → SQL Editor → New query → Run.

-- ---------- enums ----------
do $$ begin
  create type store_collection as enum ('perennial','ephemeral');
exception when duplicate_object then null; end $$;

do $$ begin
  -- draft: not built | scheduled: appears at release_at | live: for sale
  -- sold_out: shown, not buyable | archived: shown in the archive, permanently claimed
  create type store_status as enum ('draft','scheduled','live','sold_out','archived');
exception when duplicate_object then null; end $$;

-- ---------- products ----------
create table if not exists public.store_products (
  id              uuid primary key default gen_random_uuid(),
  slug            text unique not null,
  name            text not null,
  price           numeric(10,2),
  description     text,
  notes           text[] default '{}',          -- e.g. {"Solid bronze; Ombré patina","29 x 27 x 17 mm"}
  collection      store_collection not null default 'perennial',
  status          store_status     not null default 'live',
  release_at      timestamptz,                  -- drop time; null = immediate
  quantity        integer,                      -- null = made to order (unlimited); 1 = one of one
  stripe_price_id text,
  sort_order      integer not null default 0,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index if not exists store_products_sort_idx on public.store_products (collection, sort_order);
create index if not exists store_products_status_idx on public.store_products (status);

-- ---------- product images ----------
-- `url` holds either a repo-relative path (migrated content, e.g. images/products/pip-1.jpg)
-- or a full Supabase Storage URL (anything Hannah uploads via the editor).
create table if not exists public.store_product_images (
  id          uuid primary key default gen_random_uuid(),
  product_id  uuid not null references public.store_products(id) on delete cascade,
  url         text not null,
  alt         text,
  sort_order  integer not null default 0,
  created_at  timestamptz not null default now()
);
create index if not exists store_product_images_product_idx
  on public.store_product_images (product_id, sort_order);

-- ---------- editable pages ----------
create table if not exists public.store_pages (
  key        text primary key,                  -- story | custom | shipping | contact
  title      text,
  body       jsonb not null default '[]'::jsonb, -- ordered blocks: {type, text|src|alt, ...}
  updated_at timestamptz not null default now()
);

-- ---------- site settings (hero art, tagline, ...) ----------
create table if not exists public.store_settings (
  key        text primary key,
  value      jsonb,
  updated_at timestamptz not null default now()
);

-- ---------- updated_at triggers ----------
create or replace function public.store_touch_updated_at()
returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end $$;

drop trigger if exists store_products_touch on public.store_products;
create trigger store_products_touch before update on public.store_products
  for each row execute function public.store_touch_updated_at();

drop trigger if exists store_pages_touch on public.store_pages;
create trigger store_pages_touch before update on public.store_pages
  for each row execute function public.store_touch_updated_at();

drop trigger if exists store_settings_touch on public.store_settings;
create trigger store_settings_touch before update on public.store_settings
  for each row execute function public.store_touch_updated_at();

-- ---------- row level security ----------
-- Public (anon) may READ published content — the live sold-out badge depends on this.
-- Only the two keepers may write.
alter table public.store_products       enable row level security;
alter table public.store_product_images enable row level security;
alter table public.store_pages          enable row level security;
alter table public.store_settings       enable row level security;

drop policy if exists "public reads published products" on public.store_products;
create policy "public reads published products" on public.store_products
  for select to anon, authenticated
  using ( status in ('live','sold_out','archived') );

drop policy if exists "keepers write products" on public.store_products;
create policy "keepers write products" on public.store_products
  for all to authenticated
  using      ( auth.jwt() ->> 'email' in ('alex@studiomacon.co','hannah@studiomacon.co') )
  with check ( auth.jwt() ->> 'email' in ('alex@studiomacon.co','hannah@studiomacon.co') );

drop policy if exists "public reads product images" on public.store_product_images;
create policy "public reads product images" on public.store_product_images
  for select to anon, authenticated using ( true );

drop policy if exists "keepers write product images" on public.store_product_images;
create policy "keepers write product images" on public.store_product_images
  for all to authenticated
  using      ( auth.jwt() ->> 'email' in ('alex@studiomacon.co','hannah@studiomacon.co') )
  with check ( auth.jwt() ->> 'email' in ('alex@studiomacon.co','hannah@studiomacon.co') );

drop policy if exists "public reads pages" on public.store_pages;
create policy "public reads pages" on public.store_pages
  for select to anon, authenticated using ( true );

drop policy if exists "keepers write pages" on public.store_pages;
create policy "keepers write pages" on public.store_pages
  for all to authenticated
  using      ( auth.jwt() ->> 'email' in ('alex@studiomacon.co','hannah@studiomacon.co') )
  with check ( auth.jwt() ->> 'email' in ('alex@studiomacon.co','hannah@studiomacon.co') );

drop policy if exists "public reads settings" on public.store_settings;
create policy "public reads settings" on public.store_settings
  for select to anon, authenticated using ( true );

drop policy if exists "keepers write settings" on public.store_settings;
create policy "keepers write settings" on public.store_settings
  for all to authenticated
  using      ( auth.jwt() ->> 'email' in ('alex@studiomacon.co','hannah@studiomacon.co') )
  with check ( auth.jwt() ->> 'email' in ('alex@studiomacon.co','hannah@studiomacon.co') );

-- ---------- storage bucket for uploads ----------
insert into storage.buckets (id, name, public)
values ('store-media','store-media', true)
on conflict (id) do nothing;

drop policy if exists "public reads store media" on storage.objects;
create policy "public reads store media" on storage.objects
  for select to anon, authenticated using ( bucket_id = 'store-media' );

drop policy if exists "keepers write store media" on storage.objects;
create policy "keepers write store media" on storage.objects
  for all to authenticated
  using      ( bucket_id = 'store-media' and auth.jwt() ->> 'email' in ('alex@studiomacon.co','hannah@studiomacon.co') )
  with check ( bucket_id = 'store-media' and auth.jwt() ->> 'email' in ('alex@studiomacon.co','hannah@studiomacon.co') );
