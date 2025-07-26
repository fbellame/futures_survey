from dotenv import load_dotenv
import logging
import os
from datetime import datetime
from livekit.protocol import egress
from livekit import api
from user_data import UserData

load_dotenv()
logger = logging.getLogger("futures_survey_assistant")
logger.setLevel(logging.INFO)

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
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        phone_suffix = userdata.customer_phone.replace('+', '').replace('-', '') if userdata.customer_phone else 'unknown'
        filepath = f"future_survey/{timestamp}_{phone_suffix}_{room_name}.mp4"
        
        # Configure S3 output (without filename - that goes in EncodedFileOutput)
        s3_output = egress.S3Upload(
            access_key=aws_access_key,
            secret=aws_secret_key,
            region=aws_region,
            bucket=s3_bucket
        )
        
        # Create encoded file output (filepath goes here)
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