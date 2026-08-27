/*
  # Add user associations to planner tables

  1. New Columns
    - `user_id` (uuid) column added to `travel_plans`, `travel_guides`, and `hotel_searches` referencing `auth.users(id)`
  
  2. Security
    - Drop general "Allow public access" policies
    - Add policies for:
      - Public SELECT access (everyone can view plans/guides/searches)
      - Authenticated INSERT with matching `user_id`
      - Guest INSERT with null `user_id`
      - Authenticated management (UPDATE/DELETE) matching their own `user_id`
*/

-- Add user_id column to tables if not exists
ALTER TABLE travel_plans ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE travel_guides ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE hotel_searches ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE;

-- Drop existing public access policies
DROP POLICY IF EXISTS "Allow public access" ON travel_plans;
DROP POLICY IF EXISTS "Allow public access" ON travel_guides;
DROP POLICY IF EXISTS "Allow public access" ON hotel_searches;

-- Create policies for travel_plans
CREATE POLICY "Allow public read access" ON travel_plans
  FOR SELECT TO public USING (true);

CREATE POLICY "Allow authenticated users to create plans" ON travel_plans
  FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Allow guests to create plans" ON travel_plans
  FOR INSERT TO public WITH CHECK (user_id IS NULL);

CREATE POLICY "Allow users to update/delete their own plans" ON travel_plans
  FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Create policies for travel_guides
CREATE POLICY "Allow public read access" ON travel_guides
  FOR SELECT TO public USING (true);

CREATE POLICY "Allow authenticated users to create/manage their own guides" ON travel_guides
  FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Allow guests to create guides" ON travel_guides
  FOR INSERT TO public WITH CHECK (user_id IS NULL);

-- Create policies for hotel_searches
CREATE POLICY "Allow public read access" ON hotel_searches
  FOR SELECT TO public USING (true);

CREATE POLICY "Allow authenticated users to create/manage their own searches" ON hotel_searches
  FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Allow guests to create searches" ON hotel_searches
  FOR INSERT TO public WITH CHECK (user_id IS NULL);
