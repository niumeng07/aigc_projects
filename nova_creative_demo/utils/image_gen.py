from typing import Dict, Any
import json
import logging
from pathlib import Path
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from boto3.session import Session
from PIL import Image
import io
import base64
import requests

logger = logging.getLogger(__name__)
# boto has a default timeout of 60 seconds which can be
# surpassed when generating multiple images.
config = Config(read_timeout=300)


def resize_and_pad_image(image_base64: str, target_width=1280, target_height=720, horizontal_placement=50, vertical_placement=50, resize_percent=50):
    """
    Resize and pad an image to fit the target dimensions, allowing custom horizontal and vertical placement percentages.
    The placement percentages use the center of the resized image as reference point.

    Args:
        image_base64 (str): base64 str of the input image.
        target_width (int): Target width of the output image.
        target_height (int): Target height of the output image.
        horizontal_placement (int): Horizontal placement percentage (0 to 100).
        vertical_placement (int): Vertical placement percentage (0 to 100).
        resize_percent (int): Percentage to resize the image.

    Returns:
        str: Base64-encoded string of the final image.
    """
    # Validate input percentages
    if not (0 <= horizontal_placement <= 100):
        raise ValueError("horizontal_placement must be between 0 and 100")
    if not (0 <= vertical_placement <= 100):
        raise ValueError("vertical_placement must be between 0 and 100")
    if not (0 <= resize_percent <= 100):
        raise ValueError("resize_percent must be between 0 and 100")

    # Read Image from base64 str
    img = Image.open(io.BytesIO(base64.b64decode(image_base64)))

    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Calculate aspect ratios
    target_aspect = target_width / target_height
    img_aspect = img.width / img.height

    if img_aspect > target_aspect:
        new_width = int(target_width * (resize_percent / 100))
        new_height = int(new_width / img_aspect)
    else:
        new_height = int(target_height * (resize_percent / 100))
        new_width = int(new_height * img_aspect)

    # Resize image
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Calculate padding based on placement percentages, using the center of the resized image as reference
    available_width = target_width - new_width
    available_height = target_height - new_height
    
    pad_left = int(available_width * (horizontal_placement / 100))
    pad_top = int(available_height * (vertical_placement / 100))

    # Create new white image with target size
    final_img = Image.new('RGB', (target_width, target_height), 'white')

    # Paste resized image onto white background
    final_img.paste(img_resized, (pad_left, pad_top))

    # Convert to base64
    buffered = io.BytesIO()
    final_img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def get_image_base64(presigned_url):
    try:
        # Download the image from the presigned URL
        response = requests.get(presigned_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Convert the image content to base64
        base64_image = base64.b64encode(response.content).decode('utf-8')
        return base64_image
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return None

class ImageGenerationError(Exception):
    """Custom exception for image generation errors.

    This exception is raised when any error occurs during the image generation process,
    including AWS service errors, file I/O errors, or unexpected runtime errors.

    Args:
        message (str): The error message
    """

    pass


class BedrockImageGenerator:
    """A class to handle image generation using AWS Bedrock service.

    This class provides functionality to generate images using AWS Bedrock's image generation
    models. It handles the AWS client initialization, API calls, and response processing.

    Attributes:
        DEFAULT_MODEL_ID (str): The default AWS Bedrock model ID for image generation.
        DEFAULT_REGION (str): The default AWS region for the Bedrock service.
        region_name (str): The AWS region being used.
        endpoint_url (Optional[str]): Custom endpoint URL for the AWS service, if any.
        output_directory (Path): Directory path where generated files will be saved.
        bedrock_client (boto3.client): The initialized AWS Bedrock client.
    """

    DEFAULT_MODEL_ID: str = "amazon.nova-canvas-v1:0"
    DEFAULT_REGION: str = "us-east-1"

    def __init__(
        self,
        region_name: str = DEFAULT_REGION,
        output_directory: str = "./output",
    ) -> None:
        """Initialize the BedrockImageGenerator.

        Args:
            region_name (str): AWS region name. Defaults to DEFAULT_REGION.
            endpoint_url (Optional[str]): Optional custom endpoint URL for the AWS service.
            output_directory (str): Directory path for saving output files. Defaults to "./output".

        Raises:
            ImageGenerationError: If the Bedrock client initialization fails.
        """
        self.region_name = region_name
        self.output_directory = Path(output_directory)
        self.bedrock_client = self._initialize_bedrock_client()

    def _initialize_bedrock_client(self) -> boto3.client:
        """Initialize and return the AWS Bedrock client.

        Returns:
            boto3.client: Initialized Bedrock client.

        Raises:
            ImageGenerationError: If client initialization fails due to AWS service errors.
        """
        try:
            session = Session()
            return session.client(
                service_name="bedrock-runtime",
                region_name=self.region_name,
                config=config
            )
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to initialize Bedrock client: {str(e)}")
            raise ImageGenerationError("Failed to initialize AWS Bedrock client") from e

    def _save_json_to_file(self, data: Dict[str, Any], filename: str) -> None:
        """Save JSON data to a file in the output directory.

        Args:
            data (Dict[str, Any]): Dictionary containing JSON-serializable data.
            filename (str): Name of the file to save the data to.

        Raises:
            ImageGenerationError: If saving the file fails.
        """
        try:
            filepath = self.output_directory / filename
            with filepath.open("w") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save {filename}: {str(e)}")
            raise ImageGenerationError(f"Failed to save {filename}") from e

    def _get_image_count(self, inference_params: Dict[str, Any]) -> int:
        """Extract the number of images to generate from the inference parameters.

        Args:
            inference_params (Dict[str, Any]): Dictionary containing image generation parameters.

        Returns:
            int: Number of images to generate, defaults to 1 if not specified.
        """
        return inference_params.get("imageGenerationConfig", {}).get(
            "numberOfImages", 1
        )

    def _log_generation_details(
        self, inference_params: Dict[str, Any], model_id: str
    ) -> None:
        """Log details about the image generation request for monitoring purposes.

        Args:
            inference_params (Dict[str, Any]): Dictionary containing image generation parameters.
            model_id (str): The ID of the model being used for generation.
        """
        image_count = self._get_image_count(inference_params)
        logger.info(
            f"Generating {image_count} image(s) with {model_id} in region {self.region_name}"
        )

        seed = inference_params.get("imageGenerationConfig", {}).get("seed")
        if seed is not None:
            logger.info(f"Using seed: {seed}")

    def generate_images(
        self,
        inference_params: Dict[str, Any],
        model_id: str = DEFAULT_MODEL_ID,
    ) -> Dict[str, Any]:
        """Generate images using AWS Bedrock's image generation models.

        This method handles the entire image generation process, including:
        - Creating the output directory if it doesn't exist
        - Logging generation details
        - Making the API call to AWS Bedrock
        - Saving request and response data
        - Error handling and logging

        Args:
            inference_params (Dict[str, Any]): Dictionary containing the parameters for image generation.
                Must include required fields as per AWS Bedrock's API specifications.
            model_id (str): The model ID to use for generation. Defaults to DEFAULT_MODEL_ID.

        Returns:
            Dict[str, Any]: Dictionary containing the complete response from the model, including
                generated images and any additional metadata.

        Raises:
            ImageGenerationError: If any error occurs during the generation process,
                including AWS service errors or file I/O errors.
        """
        try:
            # Create output directory if it doesn't exist
            self.output_directory.mkdir(parents=True, exist_ok=True)

            self._log_generation_details(inference_params, model_id)

            # Prepare and save request
            body_json = json.dumps(inference_params, indent=2)
            self._save_json_to_file(json.loads(body_json), "request.json")

            # Make the API call
            response = self.bedrock_client.invoke_model(
                body=body_json,
                modelId=model_id,
                accept="application/json",
                contentType="application/json",
            )

            # Save response metadata
            self._save_json_to_file(
                response.get("ResponseMetadata", {}), "response_metadata.json"
            )

            # Process and save response body
            response_body = json.loads(response.get("body").read())
            self._save_json_to_file(response_body, "response_body.json")

            # Log request ID for tracking
            request_id = response.get("ResponseMetadata", {}).get("RequestId")
            if request_id:
                logger.info(f"Request ID: {request_id}")

            # Check for API errors
            if error_msg := response_body.get("error"):
                if error_msg == "":
                    logger.warning(
                        "Response included empty string error (possible API bug)"
                    )
                else:
                    logger.warning(f"Error in response: {error_msg}")

            return response_body

        except (BotoCoreError, ClientError) as e:
            logger.error(f"AWS service error: {str(e)}")
            if hasattr(e, "response"):
                self._save_json_to_file(e.response, "error_response.json")
            raise ImageGenerationError(
                "Failed to generate images: AWS service error"
            ) from e

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise ImageGenerationError(
                "Unexpected error during image generation"
            ) from e