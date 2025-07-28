-- SQL script to create a mapping for survey- room pattern
-- Run this in your Supabase SQL editor

-- First, let's see what campaigns are available
SELECT id, name, description FROM campaign ORDER BY id;

-- Then create the mapping (replace X with the campaign ID you want to use)
-- Example: If you want to map to campaign ID 1, uncomment and run this:

/*
INSERT INTO campaign_room_mapping (campaign_id, room_pattern, is_active)
VALUES (1, 'survey-', true)
ON CONFLICT (room_pattern) DO UPDATE SET
    campaign_id = EXCLUDED.campaign_id,
    is_active = EXCLUDED.is_active;
*/

-- To verify the mapping was created:
-- SELECT * FROM campaign_room_mapping WHERE room_pattern = 'survey-';

-- To see all mappings:
-- SELECT 
--     crm.id,
--     crm.room_pattern,
--     crm.is_active,
--     c.name as campaign_name,
--     c.id as campaign_id
-- FROM campaign_room_mapping crm
-- JOIN campaign c ON crm.campaign_id = c.id
-- ORDER BY crm.room_pattern; 