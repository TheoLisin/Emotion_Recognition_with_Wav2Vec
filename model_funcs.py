import torch
import torch.nn.functional as F

from transformers import AutoConfig, Wav2Vec2Processor
from model_class import Wav2Vec2ForSpeechClassification, SpeechClassifierOutput


def load_model(model_path, pretrained_model_path=None):
    if pretrained_model_path is None:
        pretrained_model_path = model_path

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    config = AutoConfig.from_pretrained(model_path)
    processor = Wav2Vec2Processor.from_pretrained(
        "jonatasgrosman/wav2vec2-large-xlsr-53-english")
    sampling_rate = processor.feature_extractor.sampling_rate
    model = Wav2Vec2ForSpeechClassification.from_pretrained(
        model_path).to(device)

    return model, processor, config, sampling_rate, device


def predict(batches, model, processor, config, sampling_rate, device):
    features = processor(batches, sampling_rate=sampling_rate,
                         return_tensors="pt", padding=True)

    input_values = features.input_values.to(device)
    attention_mask = features.attention_mask.to(device)

    with torch.no_grad():
        logits = model(input_values, attention_mask=attention_mask).logits

    scores = F.softmax(logits, dim=1).detach().cpu().numpy()[0]
    outputs = [{"Emotion": config.id2label[i], "Score": f"{round(score * 100, 3):.1f}%"}
               for i, score in enumerate(scores)]
    return outputs
