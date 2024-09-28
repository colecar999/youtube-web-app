# backend/models/video.py

from datetime import datetime

class Video:
    def __init__(self, video_id, title, description, duration, view_count, like_count, comment_count):
        self.video_id = video_id
        self.title = title
        self.description = description
        self.duration = duration
        self.view_count = view_count
        self.like_count = like_count
        self.comment_count = comment_count
        self.retrieval_date = datetime.utcnow().isoformat()
        self.tags = []

    def to_dict(self):
        return {
            'video_id': self.video_id,
            'title': self.title,
            'description': self.description,
            'duration': self.duration,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'retrieval_date': self.retrieval_date,
            'tags': ', '.join(self.tags)
        }

    def add_tags(self, tags):
        self.tags.extend(tags)
        self.tags = list(set(self.tags))  # Remove duplicates