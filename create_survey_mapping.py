#!/usr/bin/env python3
"""
Quick script to create a mapping for survey- room pattern.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set in environment variables or .env file")
    exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def list_campaigns():
    """List all available campaigns."""
    try:
        result = supabase.table("campaign").select("*").order("id").execute()
        
        if result.data:
            print("\n=== Available Campaigns ===")
            for campaign in result.data:
                print(f"ID: {campaign['id']} | Name: {campaign['name']}")
            return result.data
        else:
            print("No campaigns found in database.")
            return []
            
    except Exception as e:
        print(f"Error listing campaigns: {e}")
        return []

def create_survey_mapping(campaign_id):
    """Create mapping for survey- room pattern."""
    try:
        data = {
            "campaign_id": campaign_id,
            "room_pattern": "survey-",
            "is_active": True
        }
        
        result = supabase.table("campaign_room_mapping").insert(data).execute()
        
        if result.data:
            mapping_id = result.data[0]["id"]
            print(f"✓ Created mapping with ID: {mapping_id}")
            print(f"  Pattern: 'survey-' -> Campaign ID: {campaign_id}")
            return mapping_id
        else:
            print("Failed to create mapping")
            return None
            
    except Exception as e:
        print(f"Error creating mapping: {e}")
        return None

def main():
    print("=== Creating Survey Room Mapping ===")
    print("This will create a mapping for room names starting with 'survey-'")
    print()
    
    # List available campaigns
    campaigns = list_campaigns()
    
    if not campaigns:
        print("No campaigns available. Please create a campaign first.")
        return
    
    # Get campaign ID from user
    campaign_id = input("\nEnter the campaign ID to map to 'survey-' pattern: ").strip()
    
    if not campaign_id:
        print("Campaign ID is required.")
        return
    
    try:
        campaign_id = int(campaign_id)
    except ValueError:
        print("Campaign ID must be a number.")
        return
    
    # Verify campaign exists
    campaign_exists = any(c["id"] == campaign_id for c in campaigns)
    if not campaign_exists:
        print(f"Campaign ID {campaign_id} not found in available campaigns.")
        return
    
    # Create the mapping
    mapping_id = create_survey_mapping(campaign_id)
    
    if mapping_id:
        print(f"\n✅ Successfully created mapping!")
        print(f"   Room pattern: 'survey-'")
        print(f"   Campaign ID: {campaign_id}")
        print(f"   Mapping ID: {mapping_id}")
        print(f"\nNow any room starting with 'survey-' will use campaign {campaign_id}")

if __name__ == "__main__":
    main() 