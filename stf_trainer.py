import argparse

from datasets import load_dataset
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
from transformers.models.auto.modeling_auto import (
    MODEL_FOR_IMAGE_TEXT_TO_TEXT_MAPPING_NAMES,
)

from trl import (
    ModelConfig,
    ScriptArguments,
    SFTConfig,
    SFTTrainer,
    TrlParser,
    get_kbit_device_map,
    get_peft_config,
    get_quantization_config,
    setup_chat_format,
)


def main(script_args, training_args, model_args):
    ################
    # Model init kwargs & Tokenizer
    ################
    quantization_config = get_quantization_config(model_args)
    model_kwargs = dict(
        revision=model_args.model_revision,
        trust_remote_code=model_args.trust_remote_code,
        attn_implementation=model_args.attn_implementation,
        torch_dtype=model_args.torch_dtype,
        use_cache=False if training_args.gradient_checkpointing else True,
        device_map=get_kbit_device_map() if quantization_config is not None else None,
        quantization_config=quantization_config,
    )

    # Create model
    config = AutoConfig.from_pretrained(model_args.model_name_or_path)
    valid_image_text_architectures = MODEL_FOR_IMAGE_TEXT_TO_TEXT_MAPPING_NAMES.values()

    if config.architectures and any(
        arch in valid_image_text_architectures for arch in config.architectures
    ):
        from transformers import AutoModelForImageTextToText

        model_kwargs.pop("use_cache", None)  # Image models do not support cache
        model = AutoModelForImageTextToText.from_pretrained(
            model_args.model_name_or_path, **model_kwargs
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_args.model_name_or_path, **model_kwargs
        )

    # Create tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_args.model_name_or_path,
        trust_remote_code=model_args.trust_remote_code,
        use_fast=True,
    )

    # Set default chat template if needed
    if tokenizer.chat_template is None:
        model, tokenizer = setup_chat_format(model, tokenizer, format="chatml")

    ################
    # Dataset
    ################
    dataset = load_dataset(script_args.dataset_name, name=script_args.dataset_config)

    ################
    # Training
    ################
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset[script_args.dataset_train_split],
        eval_dataset=(
            dataset[script_args.dataset_test_split]
            if training_args.eval_strategy != "no"
            else None
        ),
        processing_class=tokenizer,
        peft_config=get_peft_config(model_args),
    )

    trainer.train()

    # Save and push to hub
    trainer.save_model(training_args.output_dir)
    if training_args.push_to_hub:
        trainer.push_to_hub(dataset_name=script_args.dataset_name)


def make_parser(subparsers: argparse._SubParsersAction = None):
    dataclass_types = (ScriptArguments, SFTConfig, ModelConfig)
    if subparsers is not None:
        parser = subparsers.add_parser(
            "sft", help="Run the SFT training script", dataclass_types=dataclass_types
        )
    else:
        parser = TrlParser(dataclass_types)
    return parser


if __name__ == "__main__":
    parser = make_parser()
    script_args, training_args, model_args = parser.parse_args_and_config()
    main(script_args, training_args, model_args)
