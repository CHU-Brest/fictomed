import pytest

from fictomed.core import generate


@pytest.mark.parametrize(
    "options",
    [
        {"prompt_workflow": "two_stage"},
        {"prompt_set": "old"},
        {"prompt_dir": "/tmp/prompts"},
    ],
)
def test_prompt_options_are_restricted_to_aphp(options):
    with pytest.raises(ValueError, match="réservées à la pipeline AP-HP"):
        generate("brest", **options)
