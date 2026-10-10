from spacy.matcher import PhraseMatcher

CONCEPT_VOCAB = {
    "Model": {
        "Transformer": ["Transformers"],
        "BERT": [],
        "RoBERTa": [],
        "GPT": [],
        "Vision Transformer": ["Vision Transformers", "ViT"],
        "ResNet": [],
        "LSTM": [],
        "CNN": ["CNNs", "Convolutional Neural Network", "Convolutional Neural Networks"],
        "GAN": ["GANs", "Generative Adversarial Network"],
        "Diffusion Model": ["Diffusion Models"],
        "Large Language Model": ["Large Language Models", "LLM", "LLMs"],
    },
    "Method": {
        "Self-Attention": ["Self Attention"],
        "Attention Mechanism": ["Attention Mechanisms"],
        "Pretraining": ["Pre-training"],
        "Fine-tuning": ["Finetuning", "Fine tuning"],
        "Data Augmentation": [],
        "Reinforcement Learning": [],
        "Transfer Learning": [],
        "Contrastive Learning": [],
        "Knowledge Distillation": [],
    },
    "Task": {
        "Machine Translation": [],
        "Language Modeling": ["Language Modelling"],
        "Image Classification": [],
        "Object Detection": [],
        "Semantic Segmentation": [],
        "Question Answering": [],
        "Sentiment Analysis": [],
        "Text Summarization": ["Text Summarisation"],
    },
    "Dataset": {
        "WMT2014": [],
        "GLUE": [],
        "ImageNet": [],
        "COCO": [],
        "SQuAD": [],
        "CIFAR-10": [],
    },
    "Metric": {
        "BLEU Score": ["BLEU"],
        "Accuracy": [],
        "F1 Score": ["F1"],
        "Perplexity": [],
    },
}


def build_matcher(nlp):
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    aliases = {}

    for concept_type, concepts in CONCEPT_VOCAB.items():
        patterns = []
        for canonical_name, alias_list in concepts.items():
            for surface in [canonical_name] + alias_list:
                patterns.append(nlp.make_doc(surface))
                aliases[surface.lower()] = canonical_name
        matcher.add(concept_type, patterns)

    return matcher, aliases