#!/usr/bin/env python3
"""
Setup script for campaign room mappings.
This script helps you create mappings between room name patterns and campaigns.
"""

from db_manager import (
    get_campaign_from_db, get_campaign_by_id, 
    create_campaign_room_mapping, get_questions_for_campaign
)

def list_all_campaigns():
    """List all available campaigns."""
    try:
        from db_manager import supabase
        result = supabase.table("campaign").select("*").order("id").execute()
        
        if result.data:
            print("\n=== Available Campaigns ===")
            for campaign in result.data:
                questions = get_questions_for_campaign(campaign["id"])
                print(f"ID: {campaign['id']}")
                print(f"Name: {campaign['name']}")
                print(f"Description: {campaign['description']}")
                print(f"Questions: {len(questions)}")
                print(f"Greeting: {campaign['greeting']}")
                print("-" * 50)
        else:
            print("No campaigns found in database.")
            
    except Exception as e:
        print(f"Error listing campaigns: {e}")

def setup_default_mappings():
    """Set up default campaign room mappings."""
    try:
        # Get the most recent campaign as default
        default_campaign = get_campaign_from_db()
        
        # Create a default mapping for the current room pattern
        # This assumes rooms are named like "call-<phone_number>"
        # You can modify this pattern based on your actual room naming convention
        default_pattern = "call-"
        
        print(f"Setting up default mapping:")
        print(f"Pattern: '{default_pattern}' -> Campaign: '{default_campaign['name']}' (ID: {default_campaign['id']})")
        
        mapping_id = create_campaign_room_mapping(
            campaign_id=default_campaign["id"],
            room_pattern=default_pattern,
            is_active=True
        )
        
        print(f"✓ Created mapping with ID: {mapping_id}")
        
    except Exception as e:
        print(f"Error setting up default mappings: {e}")

def create_custom_mapping():
    """Create a custom campaign room mapping."""
    try:
        # List available campaigns
        list_all_campaigns()
        
        # Get user input
        campaign_id = input("\nEnter campaign ID: ").strip()
        room_pattern = input("Enter room pattern (e.g., 'call-campaign1-'): ").strip()
        
        if not campaign_id or not room_pattern:
            print("Campaign ID and room pattern are required.")
            return
        
        # Verify campaign exists
        campaign = get_campaign_by_id(int(campaign_id))
        print(f"Creating mapping for campaign: '{campaign['name']}'")
        
        mapping_id = create_campaign_room_mapping(
            campaign_id=int(campaign_id),
            room_pattern=room_pattern,
            is_active=True
        )
        
        print(f"✓ Created mapping with ID: {mapping_id}")
        
    except Exception as e:
        print(f"Error creating custom mapping: {e}")

def main():
    """Main function to run the setup."""
    print("=== Campaign Room Mapping Setup ===")
    print("This script helps you set up mappings between room names and campaigns.")
    print()
    
    while True:
        print("\nOptions:")
        print("1. List all campaigns")
        print("2. Set up default mapping (for 'call-' pattern)")
        print("3. Create custom mapping")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            list_all_campaigns()
        elif choice == "2":
            setup_default_mappings()
        elif choice == "3":
            create_custom_mapping()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 