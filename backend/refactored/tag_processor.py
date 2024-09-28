# youtube-web-app/backend/refactored/tag_processor.py

import spacy
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
from config import SENTENCE_TRANSFORMER_MODEL

nlp = spacy.load("en_core_web_sm")

class TagProcessor:
    @staticmethod
    def process_tags(tags, clustering_strength):
        normalized_tags = [TagProcessor.normalize_tag(tag) for tag in tags]
        names, non_names = TagProcessor.detect_names(normalized_tags)

        if non_names:
            model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
            non_name_embeddings = model.encode(non_names)

            clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=clustering_strength, affinity='cosine', linkage='average')
            labels = clustering.fit_predict(non_name_embeddings)

            cluster_to_tag = {}
            for tag, label in zip(non_names, labels):
                if label not in cluster_to_tag:
                    cluster_to_tag[label] = [tag]
                else:
                    cluster_to_tag[label].append(tag)

            consolidated_tags = set()
            tag_mapping = {name: name for name in names}

            for label, tags in cluster_to_tag.items():
                representative_tag = TagProcessor.find_representative_tag(tags, model)
                for tag in tags:
                    tag_mapping[tag] = representative_tag
                consolidated_tags.add(representative_tag)
            consolidated_tags.update(names)

            final_tags = [tag_mapping[tag] for tag in normalized_tags]
            final_tags = sorted(set(final_tags))
        else:
            final_tags = sorted(set(normalized_tags))

        return final_tags

    @staticmethod
    def detect_names(tags):
        names = []
        non_names = []
        for tag in tags:
            doc = nlp(tag)
            if any(ent.label_ == "PERSON" for ent in doc.ents):
                names.append(tag)
            else:
                non_names.append(tag)
        return names, non_names

    @staticmethod
    def normalize_tag(tag):
        import re
        tag = tag.strip().lower()
        tag = re.sub(r'[^a-z0-9\s]', '', tag)  # Remove special characters
        tag = re.sub(r'\s+', ' ', tag)  # Replace multiple spaces with single space
        return tag

    @staticmethod
    def find_representative_tag(cluster, model):
        if len(cluster) == 1:
            return cluster[0]
        
        embeddings = model.encode(cluster)
        similarity_matrix = cosine_similarity(embeddings)
        
        avg_similarity = similarity_matrix.mean(axis=1)
        most_representative_index = avg_similarity.argmax()
        return cluster[most_representative_index]