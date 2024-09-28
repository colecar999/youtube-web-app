# youtube-web-app/backend/refactored/tag_generator.py

import openai
from config import OPENAI_API_KEY, NUM_TAGS_DEFAULT

openai.api_key = OPENAI_API_KEY

class TagGenerator:
    @staticmethod
    def generate_tags(transcript_text, num_tags=NUM_TAGS_DEFAULT):
        prompt = f"Generate {num_tags} relevant tags for the following transcript. The tags are used to describe the content of the transcript. Provide the tags as a list separated by commas with no numbers. For example: 'tag1, tag2, tag3, tag4'. They should be in order of most relevant to least relevant:\n\n{transcript_text}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        tags = response['choices'][0]['message']['content'].strip().split(',')
        tags = [tag.strip() for tag in tags if tag.strip()]
        return tags

    @staticmethod
    def identify_interviewees(title, description):
        prompt = (
            f"Based on the following title and description, identify the names of the people being interviewed."
            f" Do not include the host. Do not include any information other than the interviewees."
            f" If there are multiple people, their names should be listed and separated by a comma. For example: 'John Doe, Jane Smith'\n\n"
            f"Title: {title}\nDescription: {description}"
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        interviewees = response['choices'][0]['message']['content'].strip().split(',')
        interviewees = [person.strip() for person in interviewees if person.strip()]
        return interviewees