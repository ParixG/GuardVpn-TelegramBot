create extension if not exists "uuid-ossp";

create table public.users (
    telegram_id   bigint primary key,
    username      text,
    first_name    text not null,
    wallet_balance numeric(12,2) not null default 0,
    created_at    timestamptz not null default now()
);

create table public.plans (
    id              serial primary key,
    name            text not null,
    data_limit_gb   numeric(8,2) not null,
    duration_days   integer not null,
    price_toman     integer not null,
    guard_service_ids jsonb not null default '[]'
);

create table public.subscriptions (
    id               uuid primary key default uuid_generate_v4(),
    user_telegram_id bigint not null references public.users(telegram_id) on delete cascade,
    guard_username   text not null unique,
    plan_id          integer not null references public.plans(id),
    created_at       timestamptz not null default now()
);

create table public.transactions (
    id               uuid primary key default uuid_generate_v4(),
    user_telegram_id bigint not null references public.users(telegram_id) on delete cascade,
    amount           numeric(12,2) not null,
    type             text not null check (type in ('deposit','purchase')),
    note             text,
    created_at       timestamptz not null default now()
);
S
-- Atomic wallet operations (avoids race conditions)
create or replace function deduct_wallet(p_tid bigint, p_amount numeric)
returns boolean language plpgsql as $$
begin
  update public.users set wallet_balance = wallet_balance - p_amount
  where telegram_id = p_tid and wallet_balance >= p_amount;
  return found;
end;
$$;

create or replace function add_wallet(p_tid bigint, p_amount numeric)
returns void language plpgsql as $$
begin
  update public.users set wallet_balance = wallet_balance + p_amount
  where telegram_id = p_tid;
end;
$$;

-- Card-to-card top-up requests (receipt upload + admin approval workflow)
create table public.topup_requests (
    id               uuid primary key default uuid_generate_v4(),
    user_telegram_id bigint not null references public.users(telegram_id) on delete cascade,
    amount           numeric(12,2) not null check (amount > 0),
    receipt_file_id  text not null,            -- user-bot-scoped file_id (audit/reference)
    status           text not null default 'pending'
                     check (status in ('pending','approved','rejected')),
    decided_by       bigint,                   -- admin telegram_id
    decided_at       timestamptz,
    admin_messages   jsonb not null default '[]',  -- [{"chat_id":..,"message_id":..}]
    created_at       timestamptz not null default now()
);

-- Atomic decide: CAS on status + wallet credit + ledger insert in ONE transaction.
-- Returns the request row if this call won the race, else nothing.
create or replace function decide_topup(p_request_id uuid, p_admin_id bigint, p_approve boolean)
returns setof public.topup_requests language plpgsql as $$
declare r public.topup_requests;
begin
  update public.topup_requests
     set status = case when p_approve then 'approved' else 'rejected' end,
         decided_by = p_admin_id,
         decided_at = now()
   where id = p_request_id and status = 'pending'
   returning * into r;
  if not found then return; end if;
  if p_approve then
    update public.users set wallet_balance = wallet_balance + r.amount
     where telegram_id = r.user_telegram_id;
    insert into public.transactions (user_telegram_id, amount, type, note)
    values (r.user_telegram_id, r.amount, 'deposit', 'topup:' || r.id::text);
  end if;
  return next r;
end;
$$;

-- Seed plans (adjust guard_service_ids to real service IDs from your Guard panel)
insert into public.plans (name, data_limit_gb, duration_days, price_toman, guard_service_ids) values
    ('برنزی - ۲۰ گیگ / ۳۰ روز',   20,  30,  80000, '[1,3]'),
    ('نقره‌ای - ۵۰ گیگ / ۳۰ روز',  50,  30, 150000, '[1,3]'),
    ('طلایی - ۱۰۰ گیگ / ۳۰ روز',  100, 30, 250000, '[1,3]');
