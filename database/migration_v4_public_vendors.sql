-- Add is_public column to vendors table
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE;

-- Create index for faster querying
CREATE INDEX IF NOT EXISTS idx_vendors_is_public ON vendors(is_public);
