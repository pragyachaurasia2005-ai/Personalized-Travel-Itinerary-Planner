-- Personalized Travel Itinerary Planner: Supabase SQL Schema
-- Run this in your Supabase Project -> SQL Editor to initialize the database

CREATE TABLE IF NOT EXISTS public.trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    destination TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    duration_days INTEGER NOT NULL,
    traveler_type TEXT NOT NULL,
    group_size INTEGER DEFAULT 1,
    budget_tier TEXT NOT NULL,
    currency TEXT DEFAULT 'USD',
    currency_symbol TEXT DEFAULT '$',
    total_estimated_cost_usd NUMERIC(12, 2) DEFAULT 0.00,
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    cost_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb,
    days JSONB NOT NULL DEFAULT '[]'::jsonb,
    packing_checklist JSONB NOT NULL DEFAULT '[]'::jsonb,
    local_etiquette_tips JSONB NOT NULL DEFAULT '[]'::jsonb,
    ai_rationale TEXT DEFAULT '',
    generation_source TEXT DEFAULT 'local_fallback',
    generation_model TEXT DEFAULT 'Adaptive Knowledge Engine',
    is_saved BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Indices for rapid querying & filtering
CREATE INDEX IF NOT EXISTS idx_trips_destination ON public.trips (destination);
CREATE INDEX IF NOT EXISTS idx_trips_traveler_type ON public.trips (traveler_type);
CREATE INDEX IF NOT EXISTS idx_trips_created_at ON public.trips (created_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE public.trips ENABLE ROW LEVEL SECURITY;

-- Allow public read and write for demonstration (can be restricted to auth.uid() in production)
CREATE POLICY "Public trips are selectable" 
ON public.trips FOR SELECT 
USING (true);

CREATE POLICY "Public trips can be inserted" 
ON public.trips FOR INSERT 
WITH CHECK (true);

CREATE POLICY "Public trips can be updated" 
ON public.trips FOR UPDATE 
USING (true);

CREATE POLICY "Public trips can be deleted" 
ON public.trips FOR DELETE 
USING (true);
