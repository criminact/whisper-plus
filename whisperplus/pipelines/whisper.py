import logging

import torch
from hqq.core.quantize import HQQBackend, HQQLinear
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

HQQLinear.set_backend(HQQBackend.PYTORCH)  # Pytorch backend
HQQLinear.set_backend(HQQBackend.PYTORCH_COMPILE)  # Compiled Pytorch via dynamo
HQQLinear.set_backend(HQQBackend.ATEN)  # C++ Aten/CUDA backend (set automatically by default if available)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class SpeechToTextPipeline:
    """Class for converting audio to text using a pre-trained speech recognition model."""

    def __init__(self, model_id: str = "distil-whisper/distil-large-v3", quant_config=None):
        self.model = None
        self.device = None

        if self.model is None:
            self.load_model(model_id)
        else:
            logging.info("Model already loaded.")

    def load_model(self, model_id: str = "distil-whisper/distil-large-v3", quant_config=None):
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id,
            quantization_config=quant_config,
            low_cpu_mem_usage=True,
            use_safetensors=True,
            attn_implementation="flash_attention_2",
            torch_dtype=torch.bfloat16,
            device_map='auto',
            max_memory={0: "24GiB"})
        logging.info("Model loaded successfully.")

        processor = AutoProcessor.from_pretrained(model_id)

        self.processor = processor
        self.model = model

    def __call__(
            self,
            audio_path: str = "test.mp3",
            chunk_length_s: int = 30,
            stride_length_s: int = 5,
            max_new_tokens: int = 128,
            batch_size: int = 100,
            language: str = "turkish",
            return_timestamps: bool = False):
        """
        Converts audio to text using the pre-trained speech recognition model.

        Args:
            audio_path (str): Path to the audio file to be transcribed.

        Returns:
            str: Transcribed text from the audio.
        """

        pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            chunk_length_s=chunk_length_s,
            stride_length_s=stride_length_s,
            max_new_tokens=max_new_tokens,
            batch_size=batch_size,
            return_timestamps=return_timestamps,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            model_kwargs={"use_flash_attention_2": True},
            generate_kwargs={"language": language},
        )
        logging.info("Transcribing audio...")
        result = pipe(audio_path)
        return result
