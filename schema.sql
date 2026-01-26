-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- 1. Users Table (extends Supabase Auth)
-- This table stores additional user profile info not in auth.users
create table public.users (
  id uuid references auth.users not null primary key,
  email text not null,
  name text,
  role text default 'user',
  is_active boolean default true,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS)
alter table public.users enable row level security;

-- Policies for Users
create policy "Users can view their own profile" on public.users
  for select using (auth.uid() = id);

create policy "Users can update their own profile" on public.users
  for update using (auth.uid() = id);

-- 2. Vendors Table
create table public.vendors (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.users(id) not null,
  
  -- Basic Info
  vendor_type text not null,
  vendor_type_other text,
  business_name text not null,
  legal_name text,
  contact_person text not null,
  email text not null,
  phone_number text not null,
  
  -- Areas
  operating_areas text[] default '{}',
  operating_areas_other text,
  
  -- Business Details
  business_reg_number text,
  business_address text not null,
  tax_id text,
  
  -- Bank Details
  bank_name text not null,
  bank_name_other text,
  account_holder_name text not null,
  account_number text not null,
  bank_branch text not null,
  
  -- Agreements
  accept_terms boolean default false,
  accept_commission boolean default false,
  accept_cancellation boolean default false,
  grant_rights boolean default false,
  confirm_accuracy boolean default false,
  marketing_permission boolean default false,
  
  -- File URLs
  reg_certificate_url text,
  nic_passport_url text,
  tourism_license_url text,
  logo_url text,
  cover_image_url text,
  gallery_urls text[] default '{}',
  
  -- Status
  status text default 'pending', -- pending, approved, rejected, suspended
  status_reason text,
  
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS
alter table public.vendors enable row level security;

-- Policies for Vendors
create policy "Vendors can view their own profile" on public.vendors
  for select using (auth.uid() = user_id);

create policy "Admins can view all vendors" on public.vendors
  for select using (
    exists (select 1 from public.users where id = auth.uid() and role = 'admin')
  );

-- 3. Vendor Services Table
create table public.vendor_services (
  id uuid default uuid_generate_v4() primary key,
  vendor_id uuid references public.vendors(id) not null,
  
  service_name text not null,
  service_category text not null,
  short_description text,
  
  whats_included text,
  whats_not_included text,
  
  duration_value integer,
  duration_unit text,
  
  languages_offered text[] default '{}',
  
  group_size_min integer,
  group_size_max integer,
  
  daily_capacity integer,
  
  operating_days text[] default '{}',
  locations_covered text[] default '{}',
  
  retail_price decimal(10, 2) not null,
  currency text default 'LKR',
  
  not_suitable_for text,
  important_info text,
  cancellation_policy text,
  accessibility_info text,
  
  image_urls text[] default '{}',
  
  is_active boolean default true,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS
alter table public.vendor_services enable row level security;

-- Policies for Services
create policy "Vendors can manage their services" on public.vendor_services
  for all using (
    exists (select 1 from public.vendors where id = vendor_id and user_id = auth.uid())
  );

create policy "Public can view active services" on public.vendor_services
  for select using (is_active = true);

-- Storage Buckets Setup (Run in SQL Editor or Storage UI)
-- insert into storage.buckets (id, name) values ('vendor-files', 'vendor-files');
-- create policy "Authenticated users can upload" on storage.objects for insert with check (auth.role() = 'authenticated');
-- create policy "Public can view" on storage.objects for select using (bucket_id = 'vendor-files');
