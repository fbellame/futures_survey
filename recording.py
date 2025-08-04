from dotenv import load_dotenv
import logging
import os
import re
from datetime import datetime
from livekit.protocol import egress
from livekit import api
from user_data import UserData

load_dotenv()
logger = logging.getLogger("futures_survey_assistant")
logger.setLevel(logging.INFO)

def get_folder_from_room_prefix(room_name: str) -> str:
    """Extract prefix from room name for folder name"""
    # Extract prefix from room name (assuming format like "prefix_99999" where prefix can contain underscores)
    # Find the last underscore followed by digits
    match = re.search(r'_(\d+)$', room_name)
    
    if match:
        # Remove the last "_digits" part to get the prefix
        prefix = room_name[:match.start()]
        return prefix
    else:
        # If no pattern found, use the whole room name as fallback
        return room_name

async def start_s3_recording(room_name: str, userdata: UserData) -> bool:
    """Start recording using LiveKit Egress API with S3 storage"""
    lkapi = None
    try:
        # Get credentials from environment
        livekit_url = os.getenv("LIVEKIT_URL")
        livekit_api_key = os.getenv("LIVEKIT_API_KEY")
        livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")
        
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        s3_bucket = "s3-photo-ai-saas"
        
        if not all([livekit_url, livekit_api_key, livekit_api_secret, aws_access_key, aws_secret_key]):
            logger.error("Missing LiveKit or AWS credentials")
            return False
        
        # Create LiveKit API client
        lkapi = api.LiveKitAPI(
            url=livekit_url,
            api_key=livekit_api_key,
            api_secret=livekit_api_secret
        )
        
        # Generate folder name based on room prefix
        folder_name = get_folder_from_room_prefix(room_name)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Handle phone suffix - only include if it exists and is not empty/unknown
        filename_parts = [timestamp]
        if (userdata.customer_phone and 
            userdata.customer_phone.strip() and 
            userdata.customer_phone.lower() != 'unknown'):
            phone_suffix = userdata.customer_phone.replace('+', '').replace('-', '').replace(' ', '')
            if phone_suffix:  # Double-check it's not empty after cleaning
                filename_parts.append(phone_suffix)
        
        filename_parts.append(room_name)
        filename = '_'.join(filename_parts) + '.mp4'
        
        # Construct full filepath with folder
        filepath = f"{folder_name}/{filename}"
        
        # Configure S3 output
        s3_output = egress.S3Upload(
            access_key=aws_access_key,
            secret=aws_secret_key,
            region=aws_region,
            bucket=s3_bucket
        )
        
        # Create encoded file output
        file_output = egress.EncodedFileOutput(
            file_type=egress.EncodedFileType.MP4,
            filepath=filepath,
            s3=s3_output
        )
        
        # Create room composite request (audio only)
        request = egress.RoomCompositeEgressRequest(
            room_name=room_name,
            audio_only=True,
            file_outputs=[file_output]
        )
        
        # Start recording using the egress service
        response = await lkapi.egress.start_room_composite_egress(request)
        
        if response.egress_id:
            userdata.recording_id = response.egress_id
            logger.info(f"S3 Recording started successfully. Egress ID: {response.egress_id}")
            logger.info(f"Recording will be saved to: s3://{s3_bucket}/{filepath}")
            userdata.s3_recording_url = f"s3://{s3_bucket}/{filepath}"
            return True
        else:
            logger.error("Failed to start S3 recording - no egress ID returned")
            return False
            
    except Exception as e:
        logger.error(f"S3 recording error: {e}")
        return False
    finally:
        # Always close the API client to prevent connection leaks
        if lkapi:
            try:
                await lkapi.aclose()
                logger.debug("LiveKit API client closed successfully")
            except Exception as e:
                logger.warning(f"Error closing LiveKit API client: {e}")