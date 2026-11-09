-- Run once in the Supabase SQL editor. Server-side service_role key only.
-- Custom application auth is enforced by db.py; deny direct browser database access.
create table if not exists public.users (
 id uuid primary key, email text unique not null, password text not null,
 name text not null, role text not null check (role in ('student','teacher')),
 created_at timestamptz not null default now()
);
create table if not exists public.subjects (
 id uuid primary key, owner_id uuid not null references public.users(id),
 name text not null, code text unique not null,
 created_at timestamptz not null default now()
);
create table if not exists public.students (
 id uuid primary key, email text unique not null, name text not null,
 user_id uuid unique references public.users(id), created_at timestamptz not null default now()
);
create table if not exists public.enrollments (
 id uuid primary key, subject_id uuid not null references public.subjects(id),
 student_id uuid not null references public.students(id),
 created_at timestamptz not null default now(), unique(subject_id,student_id)
);
create table if not exists public.photos (
 id uuid primary key, student_id uuid not null references public.students(id),
 path text not null, embedding text not null, created_at timestamptz not null default now()
);
create table if not exists public.attendance (
 id uuid primary key, subject_id uuid not null references public.subjects(id),
 student_id uuid not null references public.students(id), date date not null,
 present boolean not null, source text not null check(source in ('face','voice','manual')),
 overridden boolean not null default false, created_at timestamptz not null default now(),
 unique(subject_id,student_id,date)
);
create index if not exists attendance_subject_date on public.attendance(subject_id,date);
create index if not exists enrollment_student on public.enrollments(student_id);
create index if not exists photo_student on public.photos(student_id);
alter table public.users enable row level security;
alter table public.subjects enable row level security;
alter table public.students enable row level security;
alter table public.enrollments enable row level security;
alter table public.photos enable row level security;
alter table public.attendance enable row level security;
revoke all on public.users, public.subjects, public.students, public.enrollments,
 public.photos, public.attendance from anon, authenticated;
grant all on public.users, public.subjects, public.students, public.enrollments,
 public.photos, public.attendance to service_role;
insert into storage.buckets (id,name,public,file_size_limit,allowed_mime_types)
values ('face-photos','face-photos',false,10485760,array['image/jpeg'])
on conflict (id) do nothing;
-- Private bucket: only the server service role may read/write face photos.
drop policy if exists "TeachUs server photos" on storage.objects;
create policy "TeachUs server photos" on storage.objects for all to service_role
using (bucket_id='face-photos') with check (bucket_id='face-photos');
