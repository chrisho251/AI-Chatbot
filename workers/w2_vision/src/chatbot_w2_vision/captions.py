"""Captions and alt text for figures. Stub owned by Lane B.

Purpose
Describe charts, diagrams and photos in textbooks so they become searchable and citable.
This runs in batch only, never on the answer path.

Input
A figure Region, its image bytes and a ChatClient pointed at the vision language model.

Output
An ExtractedRegion whose content is one short caption followed by alt text in markdown.

What to build
Send the image as a base64 data url in an OpenAI style message with a short fixed prompt.
The vision model and its revision come from settings, see the default models in TECH_STACK.md.
Keep the prompt in this module with a version string and record it in Extractor.version.

How to test
Fake the ChatClient with an httpx MockTransport and assert the request carries the image.
"""

from chatbot_common.llm import ChatClient
from chatbot_contracts.corpus import ExtractedRegion, Region


async def caption_figure(region: Region, image: bytes, llm: ChatClient) -> ExtractedRegion:
    raise NotImplementedError("figure captions are not written yet")
